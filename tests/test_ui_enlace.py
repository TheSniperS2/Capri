from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
from tkinter import font as tkfont
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import app

class Enlace(PruebasTk):
    def test_texto_largo_no_invade_etiqueta_y_cabe_en_panel_pequeno(self):
        with self.capri() as (c,_):
            c.root.update_idletasks()
            pregunta='Podrías contarme una historia muy larga ' * 30
            respuesta=('¡Claro! 😏 Hace un tiempo. ' * 60)+'fin'
            c.dialogo.recibir_usuario(pregunta);c.dialogo.mostrar(respuesta)
            c.dialogo.visible=c.dialogo.objetivo
            c.dialogo.canvas.configure(width=280);c.root.update_idletasks();c.dialogo.dibujar()
            cv=c.dialogo.canvas;cab=cv.bbox('pregunta');cuerpo=cv.bbox('cuerpo')
            self.assertLess(cab[3],44)
            self.assertGreaterEqual(cuerpo[1],75)
            self.assertLess(cuerpo[3],c.dialogo.alto_canvas-12)
            texto=cv.itemcget(cv.find_withtag('cuerpo')[0],'text')
            self.assertLessEqual(len(texto.splitlines()),6)
            self.assertTrue(texto.endswith('fin'));self.assertEqual(c.dialogo.usuario,pregunta)

    def test_intro_centrada_luego_rayo_y_restaura_tamano_y_entrada(self):
        with self.capri() as (c,_):
            c.iniciar_intro();c.root.update_idletasks()
            self.assertGreater(c.escala_avatar,c.cfg['escala_avatar'])
            self.assertFalse(c.entrada_compacta.winfo_manager())
            c.inicio_intro=time.monotonic()-1;c.animar()
            textos=[c.canvas.itemcget(i,'text') for i in c.canvas.find_all() if c.canvas.type(i)=='text']
            self.assertIn('CONECTANDO',textos)
            c.inicio_intro=time.monotonic()-2.2;c.animar()
            self.assertTrue(c.intro_en_viaje)
            self.assertTrue(c.canvas.find_withtag('descarga'))
            self.assertTrue(c.canvas.find_withtag('fragmento_capri'))
            self.assertTrue(all(c.canvas.type(i) in ('line','polygon','image') for i in c.canvas.find_all()))
            c.parar();self.assertEqual(c.escala_avatar,c.cfg['escala_avatar'])
            self.assertEqual(c.entrada_compacta.winfo_manager(),'pack')
            self.assertIsNone(c.fragmentos_intro)
            c.animar();self.assertEqual(float(c.root.attributes('-alpha')),1.0)

    @contextmanager
    def capri(self):
        with tempfile.TemporaryDirectory() as d,patch.object(app,'BASE',Path(d)),patch.object(app.Voz,'parar'):
            assets=Path(d)/'assets';assets.mkdir()
            fuente=Path(__file__).resolve().parents[1]/'assets'
            for nombre in ('capri-base-v2.png','capri-bocas-v2.png'):shutil.copy2(fuente/nombre,assets/nombre)
            c=app.Capri(hotkeys=False);c.root.withdraw();c.cfg['voz']=False
            try:yield c,Path(d)
            finally:c.cerrar()

    def test_entrada_solo_debajo_de_avatar_y_dialogo_sin_controles_ni_fondo_exterior(self):
        with self.capri() as (c,_):
            self.assertFalse(hasattr(c,'b_mic'))
            self.assertIs(c.entrada_compacta.master,c.root)
            self.assertIs(c.dialogo.entrada,c.entrada_compacta.entrada)
            c.poner_chat('Capri','Una respuesta breve.')
            c.dialogo.visible=c.dialogo.objetivo;c.dialogo.dibujar()
            textos=[c.dialogo.canvas.itemcget(i,'text') for i in c.dialogo.canvas.find_all() if c.dialogo.canvas.type(i)=='text']
            self.assertNotIn('HISTORIAL',' '.join(textos));self.assertNotIn('DETENER',' '.join(textos))
            self.assertEqual(c.dialogo.canvas.cget('bg'),app.TRANS)
            if os.name=='nt':self.assertEqual(str(c.dialogo.ventana.wm_attributes('-transparentcolor')),app.TRANS)
            self.assertEqual(tkfont.Font(root=c.root,font=('Chakra Petch',12)).actual()['family'],'Chakra Petch')

    def test_tamano_persistente_y_reescala_imagen_sin_cambiar_modelos(self):
        with self.capri() as (c,p):
            self.assertEqual(c.cfg['modelo_whisper'],'base');self.assertEqual(c.cfg['reconocimiento'],'mixto')
            c.guardar('modelo_whisper','small');c.guardar('escala_avatar',1.25)
            self.assertEqual(c.avatar.fotos[0].width(),400)
            self.assertEqual(int(c.canvas.cget('width')),450)
            datos=json.loads((p/'ajustes.json').read_text())
            self.assertEqual(datos['escala_avatar'],1.25);self.assertEqual(datos['modelo_whisper'],'small')
            c.guardar('escala_avatar',999);self.assertEqual(c.escala_avatar,1.6)

    def test_intro_termina_y_puede_interrumpirse_sin_capturar_microfono(self):
        with self.capri() as (c,_),patch.object(c.micro,'escuchar') as escuchar:
            c.iniciar_intro();c.inicio_intro=time.monotonic()-.7;c.animar()
            self.assertTrue(c.intro_activa)
            c.inicio_intro=time.monotonic()-3;c.animar();self.assertFalse(c.intro_activa)
            c.iniciar_intro();c.parar();self.assertFalse(c.intro_activa)
            escuchar.assert_not_called()

    def test_no_se_pierde_texto_si_la_peticion_es_rechazada_por_ocupada(self):
        with self.capri() as (c,_):
            enviar=Mock(return_value=False);c.entrada_compacta.enviar=enviar
            c.entrada_compacta.poner('Lo que estoy escribiendo')
            c.entrada_compacta.enviar_actual()
            self.assertEqual(c.entrada_compacta.entrada.get(),'Lo que estoy escribiendo')
            enviar.return_value=None;c.entrada_compacta.enviar_actual()
            self.assertEqual(c.entrada_compacta.entrada.get(),'')

    def test_elegir_whisper_activa_el_perfil_y_no_deja_vosk_en_uso(self):
        with self.capri() as (c,_),patch.object(app,'listar_microfonos',return_value=[]),patch.object(app.IA,'modelos',return_value=[]):
            c.cfg['reconocimiento']='rapido';c.configurar()
            c.whisper_combo.current(0);c.whisper_combo.event_generate('<<ComboboxSelected>>')
            c.root.update()
            self.assertEqual(c.cfg['modelo_whisper'],'base')
            self.assertEqual(c.cfg['reconocimiento'],'mixto')

    def test_la_intro_no_bloquea_la_activacion_y_el_nombre_la_interrumpe(self):
        with self.capri() as (c,_):
            iniciado=threading.Event();terminar=threading.Event()
            def escuchar(*a,**kwargs):iniciado.set();terminar.wait(2);return None
            with patch.object(c.micro,'esperar_activacion',side_effect=escuchar):
                try:
                    c.activacion_permitida=True;c.iniciar_intro();c.mantener_activacion()
                    self.assertTrue(iniciado.wait(1));self.assertTrue(c.intro_activa)
                    c.eventos.put(('nombre_detectado',c.activacion_ticket));c.poll()
                    self.assertFalse(c.intro_activa);self.assertTrue(c.escuchando)
                finally:
                    terminar.set()
                    if c.activacion_hilo:c.activacion_hilo.join(1)
                    c.activacion_permitida=False
