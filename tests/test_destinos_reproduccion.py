import base64
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import interpretar,Orden,ejecutar
from intenciones import Interprete
import navegador
import playlists


class DestinosReproduccion(unittest.TestCase):
    def test_destino_explicito_youtube_busca_y_spotify_reproduce(self):
        for destino,tipo in [('Spotify','spotify'),('YouTube','youtube_buscar')]:
            for titulo in ['High Forever','"High Forever"','la canción High Forever']:
                with self.subTest(destino=destino,titulo=titulo):
                    orden=interpretar(f'reproduce {titulo} en {destino}')
                    self.assertEqual(orden.tipo,tipo)
                    self.assertNotIn(destino,orden.valor)
        i=Interprete();i.registrar('busca videos',Orden('youtube_buscar','cyberpunk'),'Busqué')
        self.assertEqual(i.ajustar_orden('reproduce High Forever en Spotify',interpretar('reproduce High Forever en Spotify')),Orden('spotify','High Forever'))

    def test_modelo_no_puede_cambiar_el_destino_o_el_alcance(self):
        i=Interprete()
        for texto in ('reproduce High Forever en Spotify','reproduce High Forever en YouTube','reproduce High Forever en mi playlist Capri','reproduce High Forever en mi playlist'):
            correcta=interpretar(texto)
            for accion in ('spotify','youtube_video','buscar','charla'):
                decision=i.validar({'accion':accion,'valor':'inventado'},texto,i.contexto())
                self.assertEqual(decision.orden,correcta)

    def test_seleccionar_resultado_no_vuelve_a_buscar_ni_toca_spotify(self):
        for frase,indice in [('reproduce el primer video','1'),('pon el segundo resultado','2'),('reproduce el video número 3','3')]:
            self.assertEqual(interpretar(frase),Orden('youtube_resultado',indice))
        i=Interprete();i.registrar('busca cyberpunk en youtube',Orden('youtube_buscar','cyberpunk'),'Busqué')
        self.assertEqual(i.ajustar_orden('reproduce el primero',interpretar('reproduce el primero')),Orden('youtube_resultado','1'))
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout='{"ok":true}'))
        with patch('core.abrir_opera') as abrir:
            mensaje=navegador.ejecutar_youtube(Orden('youtube_resultado','2'),correr=correr)
            abrir.assert_not_called();self.assertIn('resultado 2',mensaje)
        self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'accion':'resultado','indice':2})
        with self.assertRaises(ValueError):navegador.ejecutar_youtube(Orden('youtube_resultado','0'),correr=correr)

    def test_busqueda_youtube_no_invoca_reproduccion_automatica(self):
        correr=Mock()
        with patch('core.abrir_opera') as abrir:
            navegador.ejecutar_youtube(interpretar('reproduce High Forever en youtube'),correr=correr)
            self.assertIn('search_query=High+Forever',abrir.call_args.kwargs['pagina'])
            correr.assert_not_called()

    def test_playlist_sin_nombre_pregunta_y_no_busca_fuera(self):
        orden=interpretar('reproduce "High Forever" en mi playlist en Spotify')
        self.assertEqual(orden.tipo,'spotify_playlist_pendiente')
        self.assertEqual(json.loads(orden.valor),{'cancion':'High Forever','nombre':''})
        with patch('escritorio.controlar_spotify') as global_spotify,patch('playlists.subprocess.run') as proceso:
            respuesta=ejecutar(orden)
            self.assertIn('Cómo se llama',respuesta);global_spotify.assert_not_called();proceso.assert_not_called()
        i=Interprete();i.registrar('reproduce High Forever en mi playlist',orden,respuesta)
        resuelta=i.ajustar_orden('Capri',interpretar('Capri'))
        self.assertEqual(json.loads(resuelta.valor),{'cancion':'High Forever','nombre':'Capri'})

    def test_mi_playlist_reutiliza_lista_explicita_y_esta_cancion_consulta_sesion(self):
        i=Interprete();i.registrar('pon mi playlist Capri',Orden('spotify_playlist','Capri'),'Reproduciendo')
        frase='reproduce esta canción en mi playlist'
        orden=i.ajustar_orden(frase,interpretar(frase))
        self.assertEqual(orden.tipo,'spotify_playlist_cancion')
        self.assertEqual(json.loads(orden.valor),{'cancion':'','nombre':'Capri'})
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout='{"ok":true}'))
        with patch('multimedia.sesion_spotify',return_value={'ok':True,'titulo':'High Forever'}) as sesion:
            playlists.reproducir_cancion_playlist('', 'Capri',correr=correr)
            sesion.assert_called_once()
        self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'cancion':'High Forever','nombre':'Capri'})

    def test_aclaracion_natural_extrae_nombre_y_conserva_cancion_pendiente(self):
        peticion='Reproduce High Forever en mi playlist.';pendiente=interpretar(peticion)
        for respuesta in ('de la playlist Capri.','en mi playlist Capri','la playlist Capri','playlist llamada Capri',
                          'de la lista de reproducción Capri','mi playlist se llama Capri','se llama Capri','es Capri','la que se llama Capri','Capri'):
            with self.subTest(respuesta=respuesta):
                i=Interprete();i.registrar(peticion,pendiente,ejecutar(pendiente))
                orden=i.ajustar_orden(respuesta,interpretar(respuesta))
                self.assertEqual(orden.tipo,'spotify_playlist_cancion')
                self.assertEqual(json.loads(orden.valor),{'cancion':'High Forever','nombre':'Capri'})
        # Una nueva orden explícita no es el nombre de la playlist pendiente.
        self.assertEqual(i.ajustar_orden('abre Spotify',interpretar('abre Spotify')),Orden('abrir','spotify'))

    def test_cita_playlist_dentro_del_titulo_no_cambia_el_alcance(self):
        orden=interpretar('reproduce "Una canción en mi playlist Capri" en Spotify')
        self.assertEqual(orden.tipo,'spotify')
        self.assertEqual(orden.valor,'Una canción en mi playlist Capri')

    def test_script_youtube_es_sintacticamente_valido_sin_operar_ventanas(self):
        parser="$t=$null;$e=$null;[void][System.Management.Automation.Language.Parser]::ParseInput([Console]::In.ReadToEnd(),[ref]$t,[ref]$e);if($e.Count){$e|ForEach-Object {$_.Message};exit 1}"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(parser.encode('utf-16le')).decode()],input=navegador.YOUTUBE_UI,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
