from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageChops
from test_capri import PruebasTk
import test_companera_control as fixtures
from avatar import vista_pantalla,fragmentar


class SenalRaster(unittest.TestCase):
    def test_fragmentacion_conserva_fuente_y_transparencia_sin_envolver_bordes(self):
        im=Image.new('RGBA',(210,240));d=ImageDraw.Draw(im)
        d.rectangle((60,15,150,220),fill='#ff214b');antes=im.tobytes()
        variantes=[fragmentar(im,i,True) for i in range(6)]
        self.assertEqual(len({v.tobytes() for v in variantes}),6)
        self.assertEqual(im.tobytes(),antes)
        for v in variantes:
            self.assertEqual(v.getpixel((0,0))[3],0);self.assertEqual(v.getpixel((209,239))[3],0)
            self.assertTrue(set(v.getchannel('A').tobytes())<={0,255})
            self.assertIsNotNone(ImageChops.subtract(v.getchannel('A'),im.getchannel('A')).getbbox())

    def test_camara_fases_distintas_sin_alterar_original(self):
        with Image.open(Path(__file__).resolve().parents[1]/'assets/capri-base-hd-v1.png') as archivo:im=archivo.convert('RGBA')
        original=im.tobytes();fases=[vista_pantalla(im,fase=i) for i in range(3)]
        self.assertEqual(im.tobytes(),original)
        self.assertEqual(len({f.tobytes() for f in fases}),3)
        self.assertTrue(all(f.size==(320,210) for f in fases))


class SenalTk(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_glitch_es_temporal_se_puede_apagar_y_no_recrea_fotos_en_cada_tick(self):
        with self.capri() as (c,_):
            p=c.companera;p.redimensionar(1);p.proximo_glitch=0;p.direccion=1
            fotos=[str(f) for lista in p.glitches for f in lista]
            with patch('companera.time.monotonic',return_value=100):
                p.dibujar(c.canvas,glitch=True,halo='ninguno');self.assertTrue(p.glitch_activo)
                self.assertIn(str(p.imagen),fotos)
                p.dibujar(c.canvas,glitch=False,halo='ninguno');self.assertFalse(p.glitch_activo)
                self.assertIn(p.imagen,p.fotos+p.espejos)
            with patch('companera.time.monotonic',return_value=101):
                p.dibujar(c.canvas,glitch=True,halo='ninguno');self.assertFalse(p.glitch_activo)
            self.assertEqual(fotos,[str(f) for lista in p.glitches for f in lista])
