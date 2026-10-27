"""Micro local con Vosk. Voz hablada mediante Windows o Microsoft Edge TTS."""
from pathlib import Path
import asyncio
import base64
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from concurrent.futures import Future
from contextlib import contextmanager, ExitStack
from functools import wraps
import re
import unicodedata
import atexit
import math

HIDDEN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def normalizar_velocidad(valor=1.0):
    try:valor=float(valor)
    except (TypeError,ValueError):return 1.0
    if not math.isfinite(valor):return 1.0
    return min(1.8,max(.8,valor))

def parametros_velocidad(valor=1.0):
    velocidad=normalizar_velocidad(valor)
    return f'{round((velocidad-1)*100):+d}%',round((velocidad-1)*8)

def normalizar_volumen(valor=100):
    try:valor=float(valor)
    except (TypeError,ValueError):return 100
    return round(min(100,max(0,valor))) if math.isfinite(valor) else 100

def texto_para_voz(texto):
    """Mantiene la frase unida y evita pausas de formato o comas excesivas."""
    texto=re.sub(r'(?m)^\s*(?:#{1,6}|[-*•])\s+','',texto)
    texto=texto.replace('**','').replace('`','')
    texto=re.sub(r'\.{2,}|…','.',texto)
    # Conservar decimales y horas (3,5 o 12:30).
    texto=re.sub(r'(?<!\d)[,;:]|[,;:](?!\d)',' ',texto)
    return re.sub(r'\s+',' ',texto).strip()

_audio_trabajos = queue.Queue()
_audio_lock = threading.Lock()
_audio_hilo = None

@contextmanager
def _com_audio():
    """Cada hilo que utiliza las interfaces de audio de Windows inicializa COM."""
    ole = None
    inicializado = False
    if os.name == 'nt':
        import ctypes
        # WinDLL evita que ctypes convierta automáticamente un HRESULT en excepción.
        ole = ctypes.WinDLL('ole32')
        ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        ole.CoInitializeEx.restype = ctypes.c_long
        resultado = ole.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED
        inicializado = resultado in (0, 1)
        if resultado < 0 and resultado != -2147417850:  # RPC_E_CHANGED_MODE: COM ya existe
            raise RuntimeError('Windows no pudo inicializar el audio en este hilo.')
    try:
        yield
    finally:
        if inicializado:
            ole.CoUninitialize()

def _bucle_audio():
    # Enumeración, apertura y cierre comparten el mismo hilo durante toda la sesión.
    try:
        with _com_audio():
            while True:
                trabajo = _audio_trabajos.get()
                if trabajo is None:return
                funcion, args, kwargs, futuro = trabajo
                try:futuro.set_result(funcion(*args, **kwargs))
                except BaseException as e:futuro.set_exception(e)
                finally:
                    # No retener la última prueba de audio en el Future del
                    # trabajador cuando queda esperando el siguiente encargo.
                    del trabajo,funcion,args,kwargs,futuro
    except BaseException as error:
        while True:
            trabajo = _audio_trabajos.get()
            if trabajo is None:return
            trabajo[3].set_exception(RuntimeError('No se pudo inicializar el audio de Windows: '+str(error)))

def _cerrar_hilo_audio():
    if _audio_hilo and _audio_hilo.is_alive():
        _audio_trabajos.put(None)
        _audio_hilo.join(timeout=1)

atexit.register(_cerrar_hilo_audio)

def _en_hilo_audio(funcion):
    @wraps(funcion)
    def ejecutar(*args, **kwargs):
        global _audio_hilo
        if threading.current_thread() is _audio_hilo:
            return funcion(*args, **kwargs)
        with _audio_lock:
            if _audio_hilo is None or not _audio_hilo.is_alive():
                _audio_hilo = threading.Thread(target=_bucle_audio, name='CapriAudio', daemon=True)
                _audio_hilo.start()
        futuro = Future()
        _audio_trabajos.put((funcion, args, kwargs, futuro))
        return futuro.result()
    return ejecutar

@_en_hilo_audio
def listar_microfonos(todas_las_interfaces=False):
    """Una sola interfaz para la lista; catálogo completo al resolver ajustes antiguos."""
    import sounddevice as sd
    apis = sd.query_hostapis()
    resultado = []
    for indice, datos in enumerate(sd.query_devices()):
        if datos.get('max_input_channels', 0) > 0:
            resultado.append({'indice': indice, 'nombre': datos['name'], 'api': apis[datos['hostapi']]['name']})
    prioridad = {'Windows WASAPI': 0, 'MME': 1, 'Windows DirectSound': 2}
    resultado = sorted(resultado, key=lambda m: (prioridad.get(m['api'], 3), m['nombre'].casefold(), m['indice']))
    if todas_las_interfaces or not resultado:
        return resultado
    # PortAudio repite los mismos endpoints a través de varias interfaces de Windows.
    # WASAPI enumera los endpoints actuales sin los alias de entrada predeterminada.
    interfaz = resultado[0]['api']
    alias = ('microsoft sound mapper', 'asignador de sonido de microsoft',
             'primary sound capture driver', 'controlador primario de captura de sonido')
    return [m for m in resultado if m['api'] == interfaz and not m['nombre'].casefold().startswith(alias)]

def resolver_microfono(seleccion):
    if seleccion is None:
        return None
    if not isinstance(seleccion, dict) or not isinstance(seleccion.get('nombre'), str) or not isinstance(seleccion.get('api'), str):
        raise RuntimeError('Selecciona de nuevo tu micrófono en Ajustes.')
    coincidencias = [m for m in listar_microfonos(todas_las_interfaces=True) if m['nombre'] == seleccion['nombre'] and m['api'] == seleccion['api']]
    for micro in coincidencias:
        if micro['indice'] == seleccion.get('indice'):
            return micro['indice']
    if len(coincidencias) == 1:
        return coincidencias[0]['indice']
    if not coincidencias:
        raise RuntimeError('El micrófono elegido no está disponible. Conéctalo o selecciona otro en Ajustes.')
    raise RuntimeError('Hay varios micrófonos con ese nombre. Selecciona el que quieres usar en Ajustes.')

def _identidad_microfono(nombre):
    nombre = ''.join(c for c in unicodedata.normalize('NFD', nombre.casefold()) if unicodedata.category(c) != 'Mn')
    nombre = ' '.join(nombre.split())
    completo = re.fullmatch(r'(?:microfono|microphone)\s*\((.+)\)', nombre)
    return completo[1] if completo else nombre

@contextmanager
def _abrir_entrada(indice, datos, recibir, detener, intentos):
    import sounddevice as sd
    api = sd.query_hostapis(datos['hostapi'])['name'] if 'hostapi' in datos else ''
    primero = {'indice': indice, 'nombre': datos.get('name', ''), 'api': api}
    candidatos = [primero]
    pila = None
    posicion = 0
    while posicion < len(candidatos):
        if detener.is_set():
            raise InterruptedError('Captura cancelada.')
        candidato = candidatos[posicion]
        posicion += 1
        flujo = None
        if candidato['api'] != 'Windows WDM-KS':
            try:
                info = datos if candidato is primero else sd.query_devices(candidato['indice'], kind='input')
                tasa = int(info['default_samplerate'])
                opciones = dict(device=candidato['indice'], samplerate=tasa, blocksize=0,
                                latency='high', dtype='int16', channels=1, callback=recibir)
                if candidato['api'] == 'Windows WASAPI':
                    opciones['extra_settings'] = sd.WasapiSettings(exclusive=False, auto_convert=True)
                flujo = sd.RawInputStream(**opciones)
                prueba = ExitStack()
                try:
                    prueba.enter_context(flujo)
                except BaseException:
                    prueba.close()
                    raise
                pila = prueba
                intentos.append(dict(candidato, frecuencia=tasa, resultado='abierto'))
                break
            except Exception as e:
                if flujo:
                    try: flujo.close()
                    except Exception: pass
                intentos.append(dict(candidato, resultado='error', detalle=str(e)))
        else:
            intentos.append(dict(candidato, resultado='interfaz omitida'))
        if candidato is primero and primero['nombre']:
            # Nunca probar otra fuente de audio. Las variantes deben corresponder
            # al mismo nombre de hardware; si son ambiguas no se eligen solas.
            identidad = _identidad_microfono(primero['nombre'])
            relacionados = [m for m in listar_microfonos(todas_las_interfaces=True)
                            if _identidad_microfono(m['nombre']) == identidad]
            if sum(m['api'] == primero['api'] for m in relacionados) <= 1:
                alternativas = [m for m in relacionados if m['indice'] != indice
                                and m['api'] not in (primero['api'], 'Windows WDM-KS')]
                candidatos.extend(m for m in alternativas if sum(n['api'] == m['api'] for n in alternativas) == 1)
    if pila is None:
        raise RuntimeError('Windows no permitió abrir el micrófono elegido. Selecciónalo de nuevo en Ajustes y vuelve a probar. El detalle quedó en diagnostico-microfono.json.')
    with pila:
        yield tasa

class Microfono:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.modelo = None
        self.diagnostico = {}
        self.confianza_baja = False
        self.whisper = None
        self.modelo_whisper = 'base'
        self.whisper_cargado = None
        self.umbral_microfono_db = None

    @_en_hilo_audio
    def probar(self,detener,actualizar,dispositivo=None):
        from prueba_microfono import grabar
        return grabar(self,detener,actualizar,dispositivo)

    @_en_hilo_audio
    def reproducir_prueba(self,muestra,detener):
        from prueba_microfono import reproducir
        return reproducir(muestra,detener)

    @_en_hilo_audio
    def esperar_activacion(self,detener,detectada,dispositivo=None,motor='mixto',terminar=None,nivel=None,estado=None,lista=None):
        from activacion import esperar
        return esperar(self,detener,detectada,dispositivo,motor,terminar,nivel,estado,lista)

    @_en_hilo_audio
    def escuchar(self, detener, parcial, nivel, limite=18, dispositivo=None, motor='rapido', estado=None):
        self.confianza_baja=False
        if motor in ('preciso','mixto'):
            from reconocimiento import escuchar_preciso, disponible
            if disponible(self.carpeta,self.modelo_whisper):
                return escuchar_preciso(self,detener,nivel,estado or (lambda t:None),limite,dispositivo,idioma='es')
            if estado:estado('Usando Vosk. Abre «Abrir Capri» para preparar el reconocimiento preciso.')
        import sounddevice as sd
        from prueba_microfono import filtrar
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        self.diagnostico = {'seleccion': dispositivo, 'intentos': []}
        indice = resolver_microfono(dispositivo)
        datos = sd.query_devices(indice, kind='input') if indice is not None else sd.query_devices(kind='input')
        ruta = self.carpeta/'vosk-model-small-es-0.42'
        if not ruta.is_dir():
            raise RuntimeError('Falta el reconocimiento en español. Cierra Capri y vuelve a abrir el instalador para completarlo.')
        if self.modelo is None:
            self.modelo = Model(str(ruta))
        audio = queue.Queue(maxsize=80)
        def recibir(datos, frames, reloj, estado):
            try: audio.put_nowait(bytes(datos))
            except queue.Full: pass
        with _abrir_entrada(indice, datos, recibir, detener, self.diagnostico['intentos']) as tasa:
            reconocedor = KaldiRecognizer(self.modelo, tasa)
            inicio = time.monotonic()
            while not detener.is_set() and time.monotonic() - inicio < limite:
                try: datos = audio.get(timeout=.15)
                except queue.Empty: continue
                import array
                muestras = array.array('h', datos)
                rms = (sum(x*x for x in muestras)/max(1, len(muestras))) ** .5 / 32768
                nivel(min(1, rms*10))
                if reconocedor.AcceptWaveform(filtrar(datos,self.umbral_microfono_db)):
                    texto = json.loads(reconocedor.Result()).get('text', '').strip()
                    if texto:
                        return texto
                else:
                    texto = json.loads(reconocedor.PartialResult()).get('partial', '')
                    if texto: parcial(texto)
            return json.loads(reconocedor.FinalResult()).get('text', '').strip()

class Voz:
    def __init__(self, estado):
        self.estado = estado
        self.cancelar = threading.Event()
        self.proceso = None
        self.generacion = 0
        self.natural_no_hasta = 0
        self._control = threading.RLock()
        self._alias = None

    def _vigente(self,token,cancelar):
        return token==self.generacion and not cancelar.is_set()

    def _mci(self,comando,resultado=None,longitud=0):
        if os.name!='nt':return 0
        import ctypes
        mci=ctypes.windll.winmm.mciSendStringW
        mci.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_void_p]
        return mci(comando,resultado,longitud,None)

    def _emitir(self,valor,token,cancelar):
        with self._control:
            if self._vigente(token,cancelar):self.estado(valor)

    def parar(self):
        with self._control:
            self.cancelar.set()
            self.generacion += 1
            proceso=self.proceso;self.proceso=None
            if proceso and proceso.poll() is None:
                try:proceso.terminate()
                except OSError:pass
            alias=self._alias;self._alias=None
            if alias:
                self._mci('stop '+alias)
                self._mci('close '+alias)
            self.estado(False)

    def hablar(self, texto, natural=True, perfil='capri',velocidad=1.0,volumen=100):
        self.parar()
        with self._control:
            self.cancelar = threading.Event()
            token = self.generacion;cancelar=self.cancelar
        threading.Thread(target=self._hablar, args=(texto[:1800], natural, token, cancelar,perfil,velocidad,volumen), daemon=True).start()

    def iniciar_respuesta(self,natural=True,perfil='capri',velocidad=1.0,volumen=100):
        self.parar()
        with self._control:
            self.cancelar=threading.Event()
            self.frases=queue.Queue()
            token=self.generacion;cancelar=self.cancelar;frases=self.frases
        def reproducir():
            while not cancelar.is_set():
                try:texto=frases.get(timeout=.15)
                except queue.Empty:continue
                if texto is None or cancelar.is_set():return
                self._hablar(texto[:1800],natural,token,cancelar,perfil,velocidad,volumen)
        threading.Thread(target=reproducir,daemon=True).start()

    def encolar(self,texto):
        if not self.cancelar.is_set():self.frases.put(texto)

    def terminar_respuesta(self):
        self.frases.put(None)

    def _reproducir_archivo(self,archivo,token,cancelar,volumen=100,marcas=None,texto=None):
        import ctypes
        from sincronia import avance_texto
        alias=f'capri_voice_{token}_{time.monotonic_ns()}'
        duracion=0;ultimo=-1;ultima_actividad=None
        with self._control:
            if not self._vigente(token,cancelar):return False
            # MPEGVideo admite MP3 y WAV, con volumen por alias. WaveAudio no
            # admite setaudio volume (error 261 en Windows).
            tipo='mpegvideo'
            if self._mci(f'open "{archivo}" type {tipo} alias {alias}'):
                raise RuntimeError('No se pudo reproducir la voz natural.')
            self._alias=alias
            self._mci('set '+alias+' time format milliseconds')
            largo=ctypes.create_unicode_buffer(40)
            if not self._mci('status '+alias+' length',largo,40):
                try:duracion=int(largo.value)/1000
                except ValueError:pass
            if self._mci(f'setaudio {alias} volume to {normalizar_volumen(volumen)*10}'):
                self._mci('close '+alias);self._alias=None
                raise RuntimeError('No se pudo ajustar el volumen de Capri.')
            if self._mci('play '+alias):
                self._mci('close '+alias);self._alias=None
                raise RuntimeError('No se pudo iniciar la voz natural.')
            self._emitir(True,token,cancelar)
            if texto:self._emitir(('avance_voz',(texto,0,not bool(marcas))),token,cancelar)
        try:
            while not cancelar.wait(.04):
                resultado=ctypes.create_unicode_buffer(40)
                if self._mci('status '+alias+' mode',resultado,40) or resultado.value!='playing':break
                if texto:
                    posicion=ctypes.create_unicode_buffer(40)
                    if not self._mci('status '+alias+' position',posicion,40):
                        try:
                            segundos=int(posicion.value)/1000
                            indice=avance_texto(texto,segundos,duracion,marcas or ())
                        except ValueError:continue
                        actividad=any(offset<=segundos<offset+largo for offset,largo,*_ in marcas) if marcas else True
                        if indice!=ultimo or actividad!=ultima_actividad:
                            self._emitir(('avance_voz',(texto,indice,actividad)),token,cancelar)
                            ultimo=indice;ultima_actividad=actividad
            if texto and not cancelar.is_set():self._emitir(('avance_voz',(texto,len(texto),False)),token,cancelar)
        finally:
            with self._control:
                self._mci('close '+alias)
                if self._alias==alias:self._alias=None
        return True

    def _reproducir_windows(self,encoded,token,cancelar,emitir=True):
        with self._control:
            if not self._vigente(token,cancelar):return False
            proceso=subprocess.Popen(['powershell.exe','-NoProfile','-EncodedCommand',encoded],creationflags=HIDDEN,
                                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.proceso=proceso
            if emitir:self._emitir(True,token,cancelar)
        try:
            proceso.wait(timeout=100)
            if proceso.returncode and not cancelar.is_set():raise RuntimeError('No pude reproducir la voz de Windows.')
        except subprocess.TimeoutExpired:
            proceso.terminate();raise
        finally:
            with self._control:
                if self.proceso is proceso:self.proceso=None
        return True

    def _hablar(self, texto, natural, token, cancelar,perfil='capri',velocidad=1.0,volumen=100):
        if os.name != 'nt' or not self._vigente(token,cancelar):
            return
        original=texto;texto=texto_para_voz(texto)
        volumen=normalizar_volumen(volumen)
        if not texto or volumen==0:return
        archivo = None
        activo = False
        ritmo,rapidez_windows=parametros_velocidad(velocidad)
        try:
            if natural and time.monotonic() >= self.natural_no_hasta:
                try:
                    import edge_tts
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f: archivo = Path(f.name)
                    eventos=[]
                    async def crear():
                        comunicacion = edge_tts.Communicate(texto, 'es-MX-DaliaNeural' if perfil=='capri' else 'es-CL-FranciscaNeural',
                                                          rate=ritmo,pitch='+16Hz' if perfil=='capri' else '+0Hz',boundary='WordBoundary')
                        async def guardar():
                            with archivo.open('wb') as salida:
                                async for evento in comunicacion.stream():
                                    if evento['type']=='audio':salida.write(evento['data'])
                                    elif evento['type']=='WordBoundary':eventos.append(evento)
                        await asyncio.wait_for(guardar(), timeout=7)
                    asyncio.run(crear())
                    from sincronia import alinear_marcas
                    activo=self._reproducir_archivo(archivo,token,cancelar,volumen,marcas=alinear_marcas(original,eventos),texto=original)
                    return
                except Exception:
                    if cancelar.is_set(): return
                    self.natural_no_hasta = time.monotonic()+45
                    if archivo:archivo.unlink(missing_ok=True);archivo=None
            # El texto viaja como datos base64, nunca interpolado como PowerShell.
            codificado = base64.b64encode(texto.encode('utf8')).decode('ascii')
            with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:archivo=Path(f.name)
            destino=base64.b64encode(str(archivo).encode('utf8')).decode('ascii')
            script = "$ErrorActionPreference='Stop';Add-Type -AssemblyName System.Speech;$v=New-Object System.Speech.Synthesis.SpeechSynthesizer;$v.Volume=100;$v.Rate="+str(rapidez_windows)+";$es=$v.GetInstalledVoices()|Where-Object {$_.VoiceInfo.Culture.Name -like 'es-*'}|Select-Object -First 1;if($es){$v.SelectVoice($es.VoiceInfo.Name)};$v.SetOutputToWaveFile([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+destino+"')));$v.Speak([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + codificado + "')));$v.Dispose()"
            encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
            if self._reproducir_windows(encoded,token,cancelar,emitir=False):
                activo=self._reproducir_archivo(archivo,token,cancelar,volumen,texto=original)
        except Exception:
            self._emitir('No pude reproducir la voz. Puedes seguir usando el chat.',token,cancelar)
        finally:
            if activo:self._emitir(False,token,cancelar)
            if archivo:
                try: archivo.unlink(missing_ok=True)
                except OSError: pass

class Atajo:
    """F8 del sistema; no necesita mantener enfocada la ventana de Capri."""
    def __init__(self, ejecutar, error):
        self.ejecutar = ejecutar; self.error = error
        self.hilo_id = None
        self.hilo = threading.Thread(target=self._run, daemon=True)
        self.hilo.start()

    def _run(self):
        if os.name != 'nt': return
        import ctypes
        from ctypes import wintypes
        user = ctypes.windll.user32
        self.hilo_id = ctypes.windll.kernel32.GetCurrentThreadId()
        if not user.RegisterHotKey(None, 4817, 0x4000, 0x77):
            self.error('F8 está ocupado por otra aplicación. Usa el botón Hablar.')
            return
        try:
            msg = wintypes.MSG()
            while user.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x312: self.ejecutar()
        finally:
            user.UnregisterHotKey(None, 4817)

    def cerrar(self):
        if os.name == 'nt' and self.hilo_id:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self.hilo_id, 0x12, 0, 0)
