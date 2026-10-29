import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import interpretar,Orden,ejecutar
from intenciones import Interprete
from control_pc import ControlPC
import aplicaciones
import navegador

class AppsWeb(unittest.TestCase):
    def test_sitios_busquedas_y_videos_son_destinos_distintos(self):
        casos={'entra a youtube':Orden('pestana','https://www.youtube.com/'),
               'abre netflix':Orden('pestana','https://www.netflix.com/'),
               've a youtube.cl':Orden('pestana','https://youtube.cl'),
               'métete a youtube':Orden('pestana','https://www.youtube.com/'),
               'puedes meterte a youtube':Orden('pestana','https://www.youtube.com/'),
               'busca netflix':Orden('pestana','https://www.netflix.com/'),
               'busca high forever en youtube':Orden('youtube_buscar','high forever'),
               'pon un video de cyberpunk en youtube':Orden('youtube_buscar','cyberpunk'),
               'siguiente video':Orden('youtube_siguiente'),
               'pausa el video':Orden('youtube_pausa'),
               'pon high forever en spotify':Orden('spotify','high forever')}
        for t,esperada in casos.items():
            with self.subTest(t=t):self.assertEqual(interpretar(t),esperada)

    def test_lol_y_cierre_directos_respetan_permiso_y_negaciones(self):
        i=Interprete()
        self.assertEqual(i.ajustar_orden('abre lol',interpretar('abre lol'),True),Orden('programa_abrir','lol'))
        self.assertEqual(i.ajustar_orden('cierra spotify',interpretar('cierra spotify'),True),Orden('programa_cerrar','spotify'))
        self.assertEqual(i.ajustar_orden('abre lol',interpretar('abre lol'),False).tipo,'desconocida')
        self.assertIsNone(i.ajustar_orden('no cierres spotify',None,True))

    def test_contexto_youtube_no_controla_spotify_y_cambia_de_tema(self):
        i=Interprete();i.registrar('entra a youtube',Orden('pestana','https://www.youtube.com/'),'Solicitado')
        self.assertEqual(i.ajustar_orden('siguiente',interpretar('siguiente')),Orden('youtube_siguiente'))
        i.registrar('pon musica',Orden('spotify'),'Solicitado')
        self.assertEqual(i.ajustar_orden('siguiente',interpretar('siguiente')),Orden('spotify_siguiente'))
        c=i.contexto()
        self.assertIsNone(i.validar({'accion':'pestana','valor':'https://evil.test'},'abre netflix',c).orden)
        self.assertEqual(i.validar({'accion':'pestana','valor':'https://www.netflix.com/'},'abre netflix',c).orden.tipo,'pestana')

    def test_catalogo_alias_y_acceso_directo_conservan_argumentos(self):
        apps=[{'nombre':'League of Legends','tipo':'enlace','destino':'C:/Menu/League.lnk'}]
        with patch.object(aplicaciones,'catalogo',return_value=apps),patch.object(aplicaciones.os,'startfile',create=True) as abrir,patch.object(aplicaciones.subprocess,'Popen') as spawn:
            self.assertIn('League of Legends',aplicaciones.abrir('lol'))
            abrir.assert_called_once_with(apps[0]['destino']);spawn.assert_not_called()

    def test_cierre_proceso_requiere_confirmacion_una_vez_y_revocacion_cancela(self):
        procesos=[{'id':123,'nombre':'Spotify','inicio':'123456'}];activo=[True]
        pc=ControlPC(lambda:activo[0])
        with patch.object(aplicaciones,'procesos',return_value=procesos),patch.object(aplicaciones,'cerrar',return_value='Cerré Spotify') as cerrar:
            self.assertIn('Confirmas',pc.ejecutar('programa_cerrar','spotify'));cerrar.assert_not_called()
            pc.confirmar('sí, confirmo');cerrar.assert_called_once_with(procesos)
            pc.confirmar('sí');self.assertEqual(cerrar.call_count,1)
            pc.ejecutar('programa_cerrar','spotify');activo[0]=False;pc.confirmar('sí')
            self.assertEqual(cerrar.call_count,1)

    def test_procesos_no_dependen_del_titulo_ni_coincidencias_parciales(self):
        lista=[{'id':1,'nombre':'Spotify','inicio':'1'},{'id':2,'nombre':'SpotifyHelperFake','inicio':'2'}]
        with patch.object(aplicaciones,'powershell',return_value=lista):self.assertEqual(aplicaciones.procesos('spotify'),lista[:1])

    def test_identidad_proceso_reutilizado_impide_cierre_en_backend(self):
        import os,base64,subprocess
        if os.name!='nt':self.skipTest('Backend PowerShell de Windows')
        # Sustituir cmdlets por objetos en memoria: nunca cerrar procesos reales.
        stub=r'''
function Get-Process {param($Id,$ErrorAction)
 $p=[pscustomobject]@{Id=123;ProcessName='Spotify';StartTime=[datetime]'2026-01-01T00:00:00Z'}
 $p|Add-Member -MemberType ScriptMethod -Name WaitForExit -Value {param($ms) return $true}
 return $p
}
function Stop-Process {param($InputObject,$ErrorAction) throw 'NO DEBE CERRAR UN PID REUTILIZADO'}
'''
        script=stub+aplicaciones.PROCESOS
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],
                         input=json.dumps({'cerrar':True,'procesos':[{'id':123,'nombre':'Spotify','inicio':'1'}]}),capture_output=True,text=True,errors='replace',timeout=10)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('vuelve a solicitarlo',r.stderr)
        self.assertNotIn('NO DEBE CERRAR',r.stderr)

    def test_spotify_texto_con_espacios_sin_uri_ni_lanzamiento(self):
        from escritorio import controlar_spotify
        abrir=Mock();correr=Mock(return_value=types.SimpleNamespace(stdout=json.dumps({'ok':True}),returncode=0))
        controlar_spotify('high forever',abrir=abrir,correr=correr)
        self.assertEqual(json.loads(correr.call_args.kwargs['input'])['consulta'],'high forever');abrir.assert_not_called()
        correr.return_value=types.SimpleNamespace(stdout='{}',returncode=0)
        self.assertIn('No abrí su ventana',controlar_spotify('high forever',abrir=abrir,correr=correr,proteger=lambda:True));abrir.assert_not_called()

    def test_respaldo_recupera_busqueda_y_reproduccion_fuera_del_juego(self):
        from escritorio import controlar_spotify
        from urllib.parse import unquote
        consulta='High Forever + remix'
        correr=Mock(side_effect=[types.SimpleNamespace(stdout='{}',returncode=0),
                                types.SimpleNamespace(stdout=json.dumps({'ok':True}),returncode=0)])
        abrir=Mock()
        respuesta=controlar_spotify(consulta,abrir=abrir,correr=correr,proteger=lambda:False)
        self.assertIn('Activé',respuesta)
        uri=abrir.call_args.args[0]
        self.assertEqual(unquote(uri.removeprefix('spotify:search:')),consulta)
        self.assertIn('High%20Forever%20%2B%20remix',uri)
        self.assertTrue(json.loads(correr.call_args.kwargs['input'])['navegada'])
        self.assertEqual(json.loads(correr.call_args.kwargs['input'])['consulta'],consulta)

    def test_respaldo_no_confirma_reproduccion_si_solo_abrio_la_busqueda(self):
        from escritorio import controlar_spotify
        correr=Mock(return_value=types.SimpleNamespace(stdout='{}',returncode=0));abrir=Mock()
        r=controlar_spotify('High Forever',abrir=abrir,correr=correr,proteger=lambda:False)
        abrir.assert_called_once();self.assertIn('no pude confirmar',r);self.assertNotIn('Activé',r)

    def test_juego_y_pantalla_completa_protegen_foco_y_errores_bloquean_respaldo(self):
        from escritorio import foco_protegido,controlar_spotify
        self.assertTrue(foco_protegido('League of Legends.exe',(100,100,900,700),(0,0,1920,1080)))
        self.assertTrue(foco_protegido('otro.exe',(-1920,0,0,1080),(-1920,0,0,1080)))
        self.assertFalse(foco_protegido('opera.exe',(0,0,1920,1040),(0,0,1920,1080)))
        self.assertFalse(foco_protegido('Spotify.exe',(0,0,1920,1080),(0,0,1920,1080)))
        correr=Mock(return_value=types.SimpleNamespace(stdout='{}',returncode=0));abrir=Mock()
        controlar_spotify('High Forever',abrir=abrir,correr=correr,proteger=Mock(side_effect=OSError('No disponible')))
        abrir.assert_not_called();self.assertEqual(correr.call_count,1)

    def test_video_solicita_control_dirigido_y_error_no_inventa_exito(self):
        correr=Mock(return_value=types.SimpleNamespace(stdout=json.dumps({'ok':False,'error':'Control no disponible'}),returncode=0))
        with patch('core.abrir_opera') as abrir:
            r=navegador.ejecutar_youtube(Orden('youtube_video','high forever'),correr=correr)
            self.assertEqual(r,'Control no disponible')
            from urllib.parse import parse_qs,urlsplit
            self.assertEqual(parse_qs(urlsplit(abrir.call_args.kwargs['pagina']).query)['search_query'],['high forever'])
            self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'accion':'video'})
