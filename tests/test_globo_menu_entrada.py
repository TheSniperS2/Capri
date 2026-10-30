from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from idiomas import ui
from menu_radial import sector
from league import MENSAJES
import time


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
                        icono=m.canvas.bbox(f'icono_{i}')
                        self.assertGreaterEqual(bbox[1]-icono[3],6,(idioma,nombre,bbox,icono))
                        for x,y in ((bbox[0],bbox[1]),(bbox[2],bbox[1]),(bbox[0],bbox[3]),(bbox[2],bbox[3])):
                            self.assertEqual(sector(x,y,m.centro,m.radio,len(m.opciones)),i,(idioma,nombre,bbox))
                    c.cerrar_radial()

    def test_escribir_alterna_globo_y_conserva_borrador(self):
        with self.capri() as (c,_):
            d=c.dialogo;d.recibir_usuario('hola');d.objetivo=d.visible='Hola.'
            c.alternar_escritura();self.assertTrue(d.manual)
            self.assertEqual(d.ventana.state(),'withdrawn')
            self.assertTrue(d.componiendo)
            c.entrada_compacta.poner('borrador')
            c.alternar_escritura()
            self.assertEqual(d.ventana.state(),'withdrawn');self.assertIsNone(d.pendiente)
            self.assertEqual(c.entrada_compacta.entrada.get(),'borrador')
            d.posicionar((600,400,360,338))
            self.assertEqual(d.ventana.state(),'withdrawn')

    def test_abandonar_escritura_no_resucita_mensaje_anterior_y_conserva_borrador(self):
        with self.capri() as (c,_):
            d=c.dialogo;d.recibir_usuario('anterior');d.visible=d.objetivo='Respuesta anterior'
            c.alternar_escritura();c.entrada_compacta.poner('borrador sin enviar')
            with patch.object(c,'escribiendo',return_value=False):c.cancelar_escritura_sin_foco()
            self.assertFalse(d.manual);self.assertFalse(d.componiendo);self.assertIsNone(d.pendiente)
            self.assertEqual(d.ventana.state(),'withdrawn')
            self.assertEqual(c.entrada_compacta.entrada.get(),'borrador sin enviar')
            self.assertEqual(d.objetivo,'Respuesta anterior')

    def test_globo_sigue_arrastre_en_el_mismo_evento_sin_esperar_tick(self):
        with self.capri() as (c,_):
            d=c.dialogo;d.recibir_usuario('hola');d.objetivo=d.visible='Hola.';d.canvas.configure(width=360);d.dibujar()
            c.drag=(100,100,400,400,0)
            with patch.object(d.ventana,'geometry') as mover,patch.object(d,'dibujar') as pintar,patch.object(c.root,'winfo_width',return_value=360),patch.object(c.root,'winfo_height',return_value=338):
                c._arrastrar(Mock(x_root=137,y_root=125))
                esperado=f'360x{d.alto_canvas}+437+{425-d.alto_canvas-8}'
                self.assertEqual(mover.call_args.args[0],esperado);pintar.assert_not_called()
            ancho=int(d.canvas.cget('width'));alto=d.alto_canvas
            self.assertEqual(d.canvas.coords('borde_inferior'),[10,alto-12,ancho-22,alto-12,ancho-10,alto-24])

    def test_globo_sigue_configure_y_punta_sin_remaquetar_cuerpo(self):
        with self.capri() as (c,_):
            d=c.dialogo;d.personaje=lambda:True;d.recibir_usuario('hola');d.visible=d.objetivo='Hola.';d.dibujar()
            d.posicionar((600,600,200,260))
            with patch.object(d.ventana,'geometry') as mover,patch.object(d,'dibujar') as pintar:
                d._seguir_raiz(Mock(widget=c.root,x=670,y=600,width=200,height=260))
                self.assertIn('+550+',mover.call_args.args[0]);pintar.assert_not_called()
                d.geometria=None;d.posicionar()
                self.assertIn('+550+',mover.call_args.args[0])
                texto=d.canvas.itemcget('cuerpo','text');d.posicionar((0,600,200,260))
                self.assertEqual(d.canvas.coords('globo_personaje')[10],92)
                self.assertEqual(d.canvas.itemcget('cuerpo','text'),texto)

    def test_orden_lol_pasa_por_ejecutor_sin_busqueda_web_ni_ia(self):
        with self.capri() as (c,_),patch.object(c.lol,'ejecutar',return_value=MENSAJES['buscando']) as ejecutar,patch('app.ejecutar') as web,patch.object(c.ia,'conversar') as ia:
            c.guardar('idioma','pt');c.enviar('busca partida en lol')
            limite=time.monotonic()+2
            while c.ocupada and time.monotonic()<limite:c.poll();time.sleep(.005)
            self.assertFalse(c.ocupada);ejecutar.assert_called_once()
            self.assertEqual(ejecutar.call_args.args[:2],('lol_buscar',''))
            web.assert_not_called();ia.assert_not_called()
            self.assertIn('A busca de partida',c.historial[-1][1])

    def test_activar_vigilancia_guarda_preferencia_y_desactivar_la_detiene(self):
        with self.capri() as (c,ruta),patch.object(c.lol,'activar_auto') as activar,patch.object(c.lol,'detener_auto') as detener:
            import json
            c.enviar('activa la aceptacion automatica del lol');activar.assert_called_once()
            self.assertTrue(json.loads((ruta/'ajustes.json').read_text())['lol_aceptar_automatico'])
            self.assertFalse(c.ocupada)
            c.enviar('no aceptes mas partidas');detener.assert_called_once()
            self.assertFalse(json.loads((ruta/'ajustes.json').read_text())['lol_aceptar_automatico'])

    def test_dos_turnos_playlist_ejecutan_cancion_en_lista_sin_busqueda_global(self):
        with self.capri() as (c,_),patch('playlists.reproducir_cancion_playlist',side_effect=lambda cancion,nombre:'¿Cómo se llama tu playlist?' if not nombre else 'Listo') as reproducir,patch('escritorio.controlar_spotify') as global_spotify:
            # La pregunta del primer turno se produce sin consultar Spotify.
            c.enviar('Reproduce High Forever en mi playlist.')
            limite=time.monotonic()+2
            while c.ocupada and time.monotonic()<limite:c.poll();time.sleep(.005)
            reproducir.assert_called_once_with(cancion='High Forever',nombre='')
            self.assertIn('Cómo se llama',c.historial[-1][1])
            reproducir.reset_mock()
            c.enviar('de la playlist Capri.')
            limite=time.monotonic()+2
            while c.ocupada and time.monotonic()<limite:c.poll();time.sleep(.005)
            self.assertFalse(c.ocupada)
            reproducir.assert_called_once_with(cancion='High Forever',nombre='Capri')
            global_spotify.assert_not_called()
