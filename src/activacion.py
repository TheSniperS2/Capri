"""Detección local de Capri. No conserva grabaciones ni envía audio a internet."""
import array
from collections import deque
import json
import queue
import re
import unicodedata
from reconocimiento import amplificar_bajo,DetectorVoz

def quitar_nombre(texto,*,candidato=False):
    resto=texto;encontrado=False
    while resto:
        normal=''.join(c for c in unicodedata.normalize('NFD',resto.lower()) if unicodedata.category(c)!='Mn')
        # Capriles es una confusión reproducida de Vosk, nunca una autorización.
        # Solo se considera candidato si Whisper puede verificar el nombre real.
        nombre=r'(?:capri|capriles)' if candidato else 'capri'
        coincidencia=re.match(r'^\s*[¿¡]*\s*(?:(?:oye|hey|ey|hola|ok|okay)\s*[,.:!]?\s*)?'+nombre+r'\b[\s,.:!?¿¡-]*',normal)
        if not coincidencia:break
        encontrado=True;resto=resto[coincidencia.end():].strip()
    return resto if encontrado else None

def esperar(micro,detener,detectada,dispositivo=None,motor='mixto',terminar=None,nivel=None,estado=None,lista=None):
    micro.confianza_baja=False
    import sounddevice as sd
    from vosk import Model,KaldiRecognizer,SetLogLevel
    from voz import resolver_microfono,_abrir_entrada
    from reconocimiento import disponible,transcribir
    from prueba_microfono import filtrar
    verificar_whisper=motor in ('mixto','preciso') and disponible(micro.carpeta,getattr(micro,'modelo_whisper','base'))
    SetLogLevel(-1)
    if estado:estado('Preparando activación…')
    indice=resolver_microfono(dispositivo)
    datos=sd.query_devices(indice,kind='input') if indice is not None else sd.query_devices(kind='input')
    bloques=queue.Queue(maxsize=512)
    def recibir(datos,frames,reloj,error):
        try:bloques.put_nowait(bytes(datos))
        except queue.Full:pass
    micro.diagnostico={'seleccion':dispositivo,'motor':'activacion-local','intentos':[]}
    activada=False;nombre_confirmado=False;inicio_orden=None;ultima_voz=0;texto_final='';pcm=deque();cantidad=0
    reloj_audio=0;segmentos=[];parcial='';hay_orden=False;voz_despues=0;voz_en_espera=False
    with _abrir_entrada(indice,datos,recibir,detener,micro.diagnostico['intentos']) as tasa:
        # Abrir la entrada antes de cargar modelos: la primera frase queda en
        # cola durante el arranque, en lugar de perderse con el micro cerrado.
        if micro.modelo is None:micro.modelo=Model(str(micro.carpeta/'vosk-model-small-es-0.42'))
        if detener.is_set():return None
        reconocedor=KaldiRecognizer(micro.modelo,tasa)
        actividad=DetectorVoz();actividad.analizar(bytes(6400),16000)
        if detener.is_set():return None
        if lista:lista()
        while not detener.is_set():
            if activada and terminar and terminar.is_set():
                parcial=json.loads(reconocedor.FinalResult()).get('text','')
                texto_final=' '.join(segmentos+[parcial]).strip()
                if parcial and quitar_nombre(texto_final) is not None:nombre_confirmado=True
                break
            try:bloque=bloques.get(timeout=.1)
            except queue.Empty:continue
            pcm.append(bloque);cantidad+=len(bloque)
            # El buffer circular es solo para esperar el nombre. Una vez activada,
            # conservar todo el principio de la orden hasta terminar de capturar.
            while not activada and cantidad>int(tasa*2*20) and len(pcm)>1:cantidad-=len(pcm.popleft())
            muestras=array.array('h',bloque)
            rms=(sum(v*v for v in muestras)/max(1,len(muestras)))**.5/32768
            reloj_audio+=len(bloque)/(tasa*2)
            filtrado=filtrar(bloque,getattr(micro,'umbral_microfono_db',None))
            habla=actividad.analizar(filtrado,tasa)
            if habla and not activada and not voz_en_espera:
                # Comenzar una frase nueva sin arrastrar conversación anterior
                # hacia Whisper. El margen conserva el inicio que precede al VAD.
                margen=int(tasa*2*.5)+len(bloque)
                while cantidad>margen and len(pcm)>1:cantidad-=len(pcm.popleft())
                voz_en_espera=True
            if habla:ultima_voz=reloj_audio
            audio_reconocedor=amplificar_bajo(filtrado)
            final=reconocedor.AcceptWaveform(audio_reconocedor)
            resultado=json.loads(reconocedor.Result() if final else reconocedor.PartialResult())
            if not activada and voz_en_espera and reloj_audio-ultima_voz>=.55:
                # No esperar varios segundos al endpoint interno de Vosk para
                # finalizar un nombre aislado o permitir un nuevo intento.
                if not final:resultado=json.loads(reconocedor.FinalResult());final=True
                voz_en_espera=False
            texto=resultado.get('text' if final else 'partial','').strip()
            resto=quitar_nombre(texto,candidato=verificar_whisper)
            # Mostrar la escucha en cuanto el reconocedor LIBRE oye el nombre,
            # sin esperar la pausa de fin de frase. Esto solo abre la captura:
            # Whisper verifica el nombre real antes de enviar la orden. Sin
            # Whisper solo se admite el nombre exacto confirmado por Vosk final.
            nombre_detectado=resto is not None
            if final and quitar_nombre(texto) is not None:nombre_confirmado=True
            if nombre_detectado and not activada:
                activada=True;inicio_orden=reloj_audio;detectada()
            if activada:
                if nivel:nivel(min(1,rms*10))
                if habla and reloj_audio>inicio_orden+.12:voz_despues+=len(bloque)/(tasa*2)
                if final:
                    if texto:segmentos.append(texto)
                    parcial=''
                else:parcial=texto
                texto_final=' '.join(segmentos+[parcial]).strip()
                resto_completo=quitar_nombre(texto_final,candidato=verificar_whisper)
                if resto_completo or (resto_completo is None and texto_final) or voz_despues>=.2:hay_orden=True
                silencio=reloj_audio-(ultima_voz if hay_orden else max(ultima_voz,inicio_orden))
                # Un «final» de Vosk puede ser solo «Capri». No cerrar el stream
                # ni cargar Whisper entre el nombre y la orden: seguir en el mismo.
                if reloj_audio-inicio_orden>=24 or silencio>=(.85 if hay_orden else 6):
                    cola=json.loads(reconocedor.FinalResult()).get('text','').strip()
                    texto_final=' '.join(segmentos+[cola or parcial]).strip()
                    if cola and quitar_nombre(' '.join(segmentos+[cola])) is not None:nombre_confirmado=True
                    break
            elif final:
                # Conservar un pequeño margen si el nombre tarda en detectarse.
                # Un final prematuro del transcriptor libre no descarta el audio
                # inmediatamente anterior a la activación.
                while cantidad>int(tasa*2*1.5) and len(pcm)>1:cantidad-=len(pcm.popleft())
    if nivel:nivel(0)
    if detener.is_set() or not activada:return None
    if verificar_whisper:
        if estado:estado('Reconociendo la frase…')
        texto=transcribir(micro,b''.join(pcm),tasa,'es')
        # El ASR de dictado verifica el nombre en el audio original. Un final
        # incorrecto de Vosk no veta una confirmación independiente de Whisper.
        # Si Whisper no oye Capri al principio, no se envía ninguna frase.
        return quitar_nombre(texto)
    if not nombre_confirmado:return None
    resto_vosk=quitar_nombre(texto_final)
    if resto_vosk is None:return None
    return resto_vosk
