"""Reconocimiento multilingüe con Whisper. Audio solo en memoria, sin archivos WAV."""
import array
import importlib.util
import queue
import time
from nombres import VOCABULARIO

ARCHIVOS=('config.json','model.bin','tokenizer.json','vocabulary.txt')
ORDENES='Reproduce la canción. Siguiente canción. Canción anterior. Pausa la música. Pon mi playlist.'

def modelos_disponibles(carpeta):
    return [m for m in ('base','small') if all((carpeta/('whisper-'+m)/n).is_file() for n in ARCHIVOS)]

def elegir_modelo(carpeta,preferido='base'):
    if preferido not in ('base','small'):preferido='base'
    instalados=modelos_disponibles(carpeta)
    return preferido if preferido in instalados else ('base' if 'base' in instalados else (instalados[0] if instalados else preferido))

def disponible(carpeta,modelo='base'):
    return elegir_modelo(carpeta,modelo) in modelos_disponibles(carpeta) and importlib.util.find_spec('faster_whisper') is not None

def energia(datos):
    muestras=array.array('h',datos)
    return (sum(x*x for x in muestras)/max(1,len(muestras)))**.5/32768

def umbral_voz(ruido):
    """Admitir voz suave sin tratar todo el ruido de fondo como habla."""
    return max(.0015,ruido*1.8)

class DetectorVoz:
    """Distingue habla de ruido continuo. Usa el VAD local ya incluido con Whisper."""
    def __init__(self):
        self.audio=None;self.pendiente=0;self.habla=False;self.ruido=.001
        try:
            import numpy as np
            from faster_whisper.vad import get_speech_timestamps,VadOptions
            self.np=np;self.funcion=get_speech_timestamps
            self.opciones=VadOptions(threshold=.35,min_speech_duration_ms=80,
                                    min_silence_duration_ms=100,speech_pad_ms=0)
        except (ImportError,RuntimeError,OSError):self.funcion=None

    def analizar(self,pcm,tasa):
        if self.funcion is None:
            rms=energia(pcm)
            habla=rms>umbral_voz(self.ruido)
            if not habla:self.ruido=.95*self.ruido+.05*min(rms,.004)
            return habla
        np=self.np
        a=np.frombuffer(amplificar_bajo(pcm),dtype='<i2').astype(np.float32)/32768
        if tasa!=16000 and len(a):
            a=np.interp(np.arange(max(1,round(len(a)*16000/tasa)))*tasa/16000,
                         np.arange(len(a)),a).astype(np.float32)
        self.audio=a if self.audio is None else np.concatenate((self.audio,a))[-16000:]
        self.pendiente+=len(a)
        if self.pendiente<1600:return self.habla
        self.pendiente=0
        try:
            segmentos=self.funcion(self.audio,self.opciones)
            self.habla=any(s['end']>=len(self.audio)-1600 for s in segmentos)
        except (ImportError,RuntimeError,ValueError,OSError):
            self.funcion=None
            return self.analizar(pcm,tasa)
        return self.habla

def amplificar_bajo(datos):
    """Ganancia limitada para Vosk; no modifica la captura ni amplifica silencio."""
    rms=energia(datos)
    if rms<.0006 or rms>=.025:return datos
    muestras=array.array('h',datos)
    pico=max((abs(v) for v in muestras),default=0)
    ganancia=min(3.0,.025/rms,30000/max(1,pico))
    if ganancia<=1:return datos
    return array.array('h',(round(v*ganancia) for v in muestras)).tobytes()

def preparar_pcm(datos,tasa):
    """Whisper recibe muestras a 16 kHz; evita el decodificador WAV incompatible."""
    import av
    import numpy as np
    if len(datos)%2:
        raise ValueError('La captura de audio quedó incompleta.')
    muestras=np.frombuffer(datos,dtype='<i2')
    if not len(muestras):return np.empty(0,dtype=np.float32)
    if tasa==16000:return muestras.astype(np.float32)/32768.0
    frame=av.AudioFrame.from_ndarray(muestras.reshape(1,-1),format='s16',layout='mono')
    frame.sample_rate=int(tasa)
    remuestreador=av.AudioResampler(format='fltp',layout='mono',rate=16000)
    frames=remuestreador.resample(frame)+remuestreador.resample(None)
    if not frames:return np.empty(0,dtype=np.float32)
    return np.concatenate([f.to_ndarray().reshape(-1) for f in frames]).astype(np.float32,copy=False)

def escuchar_preciso(micro,detener,nivel,estado,limite,dispositivo,idioma='es'):
    import sounddevice as sd
    from voz import resolver_microfono,_abrir_entrada
    from prueba_microfono import filtrar,umbral_db
    indice=resolver_microfono(dispositivo)
    datos=sd.query_devices(indice,kind='input') if indice is not None else sd.query_devices(kind='input')
    modelo=elegir_modelo(micro.carpeta,getattr(micro,'modelo_whisper','base'))
    micro.diagnostico={'seleccion':dispositivo,'motor':'whisper-'+modelo,'intentos':[]}
    audio=queue.Queue(maxsize=160)
    def recibir(datos,frames,reloj,error):
        try:audio.put_nowait(bytes(datos))
        except queue.Full:pass
    fragmentos=[];hubo_voz=False;duracion_voz=0;ultima_voz=None;ruido=.001
    estado('Te escucho…')
    with _abrir_entrada(indice,datos,recibir,detener,micro.diagnostico['intentos']) as tasa:
        inicio=time.monotonic()
        while not detener.is_set() and time.monotonic()-inicio<limite:
            try:bloque=audio.get(timeout=.15)
            except queue.Empty:continue
            rms=energia(bloque);nivel(min(1,rms*10))
            umbral=umbral_db(getattr(micro,'umbral_microfono_db',None))
            fragmentos.append(filtrar(bloque,umbral))
            ahora=time.monotonic()
            if rms>(umbral_voz(ruido) if umbral is None else 10**(umbral/20)):
                duracion_voz+=len(bloque)/(tasa*2)
                hubo_voz=duracion_voz>=.12
                ultima_voz=ahora
            elif not hubo_voz:
                ruido=.95*ruido+.05*min(rms,.004)
            if hubo_voz and ultima_voz and ahora-ultima_voz>.85:break
            if not hubo_voz and ahora-inicio>6:break
    nivel(0)
    if not hubo_voz or not fragmentos:return ''
    estado('Reconociendo la frase…')
    return transcribir(micro,b''.join(fragmentos),tasa,idioma)

def transcribir(micro,pcm,tasa,idioma='es'):
    """Compartido por el botón de dictado y la frase que sigue a la activación."""
    modelo=elegir_modelo(micro.carpeta,getattr(micro,'modelo_whisper','base'))
    if micro.whisper is None or getattr(micro,'whisper_cargado',modelo)!=modelo:
        from faster_whisper import WhisperModel
        micro.whisper=None
        micro.whisper=WhisperModel(str(micro.carpeta/('whisper-'+modelo)),device='cpu',compute_type='int8',cpu_threads=4)
        micro.whisper_cargado=modelo
    muestras=preparar_pcm(amplificar_bajo(pcm),tasa)
    segmentos,_=micro.whisper.transcribe(muestras,language=idioma or 'es',task='transcribe',hotwords=VOCABULARIO+', reproduce, siguiente canción, playlist',beam_size=5,best_of=1,temperature=0,
                    vad_filter=True,vad_parameters={'min_silence_duration_ms':450},condition_on_previous_text=False,
                    initial_prompt='Conversación en español. '+ORDENES+' Conservar nombres de aplicaciones y canciones en inglés sin traducirlos: '+VOCABULARIO+'.')
    segmentos=list(segmentos)
    if not segmentos:return ''
    micro.confianza_baja=all(getattr(s,'avg_logprob',0)<-.9 or getattr(s,'no_speech_prob',0)>.6 for s in segmentos)
    return ' '.join(s.text.strip() for s in segmentos if s.text.strip()).strip()
