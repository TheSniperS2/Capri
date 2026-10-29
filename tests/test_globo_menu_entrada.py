from unittest.mock import Mock
from test_capri import PruebasTk
import test_companera_control as fixtures
from idiomas import ui
from menu_radial import sector


class GloboMenuEntrada(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_corchetes_no_cambian_al_enfocar_y_escribir(self):
        with self.capri() as (c,_):
            c.abrir_chat();c.panel.update()
            antes=[c.campo_entrada.coords(i) for i in c.campo_entrada.find_withtag('corchetes')]
            c.entrada.event_generate('<FocusIn>');c.entrada.insert(0,'un mensaje');c.panel.update()
            despues=[c.campo_entrada.coords(i) for i in c.campo_entrada.find_withtag('corchetes')]
            self.assertEqual(antes,despues)
            self.assertEqual(c.entrada.cget('highlightthickness'),0)
            self.assertEqual(c.entrada.get(),'un mensaje')
            self.assertEqual(c.placeholder_entrada.winfo_manager(),'')

    def test_globo_pantalla_preparando_no_queda_vacio_y_actualiza_idioma(self):
        with self.capri() as (c,_):
            c.guardar('idioma','ja');d=c.dialogo;d.recibir_usuario('Siguiente canción.')
            d.preparar_voz('次の曲に進んだよ。');d.dibujar()
            self.assertEqual(len(d.canvas.find_withtag('pensando')),3)
            self.assertEqual(d.canvas.itemcget('cuerpo','text'),'')
            c.guardar('idioma','pt')
            pregunta=d.canvas.itemcget('pregunta','text')
            self.assertTrue(pregunta.startswith('VOCÊ'),pregunta)
            self.assertNotIn('あなた',pregunta)

    def test_etiquetas_radiales_caben_en_su_sector_en_cuatro_idiomas(self):
        with self.capri() as (c,_):
            for idioma in ('es','en','pt','ja'):
                with self.subTest(idioma=idioma):
                    c.guardar('idioma',idioma);c.abrir_menu_radial(Mock(x_root=700,y_root=400));m=c.radial;m.ventana.update()
                    for i,(nombre,_) in enumerate(m.opciones):
                        bbox=m.canvas.bbox(f'etiqueta_{i}')
                        for x,y in ((bbox[0],bbox[1]),(bbox[2],bbox[1]),(bbox[0],bbox[3]),(bbox[2],bbox[3])):
                            self.assertEqual(sector(x,y,m.centro,m.radio,len(m.opciones)),i,(idioma,nombre,bbox))
                    c.cerrar_radial()
