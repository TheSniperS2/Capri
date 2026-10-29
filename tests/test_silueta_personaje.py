import unittest
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from companera import limpiar_silueta,glitch_silueta,sombra_glitch

class Silueta(unittest.TestCase):
    def test_sombra_es_silueta_coloreada_completa_sin_rectangulo_negro(self):
        im=Image.new('RGBA',(60,70));ImageDraw.Draw(im).rectangle((20,20,40,50),fill=(0,0,0,255))
        sombra=sombra_glitch(im,'#9465ed')
        self.assertEqual(set(sombra.getchannel('A').tobytes()),{0,255})
        self.assertEqual(sombra.getpixel((0,0))[3],0)
        self.assertEqual(sombra.getpixel((30,30))[3],255)
        self.assertEqual(sombra.getchannel('A').tobytes(),im.getchannel('A').tobytes())
        self.assertIsNotNone(sombra.getbbox())
    def test_motas_negras_y_alfa_intermedio_no_aparecen_en_escritorio(self):
        im=Image.new('RGBA',(80,100))
        d=ImageDraw.Draw(im);d.rectangle((20,20,60,90),fill=(6,6,12,255))
        d.rectangle((30,25,50,40),fill=(0,255,80,255));d.point((2,3),fill=(0,0,0,255))
        d.point((4,3),fill=(0,0,0,70))
        limpia=limpiar_silueta(im)
        self.assertEqual(limpia.getpixel((2,3))[3],0)
        self.assertEqual(limpia.getpixel((25,50))[3],255)
        self.assertEqual(set(limpia.getchannel('A').tobytes()),{0,255})
        for i in range(2):
            frame=glitch_silueta(limpia,i)
            fuera=ImageChops.subtract(frame.getchannel('A'),limpia.getchannel('A'))
            self.assertIsNone(fuera.getbbox())
            self.assertEqual(set(frame.getchannel('A').tobytes()),{0,255})
