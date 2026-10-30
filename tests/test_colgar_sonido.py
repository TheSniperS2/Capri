import io,os,wave,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from unittest.mock import Mock,patch
import numpy as np
import tkinter as tk
from audio_llamada import sonido_colgado
from voz import Voz
from test_capri import PruebasTk
import test_companera_control as fixtures


class SonidoColgar(unittest.TestCase):
    def test_desconexion_wav_breve_y_volumen_proporcional(self):
        def leer(volumen):
            with wave.open(io.BytesIO(sonido_colgado(volumen)),'rb') as w:
                self.assertEqual(w.getnchannels(),1);self.assertEqual(w.getsampwidth(),2)
                self.assertAlmostEqual(w.getnframes()/w.getframerate(),.24,places=3)
                return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
        completo=leer(100);bajo=leer(25)
        self.assertGreater(np.max(abs(completo)),1000)
        self.assertAlmostEqual(np.linalg.norm(bajo)/np.linalg.norm(completo),.25,places=3)
        self.assertEqual(sonido_colgado(0),b'')

    @unittest.skipUnless(os.name=='nt','Reproductor de Windows')
    def test_no_modifica_generacion_voz_ni_emite_eventos_de_narracion(self):
        estado=Mock();v=Voz(estado);generacion=v.generacion
        with patch('winsound.PlaySound') as play:
            hilo=v.sonido_colgar(40);hilo.join(timeout=2)
            self.assertFalse(hilo.is_alive());play.assert_called_once()
            self.assertEqual(play.call_args.args[0][:4],b'RIFF')
            self.assertIsNone(v.sonido_colgar(0));play.assert_called_once()
        self.assertEqual(v.generacion,generacion);estado.assert_not_called()
        self.assertFalse(v.cancelar.is_set())


class CierreMensaje(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_rechazar_sin_contestar_no_suena_y_no_oculta_otro_mensaje(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta):
            c.cfg['voz']=True;c.dialogo.mostrar('Una respuesta anterior.');c.llamar_capri();c.llamada_ui.rechazar()
            c.voz.sonido_colgar.assert_not_called();self.assertNotEqual(c.dialogo.ventana.state(),'withdrawn')

    def test_colgar_no_borra_una_respuesta_posterior(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar'):
            c.cfg['voz']=True;c.llamar_capri();c.llamada_ui.aceptar();c.revisar_interacciones()
            c.dialogo.mostrar('Una respuesta nueva.');c.llamada_ui.terminar_voz()
            self.assertNotEqual(c.dialogo.ventana.state(),'withdrawn')
            self.assertEqual(c.dialogo.objetivo,'Una respuesta nueva.')
            c.voz.sonido_colgar.assert_called_once()
