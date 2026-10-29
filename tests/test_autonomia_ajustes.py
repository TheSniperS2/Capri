import time
from unittest.mock import patch
from test_capri import PruebasTk
import test_companera_control as fixtures

class Autonomia(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_arrastrar_no_impide_reanudar_viajes_y_destino_puede_estar_arriba(self):
        with self.capri() as (c,_),patch('companera.area_trabajo',return_value=(0,0,1920,1080)),patch('companera.visibles',return_value=[]):
            p=c.companera;p.redimensionar(1);p.posar(700,350)
            p.proxima_accion=p.ultimo
            with patch('companera.random.uniform',side_effect=[9,1000,100]):p.tick(ahora=p.ultimo+.1)
            self.assertEqual(p.salto['destino'],(1000,100));self.assertIsNone(p.ancla)

    def test_ventana_cercana_es_candidata_para_sentarse(self):
        v={'id':8,'rect':(200,400,1200,800),'titulo':'Cerca'}
        with self.capri() as (c,_),patch('companera.area_trabajo',return_value=(0,0,1920,1080)),patch('companera.visibles',return_value=[v]):
            p=c.companera;p.redimensionar(1);p.x=100;p.y=400;p.ventanas=[v]
            with patch('companera.random.random',return_value=0):p.elegir_viaje(p.ultimo)
            self.assertEqual(p.salto['id'],8)
            self.assertAlmostEqual(p.salto['destino'][1]+p.alto*.64,400)

    def test_caida_inmediata_estaca_y_limpieza_en_siguiente_viaje(self):
        with self.capri() as (c,_),patch('companera.area_trabajo',return_value=(0,0,1920,1080)),patch('companera.visibles',return_value=[]):
            p=c.companera;p.redimensionar(1);p.posar(600,150);p.gracia_fisica=0;p.proxima_accion=p.ultimo+100
            y=p.y
            with patch('companera.random.random',return_value=1):
                p.tick(ahora=p.ultimo+.05)
                self.assertGreater(p.y,y)
                for _ in range(8):p.tick(ahora=p.ultimo+.05)
            self.assertGreater(p.y-y,80);self.assertLess(p.y,1080-p.alto)
            with patch('companera.random.random',return_value=0):p.tick(ahora=p.ultimo+.05)
            self.assertIsNotNone(p.ancla);y=p.y;p.dibujar(c.canvas,glitch=False)
            self.assertTrue(c.canvas.find_withtag('ancla_personaje'))
            p.tick(ahora=p.ultimo+.1);self.assertLess(p.y-y,16)
            p.elegir_viaje(p.ultimo);self.assertIsNone(p.ancla)
            p.dibujar(c.canvas,glitch=False);self.assertFalse(c.canvas.find_withtag('ancla_personaje'))

    def test_pausar_viajes_pausa_fisica_y_teletransportes(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]):
            p=c.companera;p.redimensionar(1);p.posar(400,100);p.gracia_fisica=0;p.proxima_accion=0
            p.tick(pasear=False,ahora=p.ultimo+10)
            self.assertEqual(p.y,100);self.assertIsNone(p.salto)

    def test_ajustes_por_canales_y_galeria_con_previsualizaciones(self):
        with self.capri() as (c,carpeta):
            antes=c.cfg['voz_perfil']
            c.configurar();c.ajustes.withdraw()
            ui=c.panel_ajustes
            self.assertEqual(set(ui.secciones),{'Escritorio','Micrófono','Voz','IA y servicios','Permisos'})
            ui.mostrar('Micrófono');self.assertEqual(ui.actual,'Micrófono')
            self.assertIs(c.micro_combo.master.master,ui.secciones['Micrófono'])
            c.abrir_aspectos();g=c.galeria_aspectos;g.ventana.withdraw()
            self.assertEqual(len(g.fotos),5)
            self.assertTrue(all(b.find_withtag('vista_aspecto') for b in g.botones.values()))
            g.aplicar('hielo');self.assertEqual(c.cfg['halo_personaje'],'hielo')
            self.assertEqual(c.cfg['voz_perfil'],antes)
