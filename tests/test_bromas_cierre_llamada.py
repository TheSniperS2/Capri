import time,wave,tempfile
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
import tkinter as tk
from test_capri import PruebasTk
import test_companera_control as fixtures
from travesuras import Travesuras
from audio_llamada import preparar,factor_mascara


class Bromas(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_llamadas_son_bromas_cerradas_con_disfraces_y_sin_preguntas(self):
        j=Travesuras();frases=[j.frase() for _ in range(24)]
        self.assertEqual(len(set(frases)),24)
        self.assertEqual({j.disfraz(f) for f in frases},{None,'ardilla','villana','robot'})
        for f in frases:
            self.assertNotIn('¿',f);self.assertNotIn('?',f);self.assertNotIn('pausa',f.lower())
        for tipo,n in (('asomar',6),('minimizar',5),('saludo',4)):
            for _ in range(n):
                f=j.frase(tipo);self.assertNotIn('¿',f);self.assertNotIn('?',f)

    def test_fin_de_reproduccion_cierra_aviso_en_el_mismo_poll(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar'):
            c.cfg['voz']=True;c.llamar_capri();c.llamada_ui.aceptar();c.revisar_interacciones()
            llamada=c.llamada_ui
            self.assertIsNotNone(c.voz_ticket);self.assertFalse(llamada.cerrada)
            c.eventos.put(('voz',(c.voz.generacion,True)));c.poll()
            self.assertTrue(c.narracion_activa);self.assertFalse(llamada.cerrada)
            c.eventos.put(('voz',(c.voz.generacion,False)));c.poll()
            self.assertTrue(llamada.cerrada);self.assertIsNone(c.voz_ticket)
            self.assertEqual(c.dialogo.ventana.state(),'withdrawn');self.assertIsNone(c.dialogo.pendiente)
            c.voz.sonido_colgar.assert_called_once_with(c.cfg.get('volumen_voz',100))
            llamada.terminar_voz();c.voz.sonido_colgar.assert_called_once()

    def test_colgar_durante_preparacion_cancela_y_no_deja_broma_pendiente(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar'),patch.object(c.voz,'parar') as parar:
            c.cfg['voz']=True;c.llamar_capri();c.llamada_ui.aceptar();c.revisar_interacciones()
            c.llamada_ui.rechazar();parar.assert_called_once()
            self.assertIsNone(c.mensaje_llamada_pendiente);self.assertIsNone(c.voz_ticket)

    def test_vibracion_cambia_icono_sin_mover_botones_o_ventana(self):
        original=tk.Toplevel;root=tk.Tk();root.withdraw()
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        from llamadas import LlamadaCapri
        try:
            with patch('llamadas.tk.Toplevel',Oculta):
                l=LlamadaCapri(root,Mock(),Mock());inicio=l.inicio
                with patch('llamadas.time.monotonic',return_value=inicio+.04):l.dibujar()
                icono=l.c.coords('telefono');boton=l.c.coords(l.c.find_withtag('contestar')[0]);posicion=(l.x,l.y)
                with patch('llamadas.time.monotonic',return_value=inicio+.12):l.dibujar()
                self.assertNotEqual(icono,l.c.coords('telefono'))
                self.assertEqual(boton,l.c.coords(l.c.find_withtag('contestar')[0]));self.assertEqual(posicion,(l.x,l.y))
                l.cerrar()
        finally:root.destroy()

    def test_disfraces_sobre_audio_real_modifican_duracion_y_no_el_original(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tono.wav';t=np.arange(16000)/16000
            with wave.open(str(p),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
                w.writeframes((np.sin(2*np.pi*700*t)*6000).astype('<i2').tobytes())
            original=p.read_bytes();resultados=[]
            for mascara in ('ardilla','villana','robot'):
                salida,niveles,_=preparar(p,mascara=mascara)
                try:
                    with wave.open(str(salida),'rb') as w:
                        self.assertAlmostEqual(w.getnframes()/16000,1/factor_mascara(mascara),places=3)
                    resultados.append(salida.read_bytes());self.assertTrue(niveles)
                finally:salida.unlink(missing_ok=True)
            self.assertEqual(len(set(resultados)),3);self.assertEqual(original,p.read_bytes())
