from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from ajustes_ui import SelectorCyber,EscalaCyber
from voz import datos_atajo

class Interaccion(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def preparar(self,c,canal):
        c.configurar();c.ajustes.geometry('820x770');c.panel_ajustes.mostrar(canal);c.ajustes.update()

    def test_rueda_en_selector_y_deslizador_solo_desplaza_seccion(self):
        with self.capri() as (c,_):
            self.preparar(c,'Escritorio');ui=c.panel_ajustes
            controles=ui.secciones['Escritorio'].winfo_children()
            selector=next(w for w in controles if isinstance(w,SelectorCyber))
            escala=next(w for w in controles if isinstance(w,EscalaCyber))
            elegido=selector.get();valor=escala.get();antes=ui.vistas['Escritorio'][1].yview()[0]
            selector.event_generate('<MouseWheel>',delta=-120);c.ajustes.update()
            escala.event_generate('<MouseWheel>',delta=-120);c.ajustes.update()
            self.assertEqual(selector.get(),elegido);self.assertEqual(escala.get(),valor)
            self.assertGreater(ui.vistas['Escritorio'][1].yview()[0],antes)

    def test_permisos_empieza_arriba_no_scroll_y_ventana_topmost(self):
        with self.capri() as (c,_):
            self.preparar(c,'Permisos');ui=c.panel_ajustes
            self.assertFalse(ui.barras['Permisos'].winfo_manager())
            self.assertEqual(ui.vistas['Permisos'][1].yview(),(0.,1.))
            diferencia=ui.secciones['Permisos'].winfo_rooty()-ui.vistas['Permisos'][1].winfo_rooty()
            self.assertLess(abs(diferencia),3)
            self.assertTrue(c.ajustes.attributes('-topmost'))

    def test_captura_combinacion_y_cancelacion_restaura_atajo(self):
        with self.capri() as (c,_),patch('app.Atajo') as registro:
            self.preparar(c,'Voz');viejo=c.atajo=Mock();captura=c.captura_tecla
            captura.iniciar();viejo.cerrar.assert_called_once();self.assertIsNone(c.atajo)
            captura.capturar(Mock(keysym='space',state=4))
            self.assertEqual(c.cfg['tecla_hablar'],'Ctrl+Space');self.assertFalse(captura.capturando)
            self.assertEqual(registro.call_args.args[2],'Ctrl+Space')
            self.assertEqual(datos_atajo('Ctrl+Space'),(0x4002,0x20))
            captura.iniciar();captura.capturar(Mock(keysym='Escape',state=0))
            self.assertEqual(c.cfg['tecla_hablar'],'Ctrl+Space');self.assertIsNotNone(c.atajo)

    def test_modo_pantalla_tambien_usa_menu_radial(self):
        with self.capri() as (c,_):
            c.menu(Mock(x_root=500,y_root=350))
            self.assertTrue(c.radial.canvas.find_withtag('sector_0'))
            self.assertIn('Modo personaje',[n for n,a in c.radial.opciones])
