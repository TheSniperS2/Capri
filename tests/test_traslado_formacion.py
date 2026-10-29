import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from intro import TrasladoTeselas,Transformacion
from menu_radial import colocar_menu
from voz import elegir_voz,PERFILES_VOZ
from test_capri import PruebasTk
import test_companera_control as fixtures

class Geometria(unittest.TestCase):
    def test_menu_busca_espacio_fuera_del_personaje_y_dentro_de_pantalla(self):
        for rect in ((1600,780,210,240),(4,4,210,240),(800,4,210,240),(800,400,210,240)):
            x,y=colocar_menu(rect,(1920,1080),430);a,b,w,h=rect
            self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
            self.assertLessEqual(x+430,1920);self.assertLessEqual(y+430,1080)
            self.assertEqual(max(0,min(x+430,a+w)-max(x,a))*max(0,min(y+430,b+h)-max(y,b)),0)
        self.assertLess(colocar_menu((1600,780,210,240),(1920,1080),430)[1],780-430)

    def test_perfiles_de_voz_conservan_clasica_y_rechazan_id_desconocido(self):
        self.assertEqual(elegir_voz('capri'),('es-MX-DaliaNeural','+16Hz'))
        self.assertEqual(elegir_voz('no_existe'),elegir_voz('capri'))
        self.assertGreaterEqual(len({elegir_voz(k)[0] for k in PERFILES_VOZ}),4)

class Movimiento(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_arrastre_conserva_cualquier_posicion_sin_forzar_esquina_o_suelo(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]),patch('companera.area_trabajo',return_value=(0,0,1920,1080)):
            p=c.companera;p.redimensionar(1);p.iniciar();p.posar(720,330)
            for n in range(40):p.tick(pasear=False,ahora=p.ultimo+.05)
            self.assertEqual((p.x,p.y),(720,330));self.assertIsNone(p.salto)

    def test_teselas_son_sprite_y_terminan_en_la_pose_del_destino(self):
        with self.capri() as (c,_):
            p=c.companera;p.redimensionar(1)
            t=TrasladoTeselas(p.lienzos[0],p.lienzos[3],(1500,850),(220,300))
            t.dibujar(c.canvas,.5)
            self.assertTrue(c.canvas.find_withtag('fragmento_viaje'))
            self.assertFalse(c.canvas.find_withtag('descarga'))
            self.assertTrue(all(c.canvas.type(i)=='image' for i in c.canvas.find_withtag('fragmento_viaje')))
            c.canvas.delete('all');t.dibujar(c.canvas,1)
            for item,(fotos,(ox,oy),_,_) in zip(c.canvas.find_withtag('fragmento_viaje'),t.piezas):
                self.assertEqual(c.canvas.coords(item),[220+ox,300+oy])
                self.assertEqual(c.canvas.itemcget(item,'image'),str(fotos[3]))

    def test_pose_pequena_se_completa_antes_del_ultimo_tramo(self):
        with self.capri() as (c,_),patch('intro.ImageTk.PhotoImage',side_effect=lambda im:im):
            t=Transformacion(Image.new('RGBA',(320,210),'blue'),Image.new('RGBA',(600,400),'red'),
                             Image.new('RGBA',(210,240),'green'),(400,300),(550,400),640,480)
            try:
                fin=time.monotonic()+10
                while time.monotonic()<fin and (len(t.fotos)!=t.cantidad or not all(t.fotos)):
                    t.actualizar();time.sleep(.002)
                self.assertTrue(all(t.fotos))
                self.assertEqual(t.fotos[0].getpixel((20,40))[:3],(16,9,13))
                for q in (.81,.88,.96,1):
                    im=t.fotos[round(q*(t.cantidad-1))]
                    self.assertEqual(im.getpixel((im.width//2,im.height//2))[:3],(0,128,0))
            finally:t.detener();t.worker.join(1)

    def test_alternar_modos_reutiliza_las_dos_direcciones_preparadas(self):
        with self.capri() as (c,_):
            primera=None
            for modo in ('personaje','pantalla'):
                c.guardar('modo_visual',modo);t=c.transito['morfosis']
                fin=time.monotonic()+10
                while time.monotonic()<fin and (len(t.fotos)!=t.cantidad or not all(t.fotos)):
                    t.actualizar();time.sleep(.002)
                self.assertTrue(all(t.fotos))
                if modo=='personaje':primera=t.fotos
                c.finalizar_transito()
            c.guardar('modo_visual','personaje')
            self.assertIs(c.transito['morfosis'].fotos,primera)
