import base64
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import types
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import interpretar,Orden,ejecutar
from intenciones import Interprete
from control_pc import ControlPC
from apagado import RendererApagado,SecuenciaApagado,DURACION
from discord_control import interpretar_discord,ejecutar_discord,DISCORD_UI
from voz import Voz,elegir_voz
from test_capri import PruebasTk
import test_companera_control as fixtures


class Apagado(unittest.TestCase):
    def test_confirmacion_activa_animacion_sin_apagar_y_permiso_se_verifica_al_final(self):
        permiso=True;c=ControlPC(lambda:permiso);c.energia_animada=Mock(return_value='animación')
        with patch('control_pc.subprocess.run') as proceso:
            self.assertIn('Confirmas',c.ejecutar('equipo_apagar',''))
            c.energia_animada.assert_not_called();proceso.assert_not_called()
            self.assertEqual(c.confirmar('sí, confirmo'),'animación');c.energia_animada.assert_called_once();proceso.assert_not_called()
            permiso=False
            with self.assertRaises(PermissionError):c.apagar_ahora()
            proceso.assert_not_called()

    def test_comando_final_no_fuerza_cierre_de_programas(self):
        c=ControlPC(lambda:True)
        with patch('control_pc.subprocess.run',return_value=Mock(returncode=0)) as proceso:
            c.apagar_ahora()
            self.assertEqual(proceso.call_args.args[0],['shutdown.exe','/s','/t','0'])

    def test_cancelar_y_negar_no_arrancan_efecto(self):
        c=ControlPC(lambda:True);c.energia_animada=Mock()
        c.ejecutar('equipo_apagar','');c.confirmar('cancelar');c.energia_animada.assert_not_called()
        c.ejecutar('equipo_apagar','');c.confirmar('mejor no');c.energia_animada.assert_not_called()
        i=Interprete()
        self.assertEqual(i.ajustar_orden('apaga mi computador',interpretar('apaga mi computador'),True),Orden('equipo_apagar'))
        self.assertNotEqual(i.ajustar_orden('no apagues mi computador',interpretar('no apagues mi computador'),True),Orden('equipo_apagar'))

    def test_renderer_se_comprime_y_termina_negro(self):
        r=RendererApagado((640,360))
        inicial=r.fotograma(2);cerrando=r.fotograma(6);final=r.fotograma(DURACION)
        self.assertIsNotNone(inicial.crop((0,0,640,100)).getbbox())
        self.assertIsNone(cerrando.crop((0,0,640,100)).getbbox())
        self.assertIsNone(final.getbbox())

    def test_vista_previa_y_escape_nunca_llaman_apagado(self):
        s=SecuenciaApagado.__new__(SecuenciaApagado)
        s.cerrada=False;s.enviada=False;s.inicio=0;s.renderer=Mock();s.renderer.fotograma.return_value=Mock(size=(2,2));s.w=s.h=2
        s.c=Mock();s.item=1;s.cerrar=Mock();s.terminar=Mock();s.previa=True
        with patch('apagado.time.monotonic',return_value=DURACION+1),patch('apagado.ImageTk.PhotoImage'):
            s.tick()
        s.cerrar.assert_called_once();s.terminar.assert_not_called()
        s.cancelar=Mock();s.abortar();s.cancelar.assert_called_once();s.terminar.assert_not_called()


class Discord(unittest.TestCase):
    def test_peticiones_propias_abren_y_controlan_discord(self):
        for frase,tipo in [('abre Discord','discord_abrir'),('silénciame en Discord','discord_mutear'),
                           ('puedes mutearme en Discord','discord_mutear'),('desmutéame en Discord','discord_desmutear'),
                           ('ensordéceme en Discord','discord_ensordecer'),('desensordéceme en Discord','discord_desensordecer')]:
            self.assertEqual(interpretar(frase),Orden(tipo),frase)
        self.assertIsNone(interpretar_discord('no me mutees en Discord'))
        self.assertIsNone(interpretar_discord('mutea a Juan en Discord'))
        i=Interprete();i.registrar('abre Discord',Orden('discord_abrir'),'Abierto')
        self.assertEqual(i.ajustar_orden('silenciame',interpretar('silenciame')),Orden('discord_mutear'))

    def test_canal_y_servidor_son_datos_literales(self):
        orden=interpretar('únete al canal de voz General del servidor Amigos en Discord')
        self.assertEqual(orden.tipo,'discord_unir')
        self.assertEqual(json.loads(orden.valor),{'canal':'general','servidor':'amigos'})
        correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout='{"ok":true,"solicitado":true}'))
        self.assertIn('general',ejecutar_discord(orden,correr))
        self.assertEqual(json.loads(correr.call_args.kwargs['input']),{'accion':'unir','canal':'general','servidor':'amigos'})

    def test_estado_no_confirmado_no_se_afirma_como_exito(self):
        for valor in ({'ok':False,'codigo':'sin_confirmar'},{'ok':True}):
            correr=Mock(return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps(valor)))
            respuesta=ejecutar_discord(Orden('discord_mutear'),correr)
            self.assertNotEqual(respuesta,'Tu micrófono está silenciado en Discord.')
        correr.return_value.stdout='{"ok":true,"confirmado":true}'
        self.assertEqual(ejecutar_discord(Orden('discord_mutear'),correr),'Tu micrófono está silenciado en Discord.')

    def test_script_se_analiza_sin_acceder_a_discord(self):
        parser="[Console]::InputEncoding=New-Object Text.UTF8Encoding($false);$t=$null;$e=$null;[void][System.Management.Automation.Language.Parser]::ParseInput([Console]::In.ReadToEnd(),[ref]$t,[ref]$e);if($e.Count){$e|ForEach-Object {$_.Message};exit 1}"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(parser.encode('utf-16le')).decode()],input=DISCORD_UI,text=True,encoding='utf8',capture_output=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertNotIn('SendKeys',DISCORD_UI);self.assertNotIn('SetForegroundWindow',DISCORD_UI)


class Acento(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_apagado_de_dos_turnos_arranca_efecto_solo_tras_confirmar(self):
        with self.capri() as (c,_),patch('apagado.SecuenciaApagado') as secuencia,patch('control_pc.subprocess.run') as sistema:
            c.cfg['control_ampliado']=True
            c.enviar('apaga mi computador')
            limite=time.monotonic()+2
            while c.ocupada and time.monotonic()<limite:c.poll();time.sleep(.005)
            self.assertIsNotNone(c.control_pc.pendiente);secuencia.assert_not_called();sistema.assert_not_called()
            c.enviar('sí, confirmo')
            limite=time.monotonic()+2
            while c.ocupada and time.monotonic()<limite:c.poll();time.sleep(.005)
            secuencia.assert_called_once();sistema.assert_not_called()
            secuencia.return_value.cerrada=False;c.interrumpir()
            secuencia.return_value.abortar.assert_called_once();sistema.assert_not_called()

    def test_voz_fija_no_cambia_al_cambiar_idioma(self):
        with self.capri() as (c,ruta):
            c.guardar('voz_acento','pt-BR')
            for idioma in ('en','ja','es'):
                c.guardar('idioma',idioma)
                self.assertEqual(c.voz.acento,'pt-BR');self.assertEqual(c.voz.idioma,idioma)
                self.assertEqual(elegir_voz('capri',idioma,c.voz.acento)[0],'pt-BR-ThalitaMultilingualNeural')
            self.assertEqual(json.loads((ruta/'ajustes.json').read_text(encoding='utf8'))['voz_acento'],'pt-BR')

    def test_voz_natural_recibe_espanol_sin_traducir_con_voz_brasilena(self):
        v=Voz(lambda e:None);v.acento='pt-BR';v.idioma='es';capturados=[]
        class Comunicacion:
            def __init__(self,texto,nombre,**kwargs):capturados.append((texto,nombre))
            async def stream(self):yield {'type':'audio','data':b'audio simulado'}
        with patch('edge_tts.Communicate',Comunicacion),patch.object(v,'_reproducir_archivo',return_value=True):
            v._hablar('Hola, estamos listos.',True,v.generacion,v.cancelar)
        self.assertEqual(capturados,[('Hola estamos listos.','pt-BR-ThalitaMultilingualNeural')])
