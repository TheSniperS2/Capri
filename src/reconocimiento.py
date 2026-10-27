"""Reconocimiento multilingüe con Whisper. Audio solo en memoria, sin archivos WAV."""
import array
import importlib.util
import queue
import time
from nombres import VOCABULARIO

ARCHIVOS=('config.json','model.bin','tokenizer.json','vocabulary.txt')

def disponible(carpeta):
    return all((carpeta/'whisper-base'/n).is_file() for n in ARCHIVOS) and importlib.util.find_spec('faster_whisper') is not None

def energia(datos):
    muestras=array.array('h',datos)
    return (sum(x*x for x in muestras)/max(1,len(muestras)))**.5/32768

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
    indice=resolver_microfono(dispositivo)
    datos=sd.query_devices(indice,kind='input') if indice is not None else sd.query_devices(kind='input')
    micro.diagnostico={'seleccion':dispositivo,'motor':'whisper-base','intentos':[]}
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
            fragmentos.append(bloque)
            rms=energia(bloque);nivel(min(1,rms*10))
            ahora=time.monotonic()
            if rms>max(.0025,ruido*2.5):
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

def transcribir(micro,pcm,tasa,idioma=None):
    """Compartido por el botón de dictado y la frase que sigue a la activación."""
    if micro.whisper is None:
        from faster_whisper import WhisperModel
        micro.whisper=WhisperModel(str(micro.carpeta/'whisper-base'),device='cpu',compute_type='int8',cpu_threads=4)
    muestras=preparar_pcm(pcm,tasa)
    segmentos,_=micro.whisper.transcribe(muestras,language=idioma,task='transcribe',hotwords=VOCABULARIO,beam_size=3,best_of=1,temperature=0,
                    vad_filter=True,vad_parameters={'min_silence_duration_ms':450},condition_on_previous_text=False,
                    initial_prompt='Conversación en español e inglés. Conservar los nombres de aplicaciones sin traducirlos: '+VOCABULARIO+'.')
    segmentos=list(segmentos)
    if not segmentos:return ''
    micro.confianza_baja=all(getattr(s,'avg_logprob',0)<-.9 or getattr(s,'no_speech_prob',0)>.6 for s in segmentos)
    return ' '.join(s.text.strip() for s in segmentos if s.text.strip()).strip()
