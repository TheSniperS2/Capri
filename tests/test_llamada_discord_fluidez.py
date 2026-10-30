import time
import tkinter as tk
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from core import interpretar,Orden
from travesuras import Travesuras
from llamadas import LlamadaCapri
from apagado import SecuenciaApagado,DURACION


class LlamadasYFluidez(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_variantes_equivalentes_de_discord_y_no_cambia_objetivo(self):
        for frase in ('Capri muteame el Discord','Capri mutéame del Discord','mutéame en el Discord',
                      'muteame Discord','me puedes mutear en Discord por favor','silénciame de Discord'):
            self.assertEqual(interpretar(frase),Orden('discord_mutear'),frase)
        for frase in ('desmuteame el discord','quita mi silencio en el discord'):
            self.assertEqual(interpretar(frase),Orden('discord_desmutear'))
        for frase in ('no me mutees el discord','mutea a Juan en Discord','muteame el Spotify','si digo muteame el discord no lo hagas'):
            self.assertNotEqual(interpretar(frase),Orden('discord_mutear'))

    def test_bolsa_no_repite_dialogos_hasta_recorrerlos_todos(self):
        j=Travesuras();frases=[j.frase() for _ in range(24)]
        self.assertEqual(len(set(frases)),24)
        self.assertTrue(any('Toc, toc' in f for f in frases))
        self.assertNotEqual(j.frase(),frases[-1])

    def test_llamada_posicion_conexion_idempotente_y_cierre(self):
        root=tk.Tk();root.withdraw();original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        try:
            with patch('llamadas.tk.Toplevel',Oculta),patch('ventanas.area_trabajo',return_value=(0,40,1920,1080)):
                aceptar=Mock();terminar=Mock();l=LlamadaCapri(root,aceptar,terminar)
                self.assertEqual((l.x,l.y),(28,68))
                l.aceptar();l.aceptar();aceptar.assert_called_once()
                self.assertTrue(l.conectada);self.assertFalse(l.cerrada)
                self.assertTrue(any(l.c.type(i)=='text' and l.c.itemcget(i,'text')=='CAPRI' for i in l.c.find_all()))
                l.terminar_voz();self.assertTrue(l.cerrada)
        finally:root.destroy()

    def test_asomo_automatico_no_ofrece_boton_de_prueba(self):
        with self.capri() as (c,_):
            c.configurar()
            def textos(w):return [getattr(w,'texto','')]+[s for h in w.winfo_children() for s in textos(h)]
            self.assertNotIn('Probar asomo',textos(c.ajustes));self.assertTrue(c.cfg['asomos_curiosos'])

    def test_apagado_deja_atender_eventos_y_final_solo_tras_animacion(self):
        root=tk.Tk();root.withdraw();original=tk.Toplevel
        class Fuera(original):
            def geometry(self,v=None):return super().geometry(v.split('+')[0]+'+30000+30000' if v else None)
            def focus_force(self):pass
        try:
            with patch('apagado.tk.Toplevel',Fuera):
                terminar=Mock();s=SecuenciaApagado(root,terminar,Mock())
                pulsos=[]
                def latido():
                    pulsos.append(time.perf_counter());root.after(10,latido)
                root.after(10,latido);root.after(180,root.quit);inicio=time.perf_counter();root.mainloop()
                self.assertGreaterEqual(len(pulsos),5);self.assertLess(time.perf_counter()-inicio,2)
                self.assertTrue(s.c.find_withtag('escena'));terminar.assert_not_called()
                s.inicio=time.monotonic()-DURACION-1;s.tick();terminar.assert_called_once()
                self.assertFalse(s.c.find_withtag('escena'));s.cerrar()
        finally:root.destroy()
