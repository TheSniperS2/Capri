import array
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import activacion
import voz

class ActivacionEstricta(unittest.TestCase):
    def capturar(self,final,whisper,parcial='',motor='mixto',detector_falso=True,nivel=None,estado=None,ruido=False,lista=None,frio=False):
        detener=threading.Event();actual={'bloque':0};avisos=[];orden=[]
        detectada=Mock(side_effect=lambda:avisos.append(actual['bloque']))
        detectada.bloques=avisos
        class Libre:
            def __init__(self):self.i=0
            def AcceptWaveform(self,bloque):
                self.i+=1
                actual['bloque']=self.i
                if self.i>=10:detener.set()
                return self.i==3
            def Result(self):return json.dumps({'text':final})
            def PartialResult(self):return json.dumps({'partial':parcial if self.i<3 else ''})
            def FinalResult(self):return '{"text":""}'
        falso=Mock()
        falso.AcceptWaveform.return_value=False
        falso.PartialResult.return_value='{"partial":"capri [unk]"}'
        def crear(*args):return falso if len(args)==3 and detector_falso else Libre()
        @contextmanager
        def entrada(indice,datos,recibir,stop,intentos):
            orden.append('entrada')
            for i in range(10):recibir(array.array('h',[1200 if i<3 else (1000 if ruido else 0)]*3200).tobytes(),3200,None,None)
            yield 16000
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        def cargar(*a):
            self.assertEqual(orden,['entrada']);orden.append('modelo');return object()
        vosk=types.SimpleNamespace(Model=Mock(side_effect=cargar),SetLogLevel=lambda x:None,KaldiRecognizer=crear)
        micro=types.SimpleNamespace(modelo=None if frio else object(),carpeta=Path('.'),whisper=None)
        with patch.object(activacion,'DetectorVoz',return_value=types.SimpleNamespace(analizar=lambda datos,tasa:max(array.array('h',datos))>1100 if ruido else bool(any(datos)))),patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',return_value=whisper) as transcribir:
            resultado=activacion.esperar(micro,detener,detectada,motor=motor,nivel=nivel,estado=estado,lista=lista)
        return resultado,detectada,transcribir

    def test_nombre_inventado_por_detector_restringido_no_activa(self):
        resultado,detectada,transcribir=self.capturar('abre spotify','abre Spotify')
        self.assertIsNone(resultado);detectada.assert_not_called();transcribir.assert_not_called()

    def test_hipotesis_parcial_retirada_no_envia_si_whisper_tampoco_confirma_nombre(self):
        resultado,detectada,transcribir=self.capturar('abre spotify','abre Spotify',parcial='capri')
        self.assertIsNone(resultado);detectada.assert_called_once();transcribir.assert_called_once()

    def test_whisper_confirma_nombre_aunque_vosk_corrija_mal_su_parcial(self):
        resultado,_,convertir=self.capturar('capriles abre spotify','Capri abre Spotify',parcial='capri')
        self.assertEqual(resultado,'abre Spotify')
        self.assertEqual(convertir.call_args.args[3],'es')

    def test_confusion_capriles_solo_es_candidata_y_exige_verificacion_whisper(self):
        resultado,_,_=self.capturar('capriles abre spotify','Capri abre Spotify',parcial='capriles')
        self.assertEqual(resultado,'abre Spotify')
        resultado,_,_=self.capturar('capriles abre spotify','Capriles abre Spotify',parcial='capriles')
        self.assertIsNone(resultado)
        resultado,_,convertir=self.capturar('capriles abre spotify','Capri abre Spotify',parcial='capriles',motor='rapido')
        self.assertIsNone(resultado);convertir.assert_not_called()

    def test_aviso_rapido_no_espera_el_final_de_vosk(self):
        resultado,detectada,transcribir=self.capturar('capri abre spotify','Capri abre Spotify',parcial='capri')
        self.assertEqual(resultado,'abre Spotify')
        self.assertEqual(detectada.bloques,[1])
        transcribir.assert_called_once()

    def test_whisper_sin_nombre_no_envia_orden_aunque_vosk_lo_haya_supuesto(self):
        resultado,detectada,transcribir=self.capturar('capri abre spotify','abre Spotify')
        self.assertIsNone(resultado);detectada.assert_called_once();transcribir.assert_called_once()

    def test_nombre_y_orden_confirmados_siguen_funcionando_en_ambos_modos(self):
        for motor,esperado in [('mixto','abre Spotify'),('rapido','abre spotify')]:
            resultado,detectada,transcribir=self.capturar('capri abre spotify','Capri abre Spotify',motor=motor)
            self.assertEqual(resultado,esperado);detectada.assert_called_once()

    def test_nivel_durante_captura_y_estado_al_terminar_antes_de_whisper(self):
        niveles=[];estados=[]
        resultado,_,convertir=self.capturar('capri abre spotify','Capri abre Spotify',
                        parcial='capri',nivel=niveles.append,estado=estados.append)
        self.assertEqual(resultado,'abre Spotify')
        self.assertGreater(max(niveles),0)
        self.assertEqual(niveles[-1],0)
        self.assertEqual(estados,['Preparando activación…','Reconociendo la frase…'])
        convertir.assert_called_once()

    def test_arranque_frio_abre_entrada_antes_del_modelo_y_conserva_primera_orden(self):
        lista=Mock()
        resultado,detectada,convertir=self.capturar('capri abre spotify','Capri abre Spotify',parcial='capri',lista=lista,frio=True)
        self.assertEqual(resultado,'abre Spotify');lista.assert_called_once();detectada.assert_called_once()
        self.assertTrue(convertir.call_args.args[1].startswith(array.array('h',[1200]*3200).tobytes()))

    def test_ruido_no_alarga_captura_si_detector_no_lo_considera_voz(self):
        resultado,_,convertir=self.capturar('capri abre spotify','Capri abre Spotify',ruido=True)
        self.assertEqual(resultado,'abre Spotify')
        convertir.assert_called_once()

    def test_frase_anterior_no_contamina_audio_de_nueva_activacion(self):
        detener=threading.Event();posicion=[0]
        anterior=array.array('h',[800]*3200).tobytes()
        nombre=array.array('h',[1200]*3200).tobytes()
        class Libre:
            def AcceptWaveform(self,bloque):
                posicion[0]+=1
                if posicion[0]>25:detener.set()
                return False
            def PartialResult(self):return json.dumps({'partial':'hola buenas' if posicion[0]<9 else 'capri abre spotify'})
            def FinalResult(self):return json.dumps({'text':'hola buenas' if posicion[0]<9 else 'capri abre spotify'})
        @contextmanager
        def entrada(indice,datos,recibir,stop,intentos):
            for b in [anterior]*2+[bytes(6400)]*6+[nombre]*3+[bytes(6400)]*15:recibir(b,3200,None,None)
            yield 16000
        sd=types.SimpleNamespace(query_devices=lambda *a,**k:{'name':'USB'})
        vosk=types.SimpleNamespace(Model=Mock(),SetLogLevel=lambda x:None,KaldiRecognizer=lambda *a:Libre())
        micro=types.SimpleNamespace(modelo=object(),carpeta=Path('.'))
        with patch.object(activacion,'DetectorVoz',return_value=types.SimpleNamespace(analizar=lambda b,t:bool(any(b)))),patch.dict(sys.modules,{'sounddevice':sd,'vosk':vosk}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada),patch('reconocimiento.disponible',return_value=True),patch('reconocimiento.transcribir',return_value='Capri abre Spotify') as convertir:
            self.assertEqual(activacion.esperar(micro,detener,Mock()),'abre Spotify')
        pcm=convertir.call_args.args[1]
        self.assertNotIn(anterior,pcm)
        self.assertIn(nombre*3,pcm)

if __name__=='__main__':unittest.main()
