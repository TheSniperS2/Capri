import base64
import json
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from voz import Voz
from discord_control import DISCORD_UI
from test_capri import PruebasTk
import test_companera_control as fixtures


class Brasil(unittest.TestCase):
    def test_fallo_thalita_reintenta_voz_brasilena_sin_voz_windows_ni_traduccion(self):
        v=Voz(lambda e:None);v.acento='pt-BR';v.idioma='es';llamadas=[]
        v.natural_no_hasta=time.monotonic()+999;limites=[]
        async def esperar(coro,timeout):limites.append(timeout);return await coro
        class Sintesis:
            def __init__(self,texto,voz,**kw):
                llamadas.append((texto,voz))
                if voz=='pt-BR-ThalitaMultilingualNeural':raise TimeoutError()
            async def stream(self):yield {'type':'audio','data':b'audio'}
        with patch('edge_tts.Communicate',Sintesis),patch('voz.asyncio.wait_for',esperar),patch.object(v,'_reproducir_archivo',return_value=True),patch.object(v,'_reproducir_windows') as windows:
            v._hablar('Hola. Estamos listos.',True,v.generacion,v.cancelar)
            windows.assert_not_called()
        self.assertEqual([p[1] for p in llamadas],['pt-BR-ThalitaMultilingualNeural','pt-BR-FranciscaNeural'])
        self.assertEqual({p[0] for p in llamadas},{'Hola. Estamos listos.'})
        self.assertEqual(v.ultima_voz_usada,'pt-BR-FranciscaNeural')
        self.assertTrue(limites);self.assertGreaterEqual(min(limites),12)


class DiscordToggle(unittest.TestCase):
    def test_boton_real_tipo_toggle_con_etiqueta_constante_no_se_pulsa_dos_veces(self):
        funciones='function N'+DISCORD_UI.split(' function N',1)[1].split(' function Raiz',1)[0]
        patrones=' $micro='+DISCORD_UI.split(' $micro=',1)[1].split(' function Estado',1)[0]
        estado='function Estado {'+DISCORD_UI.split(' function Estado {',1)[1].split('\n $e=Estado',1)[0]
        script=r'''
Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
$d=[pscustomobject]@{accion='mutear'}
$toggle=[pscustomobject]@{Current=[pscustomobject]@{ToggleState=[Windows.Automation.ToggleState]::Off};veces=0}
$toggle|Add-Member ScriptMethod Toggle {$this.Current.ToggleState=[Windows.Automation.ToggleState]::On;$this.veces++}
$boton=[pscustomobject]@{Current=[pscustomobject]@{Name='Silenciar';IsEnabled=$true;ControlType=[Windows.Automation.ControlType]::Button};patron=$toggle}
$boton|Add-Member ScriptMethod TryGetCurrentPattern {param($id,[ref]$salida) if($id -eq [Windows.Automation.TogglePattern]::Pattern){$salida.Value=$this.patron;return $true};return $false}
function Items {return $boton}
'''+funciones+patrones+estado+r'''
$e=Estado;$antes=$e.muted
if(!$e.muted){[void](Invocar $e.boton $true)}
$e=Estado;$despues=$e.muted
if(!$e.muted){[void](Invocar $e.boton $true)}
@{antes=$antes;despues=$despues;veces=$toggle.veces;etiqueta=$boton.Current.Name}|ConvertTo-Json -Compress
'''
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],capture_output=True,text=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),{'antes':False,'despues':True,'veces':1,'etiqueta':'Silenciar'})


class VistaPreviaReal(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_boton_abre_toplevel_real_con_imagen_y_sin_apagado(self):
        original=tk.Toplevel
        class FueraDePantalla(original):
            def geometry(self,valor=None):
                if valor:
                    tamano=valor.split('+')[0]
                    if not tamano or tamano.startswith('-'):tamano='800x600'
                    valor=tamano+'+30000+30000'
                return super().geometry(valor)
            def focus_force(self):pass
        with self.capri() as (c,_),patch('apagado.tk.Toplevel',FueraDePantalla),patch.object(c.control_pc,'apagar_ahora') as apagar:
            errores=[];c.root.report_callback_exception=lambda *e:errores.append(str(e[1]))
            c.configurar();c.panel_ajustes.mostrar('Permisos');c.root.update_idletasks()
            def buscar(widget):
                if getattr(widget,'texto','')=='Vista previa del apagado':return widget
                for hijo in widget.winfo_children():
                    encontrado=buscar(hijo)
                    if encontrado:return encontrado
            boton=buscar(c.ajustes);self.assertIsNotNone(boton);boton.invoke()
            c.root.update_idletasks();s=c.apagado_ui
            self.assertTrue(s.previa);self.assertTrue(s.v.winfo_ismapped())
            self.assertEqual(str(s.v.transient()),str(c.ajustes))
            self.assertTrue(s.c.find_withtag('escena'))
            self.assertFalse(any(s.c.type(i)=='image' for i in s.c.find_all()))
            self.assertEqual(s.w,c.root.winfo_screenwidth());self.assertFalse(errores,errores)
            s.abortar();apagar.assert_not_called()
