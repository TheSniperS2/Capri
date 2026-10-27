import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch, Mock
from urllib.parse import urlsplit,parse_qs
import zipfile

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'src'))
sys.path.insert(0,str(RAIZ))

import core
from core import interpretar, Orden
from recursos import extraer_seguro, descargar

class PruebasTk(unittest.TestCase):
    def setUp(self):
        # Las pruebas crean varias Tk seguidas. Recoger sus ciclos en un hilo de
        # audio puede destruir variables Tcl desde el hilo equivocado.
        import gc
        self.gc_activo=gc.isenabled()
        gc.disable()

    def tearDown(self):
        import gc
        gc.collect()
        if self.gc_activo:gc.enable()

class Ordenes(unittest.TestCase):
    def test_errores_de_transcripcion_no_mandan_apertura_a_charla(self):
        for texto in ['Podríes avrir Spotify?', 'Podrías abrir Spotify?',
                      'Capri, podries avrir Spotify', '¿Puedse abrir Spotify?',
                      'Podría abrir Spotify', 'podrias abrri Spotify', 'avrir Spotify']:
            with self.subTest(texto=texto):
                self.assertEqual(interpretar(texto),Orden('abrir','spotify'))
        with patch.object(core.os,'startfile',create=True) as abrir:
            core.ejecutar(interpretar('Podríes avrir Spotify?'))
            abrir.assert_called_once_with('spotify:')

    def test_correccion_de_apertura_no_reescribe_conversacion_ni_consultas(self):
        for texto in ['no avrir Spotify','no podries avrir Spotify','explícame la frase avrir Spotify',
                      'me gusta Spotify','¿podrías hablar de Spotify?']:
            with self.subTest(texto=texto):self.assertIsNone(interpretar(texto))
        self.assertEqual(interpretar('busca Podríes avrir Spotify'),Orden('buscar','Podríes avrir Spotify'))
        self.assertIsNone(interpretar('avrir una aplicación inventada'))

    def test_charla_no_niega_capacidades_reales_ni_inventa_ejecucion(self):
        negativa='No, no puedo abrir Spotify ni ninguna otra aplicación. Mi función es conversar con la persona, no interactuar con su entorno digital.'
        respuesta={'message':{'content':negativa}}
        with patch.object(core.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(respuesta).encode())),patch.object(core.subprocess,'Popen') as spawn:
            texto=core.IA().conversar('Una petición ambigua','local:test')
        self.assertIn('Sí puedo abrir Spotify',texto)
        self.assertIn('no interpreté una orden',texto)
        spawn.assert_not_called()
        normal='Para abrir aplicaciones uso mi ejecutor.'
        self.assertEqual(core.respuesta_conversacion(normal),normal)

    def test_nombres_ingleses_solo_se_corrigen_al_abrir_apps(self):
        for nombre in ['Spotify','spotifai','es potifai','es por ti','spot ifai']:
            self.assertEqual(interpretar('abre '+nombre),Orden('abrir','spotify'))
        self.assertEqual(interpretar('abre yutub'),Orden('abrir','youtube'))
        self.assertEqual(interpretar('busca es por ti'),Orden('buscar','es por ti'))
        self.assertIsNone(interpretar('esa canción es por ti'))
        with patch.object(core.os,'startfile',create=True) as abrir:
            core.ejecutar(interpretar('abre es por ti'))
            abrir.assert_called_once_with('spotify:')
    def test_pestanas_por_ordenes_naturales(self):
        for texto in ['abre una pestaña del Opera GX', '¿Puedes abrirme una pestaña en Opera GX?',
                      'Me gustaría que abrieras una pestaña del Opera GX.',
                      'Capri, por favor abre una nueva pestaña en el Opera GX',
                      'Quiero que me abras una pestaña nueva en Opera GX',
                      'Ábreme una pestaña','Quisiera una pestaña nueva en Opera GX',
                      'Podrías abrir una pestaña en Opera ge equis']:
            with self.subTest(texto=texto):self.assertEqual(interpretar(texto),Orden('pestana'))
        self.assertEqual(interpretar('Abre una pestaña nueva y busca fotos de Saturno'),Orden('buscar','fotos de Saturno'))
        self.assertEqual(interpretar('Abre una pestaña en YouTube'),Orden('pestana','https://www.youtube.com/'))

    def test_pestana_llama_opera_y_no_simula_accion(self):
        spawn=Mock()
        with patch.object(core,'localizar_opera',return_value=Path('C:/Opera/opera.exe')):
            r=core.ejecutar(interpretar('¿Puedes abrirme una pestaña en Opera GX?'),spawn=spawn)
        self.assertEqual(spawn.call_args.args[0],[str(Path('C:/Opera/opera.exe')),'about:blank'])
        self.assertFalse(spawn.call_args.kwargs['shell'])
        self.assertIn('Opera GX',r)
        with patch.object(core,'localizar_opera',return_value=Path('C:/Opera/opera.exe')):
            with self.assertRaises(OSError):core.ejecutar(Orden('pestana'),spawn=Mock(side_effect=OSError('No abrió')))

    def test_accion_no_disponible_no_llega_a_charla(self):
        for texto in ['puedes cerrar Opera','haz clic en descargar','borra mis documentos','instala ese programa','ejecuta powershell']:
            self.assertEqual(interpretar(texto).tipo,'no_admitida')
        for texto in ['No quiero que abras una pestaña','Explícame cómo abrir una pestaña','Dime qué significa abre Opera']:
            self.assertIsNone(interpretar(texto))

    def test_orden_velocidad_sin_generacion(self):
        self.assertEqual(interpretar('Capri, habla más rápido'),Orden('velocidad_voz','subir'))
        self.assertEqual(interpretar('lee más lento'),Orden('velocidad_voz','bajar'))
    def test_identidad_y_charla_breves_sin_generacion(self):
        for texto in ['¿Cómo te llamas?','¿Cuál es tu nombre?','¿Quién eres?','Capri, ¿cómo te llamas?']:
            self.assertEqual(interpretar(texto),Orden('identidad'))
            self.assertIn('Capri',core.ejecutar(interpretar(texto)))
        self.assertEqual(interpretar('¿Puedo hablar contigo?'),Orden('charla'))
        self.assertIn('podemos hablar',core.ejecutar(Orden('charla')))

    def test_identidad_no_cambia_negaciones_correctas(self):
        self.assertEqual(core.mantener_identidad('Me llamo Luna.'),'Me llamo Capri.')
        self.assertEqual(core.mantener_identidad('No, no me llamo Luna. Me llamo Capri.'),'No, no me llamo Luna. Me llamo Capri.')
        self.assertEqual(core.mantener_identidad('No soy Luna, soy Capri.'),'No soy Luna, soy Capri.')

    def test_respuesta_progresiva_conserva_identidad_y_opciones_rapidas(self):
        mensajes=[{'message':{'content':'Soy Capri.'},'done':False},
                  {'message':{'content':' ¿Qué tienes en mente?'},'done':False},
                  {'done':True,'eval_count':12,'load_duration':0}]
        archivo=io.BytesIO(b'\n'.join(json.dumps(m).encode() for m in mensajes))
        parciales=[]
        with patch.object(core.urllib.request,'urlopen',return_value=archivo) as red:
            ia=core.IA();texto=ia.conversar('Hola','local:test',al_texto=parciales.append)
        self.assertEqual(parciales,['Soy Capri.','Soy Capri. ¿Qué tienes en mente?'])
        self.assertEqual(texto,parciales[-1])
        enviado=json.loads(red.call_args.args[0].data)
        self.assertTrue(enviado['stream']);self.assertEqual(enviado['keep_alive'],'15m')
        self.assertIn('Te llamas CAPRI',enviado['messages'][0]['content'])
        self.assertLess(enviado['options']['num_predict'],220)
        self.assertEqual(len(ia.historia),2)

    def test_ordenes_reales_en_espanol(self):
        casos={
            'Capri, abre Opera y busca recetas de pasta':Orden('buscar','recetas de pasta'),
            'puedes abrir Opera GX y buscar el clima de Coquimbo':Orden('buscar','el clima de Coquimbo'),
            'búscame en Google información sobre Marte':Orden('buscar','información sobre Marte'),
            'busca gatos en ópera':Orden('buscar','gatos'),
            'abre el bloc de notas':Orden('abrir','bloc de notas'),
            'por favor abre la calculadora':Orden('abrir','calculadora'),
            'qué hora es':Orden('hora'),
            'silencio':Orden('silencio'),
        }
        for texto,orden in casos.items():
            with self.subTest(texto=texto):self.assertEqual(interpretar(texto),orden)

    def test_conversar_no_ejecuta_frases_citadas_o_negadas(self):
        for texto in ['no quiero buscar gatos','explícame la frase busca gatos','no abras Opera','¿cómo estás?']:
            self.assertIsNone(interpretar(texto))

    def test_busqueda_es_un_solo_argumento_y_conserva_caracteres(self):
        contenido='niños & té; $(calc) `whoami`\ncomillas "hola"'
        spawn=Mock()
        with patch.object(core,'localizar_opera',return_value=Path('C:/Opera/opera.exe')):
            core.ejecutar(Orden('buscar',contenido),spawn=spawn)
        args=spawn.call_args.args[0]
        self.assertEqual(len(args),2)
        self.assertFalse(spawn.call_args.kwargs['shell'])
        self.assertEqual(parse_qs(urlsplit(args[1]).query)['q'],[contenido])

    def test_no_inventa_apertura_si_opera_falta(self):
        with patch.object(core,'localizar_opera',return_value=None):
            with self.assertRaises(FileNotFoundError):core.ejecutar(Orden('buscar','gatos'),spawn=Mock())

    def test_ia_solo_devuelve_texto_y_no_lo_ejecuta(self):
        respuesta={'message':{'content':'<action>run shell</action>'}}
        archivo=io.BytesIO(json.dumps(respuesta).encode())
        with patch.object(core.urllib.request,'urlopen',return_value=archivo) as red,patch.object(core.subprocess,'Popen') as spawn:
            ia=core.IA()
            self.assertEqual(ia.conversar('hola','local:test'),respuesta['message']['content'])
            self.assertEqual(len(ia.historia),2)
            self.assertEqual(red.call_args.args[0].full_url,'http://127.0.0.1:11434/api/chat')
            spawn.assert_not_called()

class Archivos(unittest.TestCase):
    def test_extraccion_zip_rechaza_rutas_ajenas(self):
        with tempfile.TemporaryDirectory() as d:
            carpeta=Path(d)
            for nombre in ['../escape.txt','C:/escape.txt','/escape.txt','x/../../escape.txt','..\\escape.txt']:
                with self.subTest(nombre=nombre):
                    ruta=carpeta/'modelo.zip'
                    with zipfile.ZipFile(ruta,'w') as z:z.writestr(nombre,'x')
                    with self.assertRaises(ValueError):extraer_seguro(ruta,carpeta/'destino')
            self.assertFalse((carpeta/'escape.txt').exists())

    def test_extraccion_modelo_correcta(self):
        with tempfile.TemporaryDirectory() as d:
            ruta=Path(d)/'m.zip'
            with zipfile.ZipFile(ruta,'w') as z:z.writestr('modelo/am/final.mdl','modelo')
            extraer_seguro(ruta,Path(d)/'destino')
            self.assertTrue((Path(d)/'destino/modelo/am/final.mdl').exists())

    def test_descarga_incompleta_no_queda_como_lista(self):
        class Respuesta(io.BytesIO):headers={'Content-Length':'10'}
        with tempfile.TemporaryDirectory() as d,patch('recursos.urllib.request.urlopen',return_value=Respuesta(b'ab')):
            ruta=Path(d)/'modelo.zip'
            with self.assertRaises(OSError):descargar('https://ejemplo.invalid/modelo.zip',ruta)
            self.assertFalse(ruta.exists());self.assertFalse(ruta.with_suffix('.zip.part').exists())

class EntradaVoz(unittest.TestCase):
    def test_volumen_de_voz_natural_se_aplica_antes_de_reproducir(self):
        import voz
        self.assertEqual(voz.normalizar_volumen(-20),0)
        self.assertEqual(voz.normalizar_volumen(200),100)
        self.assertEqual(voz.normalizar_volumen(float('nan')),100)
        self.assertEqual(voz.normalizar_volumen('incorrecto'),100)
        v=voz.Voz(lambda x:None);comandos=[]
        def mci(cmd,*args):
            comandos.append(cmd)
            if cmd.startswith('status '):args[0].value='stopped'
            return 0
        with patch.object(v,'_mci',side_effect=mci):
            self.assertTrue(v._reproducir_archivo(Path('voz.mp3'),v.generacion,v.cancelar,35))
        ajuste=next(i for i,c in enumerate(comandos) if c.startswith('setaudio ') and c.endswith('volume to 350'))
        reproduccion=next(i for i,c in enumerate(comandos) if c.startswith('play '))
        self.assertLess(ajuste,reproduccion)

    def test_volumen_windows_y_silencio_no_sintetiza(self):
        import voz,base64
        v=voz.Voz(lambda x:None)
        with patch.object(v,'_reproducir_windows',return_value=True) as reproducir:
            v._hablar('Hola',False,v.generacion,v.cancelar,volumen=35)
            script=base64.b64decode(reproducir.call_args.args[0]).decode('utf-16-le')
            self.assertIn('$v.Volume=35;',script)
            reproducir.reset_mock()
            v._hablar('Hola',False,v.generacion,v.cancelar,volumen=0)
            reproducir.assert_not_called()

    def test_velocidad_normal_y_ajustes_en_ambos_motores(self):
        from voz import parametros_velocidad,normalizar_velocidad
        self.assertEqual(parametros_velocidad(1.35),('+35%',3))
        self.assertEqual(parametros_velocidad(1.0),('+0%',0))
        self.assertEqual(parametros_velocidad(),('+0%',0))
        self.assertEqual(normalizar_velocidad('texto'),1.0)
        self.assertEqual(normalizar_velocidad(float('nan')),1.0)
        self.assertEqual(normalizar_velocidad(20),1.8)
    def test_whisper_usa_audio_en_memoria_espanol_y_confianza(self):
        import reconocimiento as rec,voz,array,numpy as np
        from contextlib import contextmanager
        from collections import deque
        datos_transcripcion=[]
        class Modelo:
            def transcribe(self,audio,**kwargs):
                datos_transcripcion.append((audio,kwargs))
                return iter([types.SimpleNamespace(text='Abre Opera y busca gatos.',avg_logprob=-1.2,no_speech_prob=.1)]),None
        voz_datos=array.array('h',[1200]*24000).tobytes()
        silencio=bytes(48000)
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            for bloque in [voz_datos,silencio,silencio,silencio,silencio]:recibir(bloque,24000,None,None)
            yield 48000
        reloj=iter([0,.1,.2,.5,.8,1.1,1.4,1.7,2,2.3,2.6,3,4,5,6,7,8])
        sd=types.SimpleNamespace(query_devices=lambda *a,**kw:{'name':'USB','default_samplerate':48000})
        micro=types.SimpleNamespace(whisper=Modelo(),carpeta=Path('.'),confianza_baja=False)
        with patch.dict(sys.modules,{'sounddevice':sd}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch.object(rec.time,'monotonic',side_effect=lambda:next(reloj)):
            texto=rec.escuchar_preciso(micro,threading.Event(),lambda n:None,lambda t:None,18,{'indice':23})
        self.assertEqual(texto,'Abre Opera y busca gatos.')
        self.assertTrue(micro.confianza_baja)
        self.assertIsInstance(datos_transcripcion[0][0],np.ndarray)
        self.assertEqual(datos_transcripcion[0][0].dtype,np.float32)
        self.assertEqual(datos_transcripcion[0][1]['language'],'es')
        self.assertTrue(datos_transcripcion[0][1]['vad_filter'])
        self.assertEqual(datos_transcripcion[0][1]['beam_size'],5)
        self.assertIn('Siguiente canción',datos_transcripcion[0][1]['initial_prompt'])
        self.assertIn('reproduce',datos_transcripcion[0][1]['hotwords'])

    def test_pcm_16k_y_remuestreo_no_utilizan_av_open(self):
        import reconocimiento as rec,numpy as np,av
        with patch.object(av,'open',side_effect=AssertionError('No se debe decodificar un WAV')):
            for tasa in [16000,44100,48000]:
                with self.subTest(tasa=tasa):
                    tiempo=np.arange(tasa)/tasa
                    pcm=(np.sin(2*np.pi*440*tiempo)*16000).astype('<i2').tobytes()
                    salida=rec.preparar_pcm(pcm,tasa)
                    self.assertEqual(salida.dtype,np.float32)
                    self.assertLessEqual(abs(len(salida)-16000),1)
                    self.assertGreater(np.max(np.abs(salida)),.4)
                    self.assertLess(np.max(np.abs(salida)),1)
        self.assertEqual(rec.preparar_pcm(b'',48000).size,0)
        with self.assertRaises(ValueError):rec.preparar_pcm(b'\x01',48000)

    def test_voz_progresiva_respeta_orden_sin_cancelar_primera_frase(self):
        import voz
        habladas=[];listo=threading.Event()
        v=voz.Voz(lambda estado:None)
        def decir(texto,*args):
            habladas.append(texto)
            if len(habladas)==2:listo.set()
        with patch.object(v,'_hablar',side_effect=decir),patch.object(v,'parar',side_effect=lambda:None):
            v.iniciar_respuesta();v.encolar('Soy Capri.');v.encolar('Te escucho.');v.terminar_respuesta()
            self.assertTrue(listo.wait(2))
        v.cancelar.set()
        self.assertEqual(habladas,['Soy Capri.','Te escucho.'])

    def test_lectura_fluida_sin_pausas_de_formato(self):
        from voz import texto_para_voz
        self.assertEqual(texto_para_voz('**Hola**, Alex; aquí estoy:\n\nseguimos... Bien.'),'Hola Alex aquí estoy seguimos. Bien.')
        self.assertEqual(texto_para_voz('Son las 12:30, cuesta 3,5 euros.'),'Son las 12:30 cuesta 3,5 euros.')

    def test_audio_cancelado_no_arranca_despues(self):
        import voz
        v=voz.Voz(lambda estado:None);cancelar=v.cancelar;token=v.generacion
        v.parar()
        with patch.object(v,'_mci') as mci:
            self.assertFalse(v._reproducir_archivo(Path('clip.mp3'),token,cancelar))
            mci.assert_not_called()

    def test_interrumpir_cierra_clip_y_no_vuelve_a_reproducir(self):
        import voz
        v=voz.Voz(lambda estado:None);token=v.generacion;cancelar=v.cancelar
        comandos=[];empezo=threading.Event()
        def mci(cmd,*args):
            comandos.append(cmd)
            if cmd.startswith('play '):empezo.set()
            if cmd.startswith('status '):args[0].value='playing'
            return 0
        with patch.object(v,'_mci',side_effect=mci):
            hilo=threading.Thread(target=v._reproducir_archivo,args=(Path('clip.mp3'),token,cancelar))
            hilo.start();self.assertTrue(empezo.wait(2));v.parar();despues=len(comandos)
            hilo.join(2);self.assertFalse(hilo.is_alive())
        self.assertTrue(any(c.startswith('stop ') for c in comandos))
        self.assertFalse(any(c.startswith('play ') for c in comandos[despues:]))
        self.assertIsNone(v._alias)

    def test_interrumpir_durante_creacion_de_voz_windows(self):
        import voz
        v=voz.Voz(lambda estado:None);creando=threading.Event();permitir=threading.Event();muerto=threading.Event()
        class Proceso:
            returncode=0
            def poll(self):return 0 if muerto.is_set() else None
            def terminate(self):muerto.set()
            def wait(self,**kw):muerto.wait(2);return 0
        def crear(*a,**kw):creando.set();permitir.wait(2);return Proceso()
        with patch.object(voz.subprocess,'Popen',side_effect=crear):
            hilo=threading.Thread(target=v._reproducir_windows,args=('texto-codificado',v.generacion,v.cancelar))
            hilo.start();self.assertTrue(creando.wait(2))
            detener=threading.Thread(target=v.parar);detener.start();permitir.set()
            detener.join(2);hilo.join(2)
            self.assertTrue(muerto.is_set());self.assertFalse(hilo.is_alive())
            self.assertIsNone(v.proceso)

    def test_modo_mixto_transcribe_sin_imponer_espanol(self):
        import voz,reconocimiento
        with patch.object(reconocimiento,'disponible',return_value=True),patch.object(reconocimiento,'escuchar_preciso',return_value='Abre Spotify') as escuchar:
            texto=voz.Microfono(Path('.')).escuchar(threading.Event(),lambda t:None,lambda n:None,motor='mixto')
        self.assertEqual(texto,'Abre Spotify')
        self.assertIsNone(escuchar.call_args.kwargs['idioma'])

    def test_reintenta_otra_interfaz_del_usb_sin_cambiar_de_microfono(self):
        import voz
        aperturas=[];cerrados=[];ajustes=[]
        class Stream:
            def __init__(self,**opciones):self.opciones=opciones;aperturas.append(opciones)
            def __enter__(self):
                if self.opciones['device']==23:raise RuntimeError('No se pudo iniciar WASAPI')
                return self
            def __exit__(self,*args):cerrados.append(self.opciones['device'])
            def close(self):cerrados.append(self.opciones['device'])
        sd=types.SimpleNamespace(query_hostapis=lambda i:{'name':'Windows WASAPI'},
                                 query_devices=lambda i,**kw:{'default_samplerate':44100},
                                 WasapiSettings=lambda **kw:ajustes.append(kw) or kw,RawInputStream=Stream)
        catalogo=[{'indice':23,'nombre':'Microphone (USB MICROPHONE)','api':'Windows WASAPI'},
                  {'indice':2,'nombre':'Microphone (USB MICROPHONE)','api':'MME'},
                  {'indice':1,'nombre':'Audífonos averiados','api':'MME'}]
        datos={'name':'Microphone (USB MICROPHONE)','hostapi':0,'default_samplerate':48000}
        intentos=[]
        with patch.dict(sys.modules,{'sounddevice':sd}),patch.object(voz,'listar_microfonos',return_value=catalogo):
            with voz._abrir_entrada(23,datos,lambda *a:None,threading.Event(),intentos) as tasa:
                self.assertEqual(tasa,44100)
        self.assertEqual([a['device'] for a in aperturas],[23,2])
        self.assertTrue(all(a['blocksize']==0 for a in aperturas))
        self.assertEqual(ajustes,[{'exclusive':False,'auto_convert':True}])
        self.assertEqual(cerrados,[23,2])

    def test_configuracion_antigua_wdm_se_abre_por_wasapi(self):
        import voz
        dispositivos=[]
        class Stream:
            def __init__(self,**kw):dispositivos.append(kw['device'])
            def __enter__(self):return self
            def __exit__(self,*args):pass
        sd=types.SimpleNamespace(query_hostapis=lambda i:{'name':'Windows WDM-KS'},
                                 query_devices=lambda i,**kw:{'default_samplerate':48000},
                                 WasapiSettings=lambda **kw:kw,RawInputStream=Stream)
        datos={'name':'Micrófono (USB MICROPHONE)','hostapi':0,'default_samplerate':44100}
        catalogo=[{'indice':32,'nombre':datos['name'],'api':'Windows WDM-KS'},
                  {'indice':23,'nombre':'Microphone (USB MICROPHONE)','api':'Windows WASAPI'}]
        with patch.dict(sys.modules,{'sounddevice':sd}),patch.object(voz,'listar_microfonos',return_value=catalogo):
            with voz._abrir_entrada(32,datos,lambda *a:None,threading.Event(),[]) as tasa:self.assertEqual(tasa,48000)
        self.assertEqual(dispositivos,[23])

    def test_no_reintenta_otro_usb_con_nombre_ambiguo(self):
        import voz
        aperturas=[]
        def crear(**kw):aperturas.append(kw['device']);raise RuntimeError('No se pudo abrir')
        sd=types.SimpleNamespace(query_hostapis=lambda i:{'name':'Windows WASAPI'},
                                 WasapiSettings=lambda **kw:kw,RawInputStream=crear)
        nombre='Microphone (USB MICROPHONE)'
        catalogo=[{'indice':23,'nombre':nombre,'api':'Windows WASAPI'},
                  {'indice':25,'nombre':nombre,'api':'Windows WASAPI'},
                  {'indice':2,'nombre':nombre,'api':'MME'}]
        with patch.dict(sys.modules,{'sounddevice':sd}),patch.object(voz,'listar_microfonos',return_value=catalogo):
            with self.assertRaisesRegex(RuntimeError,'Windows no permitió'):
                with voz._abrir_entrada(23,{'name':nombre,'hostapi':0,'default_samplerate':48000},lambda *a:None,threading.Event(),[]):pass
        self.assertEqual(aperturas,[23])

    def test_com_se_libera_si_la_captura_lanza_error(self):
        import voz,ctypes
        if voz.os.name!='nt':self.skipTest('COM solo existe en Windows')
        ole=types.SimpleNamespace(CoInitializeEx=Mock(return_value=0),CoUninitialize=Mock())
        with patch.object(ctypes,'WinDLL',return_value=ole):
            with self.assertRaises(ValueError):
                with voz._com_audio():raise ValueError('fallo de captura')
        ole.CoInitializeEx.assert_called_once_with(None,0)
        ole.CoUninitialize.assert_called_once()

    def test_audio_y_enumeracion_comparten_hilo(self):
        import voz
        hilos=[]
        sd=types.SimpleNamespace(query_hostapis=lambda:[{'name':'MME'}],
                                 query_devices=lambda:hilos.append(threading.get_ident()) or [{'name':'USB','hostapi':0,'max_input_channels':1}])
        @voz._en_hilo_audio
        def trabajo_audio():hilos.append(threading.get_ident())
        with patch.dict(sys.modules,{'sounddevice':sd}):
            voz.listar_microfonos();trabajo_audio()
        self.assertEqual(len(set(hilos)),1)
        self.assertNotEqual(hilos[0],threading.get_ident())

    def test_seleccion_conserva_identidad_si_windows_cambia_indice(self):
        import voz
        elegido={'indice':2,'nombre':'Microphone (USB MICROPHONE)','api':'Windows WASAPI'}
        actuales=[{'indice':2,'nombre':'Audífonos averiados','api':'Windows WASAPI'},
                  {'indice':23,'nombre':'Microphone (USB MICROPHONE)','api':'Windows WASAPI'}]
        with patch.object(voz,'listar_microfonos',return_value=actuales):
            self.assertEqual(voz.resolver_microfono(elegido),23)

    def test_microfono_desconectado_no_cambia_al_predeterminado(self):
        import voz
        elegido={'indice':2,'nombre':'Micrófono de escritorio','api':'MME'}
        with patch.object(voz,'listar_microfonos',return_value=[{'indice':2,'nombre':'Audífonos','api':'MME'}]):
            with self.assertRaisesRegex(RuntimeError,'no está disponible'):
                voz.resolver_microfono(elegido)
        self.assertIsNone(voz.resolver_microfono(None))

    def test_lista_excluye_salidas_y_repeticiones_de_interfaces(self):
        import voz
        dispositivos=[{'name':'Altavoces','max_input_channels':0,'hostapi':0},
                      {'name':'USB','max_input_channels':1,'hostapi':0},
                      {'name':'USB','max_input_channels':1,'hostapi':1}]
        sd=types.SimpleNamespace(query_hostapis=lambda:[{'name':'MME'},{'name':'Windows WASAPI'}],query_devices=lambda:dispositivos)
        with patch.dict(sys.modules,{'sounddevice':sd}):
            self.assertEqual(voz.listar_microfonos(),[{'indice':2,'nombre':'USB','api':'Windows WASAPI'}])
            self.assertEqual(len(voz.listar_microfonos(todas_las_interfaces=True)),2)

    def test_seleccion_mme_antigua_sigue_funcionando(self):
        import voz
        dispositivos=[{'name':'USB','max_input_channels':1,'hostapi':0},
                      {'name':'USB','max_input_channels':1,'hostapi':1}]
        sd=types.SimpleNamespace(query_hostapis=lambda:[{'name':'MME'},{'name':'Windows WASAPI'}],query_devices=lambda:dispositivos)
        with patch.dict(sys.modules,{'sounddevice':sd}):
            self.assertEqual(voz.resolver_microfono({'indice':0,'nombre':'USB','api':'MME'}),0)

    def test_sin_wasapi_no_se_muestran_alias_ni_otras_interfaces(self):
        import voz
        dispositivos=[{'name':'Microsoft Sound Mapper - Input','max_input_channels':1,'hostapi':0},
                      {'name':'USB','max_input_channels':1,'hostapi':0},
                      {'name':'USB','max_input_channels':1,'hostapi':1}]
        sd=types.SimpleNamespace(query_hostapis=lambda:[{'name':'MME'},{'name':'Windows DirectSound'}],query_devices=lambda:dispositivos)
        with patch.dict(sys.modules,{'sounddevice':sd}):
            self.assertEqual(voz.listar_microfonos(),[{'indice':1,'nombre':'USB','api':'MME'}])

    def test_captura_usa_dispositivo_seleccionado_y_su_frecuencia(self):
        import voz
        streams=[]
        class Reconocedor:
            def __init__(self,modelo,tasa):self.tasa=tasa
            def AcceptWaveform(self,data):return True
            def Result(self):return json.dumps({'text':'hola'})
        class Stream:
            def __init__(self,**kwargs):self.kwargs=kwargs;streams.append(kwargs)
            def __enter__(self):self.kwargs['callback'](bytes(2000),1000,None,None);return self
            def __exit__(self,*args):pass
        sd=types.SimpleNamespace(query_devices=Mock(return_value={'default_samplerate':44100}),RawInputStream=Stream)
        vosk=types.SimpleNamespace(Model=lambda p:object(),KaldiRecognizer=Reconocedor,SetLogLevel=lambda n:None)
        elegido={'indice':23,'nombre':'USB','api':'Windows WASAPI'}
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23):
            (Path(d)/'vosk-model-small-es-0.42').mkdir()
            self.assertEqual(voz.Microfono(d).escuchar(threading.Event(),lambda t:None,lambda n:None,dispositivo=elegido),'hola')
        sd.query_devices.assert_called_once_with(23,kind='input')
        self.assertEqual(streams[0]['device'],23)
        self.assertEqual(streams[0]['samplerate'],44100)

    def test_transcripcion_a_busqueda_sin_microfono_real(self):
        import voz
        resultado='abre opera y busca galaxias'
        class Reconocedor:
            def __init__(self,*args):pass
            def AcceptWaveform(self,data):return True
            def Result(self):return json.dumps({'text':resultado})
        class Stream:
            def __init__(self,**kwargs):self.callback=kwargs['callback']
            def __enter__(self):self.callback(bytes(2000),1000,None,None);return self
            def __exit__(self,*args):pass
        vosk=types.SimpleNamespace(Model=lambda p:object(),KaldiRecognizer=Reconocedor,SetLogLevel=lambda n:None)
        sd=types.SimpleNamespace(query_devices=lambda **kwargs:{'default_samplerate':48000},RawInputStream=Stream)
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'vosk':vosk,'sounddevice':sd}):
            (Path(d)/'vosk-model-small-es-0.42').mkdir()
            texto=voz.Microfono(d).escuchar(threading.Event(),lambda t:None,lambda n:None)
            self.assertEqual(interpretar(texto),Orden('buscar','galaxias'))

class Interfaz(PruebasTk):
    def test_volumen_ajustes_se_guarda_y_llega_a_la_voz(self):
        import app as modulo
        with tempfile.TemporaryDirectory() as d,patch.object(modulo,'BASE',Path(d)),patch.object(modulo.Capri,'cargar_microfonos'),patch.object(modulo.Voz,'hablar') as hablar:
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.configurar();capri.ajustes.withdraw()
                capri.escala_volumen.set(35);capri.root.update()
                capri.escala_volumen.tk.call(capri.escala_volumen.cget('command'),35)
                cfg=json.loads((Path(d)/'ajustes.json').read_text(encoding='utf-8'))
                self.assertEqual(cfg['volumen_voz'],35)
                capri.narrar_respuesta(capri.peticion,'Hola',final=True)
                self.assertEqual(hablar.call_args.kwargs['volumen'],35)
            finally:capri.cerrar()

    def test_peticion_de_pestana_no_pasa_por_modelo(self):
        import app as modulo
        with patch.object(modulo.Voz,'parar'),patch.object(modulo.Voz,'hablar'),patch.object(modulo.IA,'conversar') as modelo,patch.object(modulo,'ejecutar',return_value='Orden enviada a Opera GX') as accion:
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.enviar('Me gustaría que abrieras una pestaña del Opera GX')
                capri.panel.withdraw();limite=time.monotonic()+2
                while capri.ocupada and time.monotonic()<limite:capri.root.update();time.sleep(.01)
                accion.assert_called_once_with(Orden('pestana'))
                modelo.assert_not_called()
                self.assertIn('Orden enviada a Opera GX',capri.chat.get('1.0','end'))
            finally:capri.cerrar()

    def test_velocidad_por_voz_se_guarda_y_se_aplica(self):
        import app as modulo
        with tempfile.TemporaryDirectory() as d,patch.object(modulo,'BASE',Path(d)),patch.object(modulo.Voz,'parar'),patch.object(modulo.Voz,'hablar') as voz,patch.object(modulo.IA,'conversar') as modelo:
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.enviar('Habla más rápido');capri.panel.withdraw()
                self.assertEqual(capri.cfg['velocidad_voz'],1.15)
                self.assertEqual(json.loads((Path(d)/'ajustes.json').read_text(encoding='utf8'))['velocidad_voz'],1.15)
                self.assertEqual(voz.call_args.kwargs['velocidad'],1.15)
                modelo.assert_not_called()
            finally:capri.cerrar()
    def test_texto_progresivo_y_una_sola_lectura_continua(self):
        import app as modulo
        continuar=threading.Event()
        def respuesta(texto,modelo,al_texto,cancelar):
            al_texto('Soy Capri.')
            continuar.wait(2)
            al_texto('Soy Capri. ¿Qué quieres contarme?')
            return 'Soy Capri. ¿Qué quieres contarme?'
        with patch.object(modulo.Voz,'parar'),patch.object(modulo.Voz,'iniciar_respuesta') as fragmentar,patch.object(modulo.Voz,'hablar') as voz,patch.object(modulo.IA,'conversar',side_effect=respuesta):
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.enviar('Cuéntame algo');capri.panel.withdraw()
                limite=time.monotonic()+2
                while 'Soy Capri.' not in capri.chat.get('1.0','end') and time.monotonic()<limite:capri.root.update();time.sleep(.01)
                self.assertTrue(capri.ocupada)
                voz.assert_not_called()
                continuar.set()
                while capri.ocupada and time.monotonic()<limite:capri.root.update();time.sleep(.01)
                self.assertFalse(capri.ocupada)
                voz.assert_called_once()
                self.assertEqual(voz.call_args.args[0],'Soy Capri. ¿Qué quieres contarme?')
                self.assertEqual(voz.call_args.kwargs['velocidad'],1.0)
                fragmentar.assert_not_called()
                self.assertEqual(capri.chat.get('1.0','end').count('Soy Capri.'),1)
            finally:continuar.set();capri.cerrar()

    def test_hablar_interrumpe_modelo_y_voz_antes_de_escuchar(self):
        import app as modulo
        soltar=threading.Event();iniciado=threading.Event()
        def escuchar(*a,**kw):iniciado.set();soltar.wait(2);return ''
        with patch.object(modulo.Voz,'parar') as parar,patch.object(modulo.Voz,'hablar') as voz,patch.object(modulo.Microfono,'escuchar',side_effect=escuchar):
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.ocupada=True;capri.hablando=True
                vieja=capri.peticion;cancelar=capri.respuesta_stop
                capri.hablar()
                self.assertTrue(iniciado.wait(2));parar.assert_called()
                self.assertTrue(cancelar.is_set());self.assertFalse(capri.ocupada)
                self.assertFalse(capri.hablando);self.assertTrue(capri.escuchando)
                capri.eventos.put(('respuesta',(vieja,'Esta respuesta debe ignorarse')))
                capri.eventos.put(('voz',(capri.voz.generacion-1,True)))
                capri.poll();voz.assert_not_called()
                self.assertEqual(capri.estado,'Te escucho…')
            finally:soltar.set();capri.cerrar()

    def test_transcripcion_dudosa_queda_editable_sin_ejecutar(self):
        import app as modulo
        with patch.object(modulo.Voz,'parar'):
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.micro.confianza_baja=True
                with patch.object(capri,'enviar') as enviar:
                    capri.eventos.put(('transcripcion','abre calculadora'))
                    capri.poll()
                    enviar.assert_not_called()
                    self.assertEqual(capri.entrada.get(),'abre calculadora')
            finally:capri.cerrar()

    def test_selector_recuerda_microfono_sin_reemplazar_otros_ajustes(self):
        import app as modulo
        elegido={'indice':23,'nombre':'Microphone (USB MICROPHONE)','api':'Windows WASAPI'}
        with tempfile.TemporaryDirectory() as d,patch.object(modulo,'BASE',Path(d)),patch.object(modulo,'listar_microfonos',return_value=[elegido]),patch.object(modulo.Voz,'parar'):
            carpeta=Path(d)
            (carpeta/'ajustes.json').write_text(json.dumps({'voz':False,'modelo':'mi-modelo'}),encoding='utf8')
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.configurar();capri.ajustes.withdraw()
                limite=time.monotonic()+2
                while not hasattr(capri,'micro_opciones') and time.monotonic()<limite:
                    capri.root.update();time.sleep(.01)
                self.assertEqual(capri.micro_opciones,[None,elegido])
                capri.micro_combo.current(1);capri.elegir_microfono()
                cfg=json.loads((carpeta/'ajustes.json').read_text(encoding='utf8'))
                self.assertEqual(cfg['microfono'],elegido)
                self.assertFalse(cfg['voz']);self.assertEqual(cfg['modelo'],'mi-modelo')
                capri.mostrar_microfonos([elegido])
                self.assertEqual(capri.micro_combo.current(),1)
                # La lista sigue teniendo una entrada por micrófono con una selección
                # guardada de otra interfaz, sin sobrescribirla automáticamente.
                antiguo=dict(elegido,api='MME',indice=2)
                capri.cfg['microfono']=antiguo
                capri.mostrar_microfonos([elegido])
                self.assertEqual(len(capri.micro_combo['values']),2)
                self.assertEqual(capri.micro_combo['values'][1],elegido['nombre'])
                self.assertEqual(capri.cfg['microfono'],antiguo)
            finally:capri.cerrar()
            segunda=modulo.Capri(hotkeys=False);segunda.root.withdraw()
            try:self.assertEqual(segunda.cfg['microfono'],elegido)
            finally:segunda.cerrar()

    def test_chat_orden_y_cancelacion_de_respuesta(self):
        import app as modulo
        with patch.object(modulo.Voz,'parar'),patch.object(modulo.Voz,'hablar') as hablar,patch.object(modulo,'ejecutar',return_value='Busqué gatos en Opera GX.') as ejecutar:
            capri=modulo.Capri(hotkeys=False)
            capri.root.withdraw()
            try:
                capri.abrir_chat();capri.panel.withdraw()
                capri.enviar('abre Opera y busca gatos')
                limite=time.monotonic()+2
                while capri.ocupada and time.monotonic()<limite:
                    capri.root.update();time.sleep(.01)
                self.assertFalse(capri.ocupada)
                self.assertIn('Busqué gatos',capri.chat.get('1.0','end'))
                ejecutar.assert_called_once_with(Orden('buscar','gatos'))
                capri.ocupada=True;capri.peticion+=1
                ticket=capri.peticion
                capri.parar()
                hablar.reset_mock()
                capri.eventos.put(('respuesta',(ticket,'Esta respuesta fue cancelada')))
                capri.poll()
                self.assertNotIn('Esta respuesta fue cancelada',capri.chat.get('1.0','end'))
                hablar.assert_not_called()
            finally:capri.cerrar()

class AmpliacionEscritorio(PruebasTk):
    def test_errores_reales_de_dictado_musical_solo_en_orden_completa(self):
        for texto in ['Revoluces la canción.','Capri, revoluces la canción','reproduse mi musica']:
            self.assertEqual(interpretar(texto),Orden('spotify',''))
        for texto in ['ciente canción.','siguente cancion','ciente pista en Spotify']:
            self.assertEqual(interpretar(texto),Orden('spotify_siguiente'))
        for texto in ['no revoluces la canción','no ciente canción','explica ciente canción','me gusta la frase ciente canción']:
            self.assertIsNone(interpretar(texto))
        self.assertEqual(interpretar('busca revoluces la canción'),Orden('buscar','revoluces la canción'))
        self.assertEqual(interpretar('reproduce Ciente de Artist'),Orden('spotify','Ciente de Artist'))
        with patch('multimedia.controlar_sesion',return_value='Pedido al ejecutor') as controlar:
            core.ejecutar(interpretar('ciente canción'))
            controlar.assert_called_once_with('siguiente')

    def test_chat_no_confirma_reproduccion_inventada_del_dialogo_real(self):
        respuesta=core.respuesta_conversacion('¡Genial! Ahora tengo una reproducción en marcha. ¿Quieres saber qué canción es?')
        self.assertNotIn('reproducción en marcha',respuesta)
        self.assertNotIn('Reanudé la reproducción',core.respuesta_conversacion('Reanudé la reproducción.'))

    def test_playlist_alias_no_depende_del_nombre_de_su_boton(self):
        import playlists,base64
        with tempfile.TemporaryDirectory() as d:
            carpeta=Path(d);playlists.vincular('juntos','spotify:playlist:1234567890123456789012',carpeta)
            abrir=Mock();correr=Mock(return_value=types.SimpleNamespace(stdout='{"ok":true}',returncode=0))
            self.assertIn('Activé',playlists.reproducir_playlist('juntos',carpeta,abrir,correr))
            datos=json.loads(correr.call_args.kwargs['input'])
            self.assertEqual(datos['accion'],'playlist')
            codigo=base64.b64decode(correr.call_args.args[0][-1]).decode('utf-16-le')
            self.assertEqual(codigo,playlists.PLAYLIST_UI)
            correr.return_value=types.SimpleNamespace(stdout='{"ok":false}',returncode=0)
            self.assertIn('no confirmó',playlists.reproducir_playlist('juntos',carpeta,abrir,correr))

    def test_selector_playlist_real_no_confunde_boton_global_o_cancion(self):
        import os,playlists,base64,subprocess
        if os.name!='nt':self.skipTest('Selector UIA de Windows')
        funcion=playlists.PLAYLIST_UI.split(' function Coincide',1)[1].split(' $limite=',1)[0]
        funcion='function Coincide'+funcion
        script=funcion+'''\n$d=[Console]::In.ReadToEnd()|ConvertFrom-Json
@($d|ForEach-Object {Coincide $_.nombre $_.titulo ([bool]$_.pausa)})|ConvertTo-Json -Compress
'''
        casos=[{'nombre':'Reproducir 🤍🤍🤍','titulo':'🤍🤍🤍','pausa':False},
               {'nombre':'Reproducir una canción','titulo':'🤍🤍🤍','pausa':False},
               {'nombre':'Pausar','titulo':'🤍🤍🤍','pausa':True},
               {'nombre':'Pausar 🤍🤍🤍','titulo':'🤍🤍🤍','pausa':True},
               {'nombre':'Play lista [1]','titulo':'lista [1]','pausa':False}]
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16-le')).decode()],input=json.dumps(casos),text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),[True,False,False,True,True])

    def test_musica_actual_y_siguiente_no_son_busquedas(self):
        for texto in ['reproduce la música','reproduce música','reanuda la canción','pon la música',
                      'podrías poner la música','continúa la reproducción']:
            with self.subTest(texto=texto):self.assertEqual(interpretar(texto),Orden('spotify',''))
        for texto in ['salta la canción','saltar la canción','siguiente canción','pon la siguiente canción de la playlist',
                      'podrías poner la música siguiente','reproduce la música siguiente','pasa a la siguiente canción',
                      'a siguiente canción de la playlist']:
            with self.subTest(texto=texto):self.assertEqual(interpretar(texto),Orden('spotify_siguiente'))
        self.assertEqual(interpretar('pon la canción anterior'),Orden('spotify_anterior'))
        self.assertEqual(interpretar('¿qué canción está sonando?'),Orden('spotify_estado'))
        self.assertEqual(interpretar('pon mi playlist privada Cyberpunk en Spotify'),Orden('spotify_playlist','Cyberpunk'))
        self.assertIsNone(interpretar('no pongas la siguiente canción'))
        self.assertEqual(interpretar('busca la siguiente canción de la playlist'),Orden('buscar','la siguiente canción de la playlist'))

    def test_reanudar_no_abre_uri_ni_cambia_contexto(self):
        from escritorio import controlar_spotify
        from multimedia import controlar_sesion
        abrir=Mock();correr=Mock(return_value=types.SimpleNamespace(stdout='{"ok":true,"estado":"Playing","titulo":"Ya estaba puesta"}',returncode=0))
        self.assertIn('Reanudé',controlar_spotify('',abrir=abrir,correr=correr))
        abrir.assert_not_called()
        self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'accion':'reanudar'})
        self.assertIn('siguiente',controlar_sesion('siguiente',correr))
        self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'accion':'siguiente'})
        correr.return_value=types.SimpleNamespace(stdout='{"ok":false}',returncode=0)
        self.assertNotIn('Reanudé',controlar_spotify('',abrir=abrir,correr=correr))
        abrir.assert_not_called()

    def test_modelo_no_inventa_cancion_actual_y_limpia_historia(self):
        inventada='En ese caso, la canción de Shibuya sigue reproduciéndose en segundo plano mientras hablamos. ¿Quieres seguir charlando?'
        self.assertNotIn('Shibuya',core.respuesta_conversacion(inventada))
        self.assertIn('charlando',core.respuesta_conversacion(inventada))
        recomendacion='Podrías escuchar una canción sobre Shibuya.'
        self.assertEqual(core.respuesta_conversacion(recomendacion),recomendacion)
        ia=core.IA();ia.historia=[{'role':'assistant','content':inventada}]
        r=io.BytesIO(json.dumps({'message':{'content':'Sigamos hablando.'}}).encode())
        with patch.object(core.urllib.request,'urlopen',return_value=r) as red:
            ia.conversar('Hablemos','local:test')
        enviado=json.loads(red.call_args.args[0].data)
        self.assertNotIn('Shibuya',enviado['messages'][1]['content'])

    def test_playlist_privada_vinculada_no_se_busca_publicamente(self):
        import playlists
        uri='spotify:playlist:1234567890123456789012'
        with tempfile.TemporaryDirectory() as d:
            carpeta=Path(d)
            playlists.vincular('Mi lista privada','https://open.spotify.com/playlist/1234567890123456789012?si=ejemplo',carpeta)
            self.assertEqual(playlists.cargar(carpeta)['mi lista privada'],uri)
            abrir=Mock();correr=Mock(return_value=types.SimpleNamespace(stdout='{"ok":true}',returncode=0))
            respuesta=playlists.reproducir_playlist('Mi Lista Privada',carpeta,abrir,correr)
            abrir.assert_called_once_with(uri)
            self.assertIn('Activé',respuesta)
            self.assertEqual(json.loads(correr.call_args.kwargs['input'])['consulta'],'Mi Lista Privada')
            with self.assertRaises(ValueError):playlists.vincular('mal','https://otro.com/playlist/1234567890123456789012',carpeta)

    def test_icono_multiresolucion_incluido_en_paquete(self):
        from PIL import Image
        with Image.open(RAIZ/'assets/capri.ico') as icon:
            self.assertTrue({(16,16),(32,32),(256,256)}.issubset(icon.ico.sizes()))
        import empaquetar
        self.assertIn('capri.ico',empaquetar.ARCHIVOS)

    def test_busquedas_naturales_llegan_al_ejecutor(self):
        for frase in ['busca memes de cyberpunk','busque memes de cyberpunk',
                      'que busque memes de cyberpunk','¿Puedes buscarme memes de cyberpunk?',
                      'Capri, búscame memes de cyberpunk','Me gustaría que me busques memes de cyberpunk',
                      'haz una búsqueda de memes de cyberpunk']:
            with self.subTest(frase=frase):
                self.assertEqual(interpretar(frase),Orden('buscar','memes de cyberpunk'))
        self.assertIsNone(interpretar('No busques memes de cyberpunk'))
        self.assertIsNone(interpretar('Explícame qué significa busca memes'))

    def test_spotify_y_carpetas(self):
        self.assertEqual(interpretar('reproduce I Really Want to Stay at Your House en Spotify'),
                         Orden('spotify','I Really Want to Stay at Your House'))
        self.assertEqual(interpretar('pon música de Cyberpunk en Spotify'),Orden('spotify','Cyberpunk'))
        self.assertEqual(interpretar('reproduce una canción en Spotify'),Orden('spotify',''))
        self.assertEqual(interpretar('busca Never Fade Away en Spotify'),Orden('spotify_buscar','Never Fade Away'))
        self.assertEqual(interpretar('pausa Spotify'),Orden('spotify_pausa'))
        self.assertEqual(interpretar('abre mis archivos'),Orden('abrir','explorador de archivos'))
        self.assertEqual(interpretar('abre la carpeta de descargas'),Orden('carpeta','Downloads'))
        self.assertEqual(interpretar('abre documentos'),Orden('carpeta','Documents'))

    def test_spotify_datos_aislados_y_resultados_comprobados(self):
        from escritorio import controlar_spotify
        abrir=Mock();correr=Mock(return_value=types.SimpleNamespace(stdout='{"ok":true}',returncode=0))
        consulta='Cyberpunk; $(calc) `test` "song"'
        respuesta=controlar_spotify(consulta,abrir=abrir,correr=correr)
        self.assertIn('Activé',respuesta)
        args=correr.call_args
        self.assertNotIn(consulta,' '.join(args.args[0]))
        self.assertEqual(json.loads(args.kwargs['input'])['consulta'],consulta)
        self.assertTrue(abrir.call_args.args[0].startswith('spotify:search:'))
        correr.return_value=types.SimpleNamespace(stdout='{"ok":false}',returncode=0)
        self.assertIn('no pude confirmar',controlar_spotify('Cyberpunk',abrir=abrir,correr=correr))
        correr.reset_mock()
        self.assertIn('búsqueda',controlar_spotify('Cyberpunk',accion='buscar',abrir=abrir,correr=correr))
        correr.assert_not_called()

    def test_activacion_nombre_completo_y_orden_en_misma_frase(self):
        from activacion import quitar_nombre
        self.assertEqual(quitar_nombre('Capri, busca memes'),'busca memes')
        self.assertEqual(quitar_nombre('Ey Capri abre Spotify'),'abre Spotify')
        self.assertEqual(quitar_nombre('Capri.'),'')
        for texto in ['capricho','esto es un capricho','dile Capri que venga','Spotify']:
            self.assertIsNone(quitar_nombre(texto))

    def test_audio_suave_gana_nivel_sin_recorte_ni_amplificar_silencio(self):
        import array
        from reconocimiento import amplificar_bajo,energia,umbral_voz
        suave=array.array('h',[60,-60]*1600).tobytes()
        fuerte=amplificar_bajo(suave)
        self.assertGreater(energia(fuerte),energia(suave))
        self.assertGreater(energia(suave),umbral_voz(.001))
        self.assertLess(energia(suave),.0025)
        self.assertEqual(amplificar_bajo(bytes(6400)),bytes(6400))
        ruido=array.array('h',[10,-10]*1600).tobytes()
        self.assertEqual(amplificar_bajo(ruido),ruido)
        picos=array.array('h',[60]*3199+[32767]).tobytes()
        self.assertEqual(amplificar_bajo(picos),picos)
        self.assertLess(energia(suave),umbral_voz(.004))

    def test_detector_entrega_voz_suave_amplificada_y_conserva_audio_original(self):
        import activacion,voz,array
        from contextlib import contextmanager
        suave=array.array('h',[60,-60]*1600).tobytes()
        class Reconocedor:
            def __init__(self):self.i=0
            def AcceptWaveform(self,bloque):
                self.i+=1
                if self.i==1:
                    self.activado=max(array.array('h',bloque))>=150
                    return self.activado
                return False
            def Result(self):return '{"text":"capri busca memes"}'
            def PartialResult(self):return '{"partial":""}'
            def FinalResult(self):return '{"text":""}'
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            recibir(suave,3200,None,None)
            for _ in range(7):recibir(bytes(6400),3200,None,None)
            yield 16000
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        vosk=types.SimpleNamespace(Model=Mock(),SetLogLevel=lambda x:None,KaldiRecognizer=lambda *a:Reconocedor())
        micro=types.SimpleNamespace(modelo=object(),carpeta=Path('.'),whisper=None)
        with patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',return_value='Capri busca memes') as convertir:
            self.assertEqual(activacion.esperar(micro,threading.Event(),Mock()),'busca memes')
            self.assertTrue(convertir.call_args.args[1].startswith(suave))

    def test_detector_recoge_orden_y_reconoce_solo_en_memoria(self):
        import activacion,voz,array
        from contextlib import contextmanager
        modelo=types.SimpleNamespace()
        class Reconocedor:
            def __init__(self):self.bloques=0
            def AcceptWaveform(self,bloque):
                self.bloques+=1;return self.bloques==1
            def Result(self):return '{"text":"capri busca memes de cyberpunk"}'
            def PartialResult(self):return '{"partial":""}'
            def FinalResult(self):return '{"text":""}'
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            recibir(array.array('h',[1200]*3200).tobytes(),3200,None,None)
            for _ in range(7):recibir(bytes(6400),3200,None,None)
            yield 16000
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        vosk=types.SimpleNamespace(Model=Mock(),SetLogLevel=lambda x:None,KaldiRecognizer=lambda *a:Reconocedor())
        micro=types.SimpleNamespace(modelo=modelo,carpeta=Path('.'),whisper=None)
        detectada=Mock()
        with patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',return_value='Capri, busca memes de Cyberpunk') as transcribir:
            texto=activacion.esperar(micro,threading.Event(),detectada,{'indice':23})
        self.assertEqual(texto,'busca memes de Cyberpunk')
        detectada.assert_called_once()
        self.assertIsInstance(transcribir.call_args.args[1],bytes)

    def test_nombre_seguido_de_orden_detecta_nombre_aunque_transcriptor_lo_omita(self):
        import activacion,voz,array
        from contextlib import contextmanager
        bloques=[array.array('h',[1200]*3200).tobytes()]*2+[bytes(6400)]*7
        class Libre:
            def __init__(self):self.i=0
            def AcceptWaveform(self,audio):self.i+=1;return self.i==2
            def Result(self):return '{"text":"abre spotify"}'
            def PartialResult(self):return '{"partial":"abre"}' if self.i==1 else '{"partial":""}'
            def FinalResult(self):return '{"text":""}'
        detector=Mock()
        detector.AcceptWaveform.return_value=False
        detector.PartialResult.return_value='{"partial":"capri [unk]"}'
        def crear(*args):
            if len(args)==3:
                self.assertIn('[unk]',json.loads(args[2]))
                return detector
            return Libre()
        aperturas=[]
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            aperturas.append(indice)
            for bloque in bloques:recibir(bloque,3200,None,None)
            yield 16000
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        vosk=types.SimpleNamespace(Model=Mock(),SetLogLevel=lambda x:None,KaldiRecognizer=crear)
        with patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',return_value='Capri abre Spotify') as convertir:
            micro=types.SimpleNamespace(modelo=object(),carpeta=Path('.'),whisper=None)
            self.assertEqual(activacion.esperar(micro,threading.Event(),Mock()),'abre Spotify')
            self.assertTrue(convertir.call_args.args[1].startswith(b''.join(bloques[:2])))
            self.assertEqual(aperturas,[23])
            self.assertEqual(activacion.esperar(micro,threading.Event(),Mock(),motor='rapido'),'abre spotify')

    def test_nombre_y_orden_en_varios_segmentos_no_pierden_el_principio(self):
        import activacion,voz,array
        from contextlib import contextmanager
        bloques=[array.array('h',[1200]*3200).tobytes(),bytes(6400),bytes(6400)]
        bloques += [array.array('h',[valor]*3200).tobytes() for valor in (1300,1400,1500,1600)]
        bloques += [bytes(6400)]*7
        class Reconocedor:
            def __init__(self):self.i=-1
            def AcceptWaveform(self,bloque):self.i+=1;return self.i in (0,4,6)
            def Result(self):return json.dumps({'text':{0:'capri',4:'busca memes',6:'en opera gx'}[self.i]})
            def PartialResult(self):return json.dumps({'partial':'busca' if self.i==3 else ''})
            def FinalResult(self):return '{"text":""}'
        abierto=False;aperturas=0
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            nonlocal abierto,aperturas
            abierto=True;aperturas+=1
            for bloque in bloques:recibir(bloque,3200,None,None)
            try:yield 16000
            finally:abierto=False
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        vosk=types.SimpleNamespace(Model=Mock(),SetLogLevel=lambda x:None,KaldiRecognizer=lambda *a:Reconocedor())
        detectada=Mock()
        def transcribir(micro,pcm,tasa,idioma):
            self.assertFalse(abierto)
            self.assertTrue(pcm.startswith(b''.join(bloques[:7])), 'Falta el comienzo del audio de la orden')
            return 'Capri, busca memes en Opera GX'
        with patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',side_effect=transcribir) as convertir:
            micro=types.SimpleNamespace(modelo=object(),carpeta=Path('.'),whisper=None)
            self.assertEqual(activacion.esperar(micro,threading.Event(),detectada), 'busca memes en Opera GX')
            convertir.assert_called_once()
            self.assertEqual(aperturas,1)
            self.assertEqual(activacion.esperar(micro,threading.Event(),Mock(),motor='rapido'),'busca memes en opera gx')
        detectada.assert_called_once()

    def test_solo_nombre_no_reabre_microfono_al_agotar_espera(self):
        import app as modulo
        with patch.object(modulo.Voz,'parar'):
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.activacion_ticket=8
                capri.eventos.put(('nombre_detectado',8));capri.poll()
                with patch.object(capri,'hablar') as hablar,patch.object(capri,'enviar') as enviar:
                    capri.eventos.put(('activacion_resultado',(8,'',None)));capri.poll()
                    hablar.assert_not_called();enviar.assert_not_called()
                self.assertFalse(capri.escuchando)
            finally:capri.cerrar()

    def test_activacion_cancela_respuesta_y_descarta_eventos_viejos(self):
        import app as modulo
        with patch.object(modulo.Voz,'parar'):
            capri=modulo.Capri(hotkeys=False);capri.root.withdraw()
            try:
                capri.ocupada=True;pendiente=capri.respuesta_stop
                capri.activacion_ticket=10
                capri.eventos.put(('nombre_detectado',10));capri.poll()
                self.assertTrue(pendiente.is_set());self.assertTrue(capri.escuchando)
                with patch.object(capri,'enviar') as enviar:
                    capri.eventos.put(('activacion_resultado',(10,'busca memes',None)));capri.poll()
                    enviar.assert_called_once_with('busca memes')
                    enviar.reset_mock()
                    capri.parar()
                    capri.eventos.put(('activacion_resultado',(10,'busca otro',None)));capri.poll()
                    enviar.assert_not_called()
                self.assertFalse(capri.escuchando)
            finally:capri.cerrar()

class Instalador(unittest.TestCase):
    def test_distribucion_generica_sin_datos_del_desarrollador(self):
        import base64,runpy
        boot=runpy.run_path(str(RAIZ/'dist/Abrir Capri.pyw'),run_name='capri_inspeccion')
        self.assertEqual(boot['DESTINO'].name,'Capri')
        self.assertIn('de quien utiliza la aplicación',core.PERSONALIDAD)
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(boot['PAYLOAD']))) as z:
            self.assertIn('app.py',z.namelist())
            for nombre in z.namelist():
                if nombre.endswith(('.py','.md','.txt')):
                    contenido=z.read(nombre).decode('utf-8').casefold()
                    self.assertNotIn('c:\\users\\',contenido,nombre)
            for nombre in ('ajustes.json','playlists.json','CONTINUIDAD.md'):
                self.assertNotIn(nombre,z.namelist())
        self.assertTrue((RAIZ/'dist/Capri.zip').is_file())

    def test_paquete_integridad_y_arranque_sin_red_ni_instalar(self):
        import base64,hashlib,runpy,queue
        from recursos import ARTE,MODELO_NOMBRE
        globals_boot=runpy.run_path(str(RAIZ/'dist/Abrir Capri.pyw'),run_name='capri_prueba')
        paquete=base64.b64decode(globals_boot['PAYLOAD'])
        self.assertEqual(hashlib.sha256(paquete).hexdigest(),globals_boot['HASH'])
        with tempfile.TemporaryDirectory() as d:
            destino=Path(d)/'Capri'
            destino.mkdir()
            with zipfile.ZipFile(io.BytesIO(paquete)) as z:
                requisitos=z.read('requirements.txt')
                self.assertIn('app.py',z.namelist())
            (destino/'dependencias-listas.txt').write_text(hashlib.sha256(requisitos).hexdigest())
            python=destino/'.venv/Scripts/python.exe';python.parent.mkdir(parents=True);python.write_text('prueba')
            (destino/'assets').mkdir()
            for nombre,url in ARTE:(destino/'assets'/nombre).write_bytes(b'\x89PNG\r\n\x1a\n'+bytes(150))
            modelo=destino/'modelos'/MODELO_NOMBRE/'am/final.mdl';modelo.parent.mkdir(parents=True);modelo.write_text('prueba')
            from reconocimiento import ARCHIVOS
            carpeta_whisper=destino/'modelos/whisper-base';carpeta_whisper.mkdir()
            for nombre in ARCHIVOS:(carpeta_whisper/nombre).write_bytes(bytes(150))
            clase=globals_boot['Preparar']
            entorno=clase.trabajar.__globals__
            anterior=entorno['DESTINO'];entorno['DESTINO']=destino
            obj=clase.__new__(clase);obj.q=queue.Queue();obj.cancelar=threading.Event();obj.proceso=None;obj.comando=Mock()
            try:
                with patch('subprocess.Popen',return_value=types.SimpleNamespace(poll=lambda:None)) as spawn,patch('time.sleep'),patch('recursos.descargar') as red:
                    obj.trabajar()
                    red.assert_not_called()
                    eventos=list(obj.q.queue)
                    self.assertEqual(eventos[-1],('fin',None),eventos)
                    self.assertEqual(spawn.call_args.args[0][1],str(destino/'app.py'))
                    self.assertTrue((destino/'Abrir Capri.vbs').is_file())
                    self.assertEqual(obj.comando.call_args.args[0][0],'powershell.exe')
            finally:entorno['DESTINO']=anterior

if __name__=='__main__':unittest.main(verbosity=2)
