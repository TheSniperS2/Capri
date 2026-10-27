from pathlib import Path
import tempfile
import unittest
from PIL import Image
from avatar import estados_originales,BOCA
from voz import texto_para_voz

class Expresiones(unittest.TestCase):
    def test_elimina_boca_base_incluso_si_overlay_es_transparente(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        with tempfile.TemporaryDirectory() as d:
            atlas=Path(d)/'bocas.png';Image.new('RGBA',(93,25)).save(atlas)
            estados=estados_originales(assets/'capri-base-v2.png',atlas)
            original=estados[0].crop(BOCA)
            blancos=[(x,y) for y in range(original.height) for x in range(original.width)
                     if min(original.getpixel((x,y))[:3])>150 and max(original.getpixel((x,y))[:3])-min(original.getpixel((x,y))[:3])<=45]
            self.assertTrue(blancos)
            for estado in estados[1:]:
                for x,y in blancos:self.assertLess(max(estado.getpixel((x+BOCA[0],y+BOCA[1]))[:3]),45)

    def test_tts_sin_caras_conserva_idiomas_numeros_y_texto_original(self):
        texto='¡Claro! 😏 Hola 😊 :) Never Fade Away a las 12:30 por 3,5 euros.'
        hablado=texto_para_voz(texto)
        self.assertNotIn('😏',hablado);self.assertNotIn('😊',hablado);self.assertNotIn(':)',hablado)
        self.assertIn('Never Fade Away',hablado);self.assertIn('12:30',hablado);self.assertIn('3,5',hablado)
        self.assertIn('😏',texto);self.assertEqual(texto_para_voz('😊 😏'),'')
