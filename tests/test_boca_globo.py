import time
from pathlib import Path
from PIL import ImageChops,ImageTk
from test_capri import PruebasTk
import test_companera_control as fixtures

class BocaYGlobo(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def personaje(self,c):
        c.guardar('modo_visual','personaje');c.transito['inicio']-=c.transito['duracion']+.1;c.animar()

    def test_boca_alterna_en_reposo_y_sentada_sin_cambiar_cuerpo(self):
        with self.capri() as (c,_):
            self.personaje(c);p=c.companera;p.direccion=1
            for estado,cerrada,abierta in [('quieta',0,4),('sentada',3,6)]:
                p.estado=estado
                p.dibujar(c.canvas,True,True,glitch=False,halo='ninguno');self.assertIs(p.imagen,p.fotos[abierta])
                p.dibujar(c.canvas,True,False,glitch=False,halo='ninguno')
                if estado=='sentada':self.assertIs(p.imagen,p.fotos[cerrada])
                diferencia=ImageChops.difference(p.originales[cerrada],p.originales[abierta]).convert('RGB').getbbox()
                self.assertIsNotNone(diferencia)
                self.assertTrue(218<=diferencia[0]<diferencia[2]<=240)
                self.assertTrue(188<=diferencia[1]<diferencia[3]<=230)

    def test_morfosis_no_deja_descargas_sueltas_alrededor(self):
        with self.capri() as (c,_):
            c.guardar('modo_visual','personaje');c.transito['inicio']=time.monotonic()-c.transito['duracion']*.3
            c.dibujar_transito();self.assertTrue(c.canvas.find_withtag('morfosis_capri'))
            self.assertFalse(c.canvas.find_withtag('descarga'))

    def test_globo_personaje_con_retrato_respeta_voz_y_caducidad(self):
        with self.capri() as (c,_):
            self.personaje(c);d=c.dialogo
            d.ruta_retrato=Path(__file__).resolve().parents[1]/'assets/capri.ico'
            texto='Hola, choom. '+('Vamos a charlar un momento. '*18)
            d.preparar_voz(texto);self.assertEqual(d.visible,'')
            d.revelar(texto,len(texto));c.root.update_idletasks();d.dibujar()
            self.assertTrue(d.canvas.find_withtag('globo_personaje'));self.assertTrue(d.canvas.find_withtag('retrato'))
            caja=d.canvas.bbox('cuerpo');self.assertGreaterEqual(caja[0],100)
            self.assertLess(caja[2],float(d.canvas.cget('width'))-16)
            self.assertLess(caja[3],d.alto_canvas-22)
            d.terminar_voz();self.assertLessEqual(d.vence-time.monotonic(),3)
