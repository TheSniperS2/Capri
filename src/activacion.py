"""Detección local de Capri. No conserva grabaciones ni envía audio a internet."""
import array
from collections import deque
import json
import queue
import re
import unicodedata

def quitar_nombre(texto):
    normal=''.join(c for c in unicodedata.normalize('NFD',texto.lower()) if unicodedata.category(c)!='Mn')
    coincidencia=re.match(r'^\s*(?:(?:oye|hey|ey|hola|ok|okay)\s*[,.:!]?\s*)?capri\b[\s,.:!?¿¡-]*',normal)
    return texto[coincidencia.end():].strip() if coincidencia else None

def esperar(micro,detener,detectada,dispositivo=None,motor='mixto',terminar=None):
    micro.confianza_baja=False
    import sounddevice as sd
    from vosk import Model,KaldiRecognizer,SetLogLevel
    from voz import resolver_microfono,_abrir_entrada
    SetLogLevel(-1)
    if micro.modelo is None:micro.modelo=Model(str(micro.carpeta/'vosk-model-small-es-0.42'))
    indice=resolver_microfono(dispositivo)
    datos=sd.query_devices(indice,kind='input') if indice is not None else sd.query_devices(kind='input')
    bloques=queue.Queue(maxsize=160)
    def recibir(datos,frames,reloj,error):
        try:bloques.put_nowait(bytes(datos))
        except queue.Full:pass
    micro.diagnostico={'seleccion':dispositivo,'motor':'activacion-local','intentos':[]}
    activada=False;inicio_orden=None;ultima_voz=0;texto_final='';pcm=deque();cantidad=0
    reloj_audio=0;segmentos=[];parcial='';hay_orden=False;ruido=.001
    with _abrir_entrada(indice,datos,recibir,detener,micro.diagnostico['intentos']) as tasa:
        reconocedor=KaldiRecognizer(micro.modelo,tasa)
        while not detener.is_set():
            if activada and terminar and terminar.is_set():
                parcial=json.loads(reconocedor.FinalResult()).get('text','')
                texto_final=' '.join(segmentos+[parcial]).strip();break
            try:bloque=bloques.get(timeout=.1)
            except queue.Empty:continue
            pcm.append(bloque);cantidad+=len(bloque)
            # El buffer circular es solo para esperar el nombre. Una vez activada,
            # conservar todo el principio de la orden hasta terminar de capturar.
            while not activada and cantidad>int(tasa*2*20) and len(pcm)>1:cantidad-=len(pcm.popleft())
            muestras=array.array('h',bloque)
            rms=(sum(v*v for v in muestras)/max(1,len(muestras)))**.5/32768
            reloj_audio+=len(bloque)/(tasa*2)
            if rms>max(.0025,ruido*2.5):ultima_voz=reloj_audio
            elif not activada:ruido=.95*ruido+.05*min(rms,.004)
            final=reconocedor.AcceptWaveform(bloque)
            resultado=json.loads(reconocedor.Result() if final else reconocedor.PartialResult())
            texto=resultado.get('text' if final else 'partial','').strip()
            resto=quitar_nombre(texto)
            if resto is not None and not activada:
                activada=True;inicio_orden=reloj_audio;detectada()
            if activada:
                if final:
                    if texto:segmentos.append(texto)
                    parcial=''
                else:parcial=texto
                texto_final=' '.join(segmentos+[parcial]).strip()
                resto_completo=quitar_nombre(texto_final)
                if resto_completo:hay_orden=True
                silencio=reloj_audio-max(ultima_voz,inicio_orden)
                # Un «final» de Vosk puede ser solo «Capri». No cerrar el stream
                # ni cargar Whisper entre el nombre y la orden: seguir en el mismo.
                if reloj_audio-inicio_orden>=24 or silencio>=(1.15 if hay_orden else 6):
                    cola=json.loads(reconocedor.FinalResult()).get('text','').strip()
                    texto_final=' '.join(segmentos+[cola or parcial]).strip();break
            elif final:
                # No llevar conversaciones anteriores a la transcripción de la orden.
                pcm.clear();cantidad=0
    if detener.is_set() or not activada:return None
    if motor in ('mixto','preciso'):
        from reconocimiento import disponible,transcribir
        if disponible(micro.carpeta):
            texto=transcribir(micro,b''.join(pcm),tasa,None if motor=='mixto' else 'es')
            resto=quitar_nombre(texto)
            # La activación ya fue detectada por Vosk; si Whisper omite el nombre,
            # aceptar solo la transcripción del mismo fragmento de audio.
            if texto.strip():return resto if resto is not None else texto.strip()
    return quitar_nombre(texto_final) or ''
