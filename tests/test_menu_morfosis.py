import math
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from intro import geometria_morfosis
from menu_radial import sector,MenuRadial
from test_capri import PruebasTk
import test_companera_control as fixtures

class Geometria(unittest.TestCase):
    def test_crece_en_centro_y_encoge_antes_de_desplazarse(self):
        def estado(q):return geometria_morfosis(q,(1400,600),(900,500),(1700,850),(360,292),(1100,800),(210,240))
        self.assertEqual(estado(0),((1400,600),(360,292)))
        self.assertEqual(estado(.5),((900,500),(1100,800)))
        self.assertEqual(estado(.76)[0],(900,500))
        self.assertLess(estado(.76)[1][0],1100)
        self.assertEqual(estado(1),((1700,850),(210,240)))

    def test_sectores_centro_fuera_y_ocho_direcciones(self):
        self.assertEqual(sector(200,200,200,180,8),-1)
        self.assertIsNone(sector(0,0,200,180,8))
        for i in range(8):
            a=-math.pi/2+i*math.pi/4
            self.assertEqual(sector(200+math.cos(a)*140,200+math.sin(a)*140,200,180,8),i)

class Radial(PruebasTk):
    capri=fixtures.ModoPersonaje.capri
    def test_submenu_vuelve_cierra_y_accion_no_se_ejecuta_dos_veces(self):
        with self.capri() as (c,_):
            accion=Mock();opciones=[('Aspecto',[('Violeta',accion)]),('Chat',accion)]
            menu=MenuRadial(c.root,100,100,opciones)
            menu.ejecutar(0);self.assertEqual(len(menu.pila),1)
            menu.ejecutar(-1);self.assertEqual(menu.opciones,opciones);accion.assert_not_called()
            menu.ejecutar(1);menu.ejecutar(1);accion.assert_called_once()
            self.assertFalse(menu.ventana.winfo_exists())
