import base64
import json
from pathlib import Path
import os
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import interpretar,Orden
from intenciones import Interprete
import volumen_apps as volumen
import navegador
import multimedia

class ControlWebAudio(unittest.TestCase):
    def test_sitios_exactos_y_alias_nunca_son_programas_y_google_explicitamente_busca(self):
        for t in ('Capri, busca Crunchyroll','abre crunchyroll','busca crunchy roll','entra a crunchyroll.com'):
            with self.subTest(t=t):self.assertEqual(interpretar(t).tipo,'pestana')
        self.assertEqual(interpretar('busca crunchyroll').valor,'https://www.crunchyroll.com/')
        for t in ('busca en google crunchyroll','busca opiniones de crunchyroll','busca algo desconocido'):
            with self.subTest(t=t):self.assertEqual(interpretar(t).tipo,'buscar')
        i=Interprete()
        for t in ('busca crunchyroll','busca opiniones de crunchyroll'):
            d=i.validar({'accion':'programa_abrir','valor':'crunchyroll'},t,i.contexto(),True)
            self.assertEqual(d.orden,interpretar(t))
        self.assertIsNone(i.validar({'accion':'programa_abrir','valor':'crunchyroll'},'no abras crunchyroll',i.contexto(),True).orden)

    def test_volumen_natural_absoluto_relativo_contextual_y_negacion(self):
        casos={'sube el volumen de spotify':'subir:10','súbele el volumen al Spotify':'subir:10',
               'puedes subirle el volumen a Spotify':'subir:10','quiero que le subas el volumen a Spotify':'subir:10',
               'baja el volumen de spotify un veinte por ciento':'bajar:20',
               'pon el volumen de spotify al cincuenta por ciento':'fijar:50',
               'silencia spotify':'silenciar','quita el silencio de spotify':'activar'}
        for t,v in casos.items():
            with self.subTest(t=t):self.assertEqual(interpretar(t),Orden('spotify_volumen',v))
        self.assertIsNone(volumen.interpretar_volumen('no subas el volumen de spotify'))
        self.assertIsNone(volumen.interpretar_volumen('pon música de los 80 en Spotify'))
        i=Interprete();i.registrar('pon musica',Orden('spotify'),'Reproduciendo')
        self.assertEqual(i.ajustar_orden('baja el volumen',interpretar('baja el volumen')),Orden('spotify_volumen','bajar:10'))
        self.assertIsNone(i.validar({'accion':'spotify_volumen','valor':'fijar:100'},'baja el volumen de spotify',i.contexto()).orden)

    def test_volumen_interno_usa_slider_y_restaurar_recuerda_el_nivel(self):
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'volumen':0,'anterior':42})))
        with patch.object(volumen,'_ultimo_volumen',50):
            self.assertIn('dentro de Spotify: 0%',volumen.controlar_volumen('silenciar',correr))
            correr.return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'volumen':42,'anterior':0}))
            self.assertIn('42%',volumen.controlar_volumen('activar',correr))
            self.assertEqual(json.loads(correr.call_args.kwargs['input'])['restaurar'],42)
        codigo=base64.b64decode(correr.call_args.args[0][-1]).decode('utf-16le')
        self.assertIn('RangeValuePattern',codigo)
        self.assertNotIn('SetMasterVolume',codigo)
        self.assertNotIn('SetForegroundWindow',codigo)

    def test_no_confirma_si_slider_no_disponible_y_rechaza_nivel_invalido(self):
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':False})))
        self.assertIn('no confirmó',volumen.controlar_volumen('subir:10',correr))
        correr.return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'volumen':200,'anterior':40}))
        self.assertIn('no confirmó',volumen.controlar_volumen('subir:10',correr))
        with self.assertRaises(ValueError):volumen.controlar_volumen('fijar:101',correr)

    def test_youtube_volumen_directo_y_contextual_no_se_cruza_con_spotify(self):
        casos={'sube el volumen de youtube':'subir:10','baja el volumen del vídeo':'bajar:10',
               'pon el volumen de youtube al cuarenta por ciento':'fijar:40','silencia el video':'silenciar',
               'sube el sonido de youtube':'subir:10'}
        for t,v in casos.items():
            with self.subTest(t=t):self.assertEqual(interpretar(t),Orden('youtube_volumen',v))
        i=Interprete();i.registrar('abre youtube',Orden('abrir','youtube'),'Abierto')
        self.assertEqual(i.ajustar_orden('sube el volumen',interpretar('sube el volumen')),Orden('youtube_volumen','subir:10'))
        self.assertIsNone(i.validar({'accion':'spotify_volumen','valor':'subir:10'},'sube el volumen de youtube',i.contexto()).orden)
        with patch.object(volumen,'controlar_volumen',return_value='50%') as mover:
            from core import ejecutar
            ejecutar(Orden('youtube_volumen','fijar:50'))
            mover.assert_called_once_with('fijar:50',destino='youtube')

    def test_volumen_youtube_restaurar_independiente_de_spotify(self):
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'volumen':0,'anterior':75})))
        with patch.object(volumen,'_ultimo_volumen',30),patch.object(volumen,'_ultimo_youtube',50):
            self.assertIn('YouTube: 0%',volumen.controlar_volumen('silenciar',correr,destino='youtube'))
            correr.return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'volumen':75,'anterior':0}))
            volumen.controlar_volumen('activar',correr,destino='youtube')
            self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'operacion':'activar','restaurar':75,'destino':'youtube'})
            self.assertEqual(volumen._ultimo_volumen,30)

    def test_slider_youtube_solo_documento_y_dominio_correcto(self):
        if os.name!='nt':self.skipTest('Control de Windows')
        funcion='function EsYouTube'+volumen.VOLUMEN_UI.split('function EsYouTube',1)[1].split("\n$nombreApp=",1)[0]
        script=funcion+"\n@((EsYouTube 'https://www.youtube.com/watch?v=abc' 'Vídeo' 'Opera'), (EsYouTube 'https://netflix.com/' 'Vídeo - YouTube' 'YouTube'), (EsYouTube 'https://youtube.com.evil.test/' '' ''), (EsYouTube '' 'Vídeo - YouTube' 'Vídeo - YouTube - Opera'))|ConvertTo-Json -Compress"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),[True,False,False,True])

    def test_calculo_slider_interno_limites_y_porcentajes(self):
        if os.name!='nt':self.skipTest('Control de Windows')
        funcion='function DestinoVolumen'+volumen.VOLUMEN_UI.split('function DestinoVolumen',1)[1].split('\ntry{',1)[0]
        script=funcion+"\n@( (DestinoVolumen 'subir:10' 45 50), (DestinoVolumen 'subir:80' 45 50), (DestinoVolumen 'bajar:80' 45 50), (DestinoVolumen 'fijar:35' 45 50), (DestinoVolumen 'activar' 0 42), (DestinoVolumen 'activar' 60 42))|ConvertTo-Json -Compress"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),[55,100,0,35,42,60])

    def test_youtube_sesion_nativa_no_depende_de_botones_y_no_duplica_accion(self):
        for accion,estado in (('pausa','Paused'),('reanudar','Playing'),('siguiente','Playing')):
            with patch.object(multimedia,'sesion_youtube',return_value={'ok':True,'estado':estado}) as sesion,patch.object(navegador.subprocess,'run') as uia:
                r=navegador.ejecutar_youtube(Orden('youtube_'+accion))
                self.assertIn('YouTube',r);sesion.assert_called_once_with(accion,correr=None);uia.assert_not_called()
        with patch.object(multimedia,'sesion_youtube',return_value={'ok':False,'error':'Sin sesión'}) as sesion,patch.object(navegador.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True}))) as uia:
            self.assertIn('pausar',navegador.ejecutar_youtube(Orden('youtube_pausa')))
            self.assertEqual(uia.call_count,1)

    def test_selector_youtube_rechaza_spotify_netflix_y_titulos_ambiguos(self):
        if os.name!='nt':self.skipTest('Selector nativo de Windows')
        funcion='function CoincideYouTube'+multimedia.MEDIA_PS.split(' function CoincideYouTube',1)[1].split(' $datos=',1)[0]
        script=funcion+"\n$d=[Console]::In.ReadToEnd()|ConvertFrom-Json; @($d|ForEach-Object {CoincideYouTube $_.origen $_.titulo $_.ventanas})|ConvertTo-Json -Compress"
        casos=[{'origen':'OperaSoftware.OperaGX','titulo':'Video prueba','ventanas':['Video prueba - YouTube - Opera']},
               {'origen':'Spotify','titulo':'Video prueba','ventanas':['Video prueba - YouTube - Opera']},
               {'origen':'OperaSoftware.OperaGX','titulo':'Video prueba','ventanas':['Video prueba - Netflix - Opera']},
               {'origen':'OperaSoftware.OperaGX','titulo':'','ventanas':['Video prueba - YouTube - Opera']}]
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],input=json.dumps(casos),text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),[True,False,False,False])
