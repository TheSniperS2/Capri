import io
import json
import time
import unittest
import ast
import re
from pathlib import Path
from unittest.mock import patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from core import IA,limpiar_traduccion
from idiomas import IDIOMAS,texto,ui,catalogo
from voz import elegir_voz,texto_para_voz
from ajustes_ui import BotonCyber


class Idiomas(unittest.TestCase):
    def test_catalogo_no_mezcla_japones_con_ingles_o_portugues(self):
        marcas={' Capri','CAPRI','CAPRI // ','Capri','OK','Opera GX','Preparar Capri.pyw'}
        japones=r'[\u3040-\u30ff\u3400-\u9fff]'
        for origen,valores in catalogo().items():
            self.assertIsNone(re.search(japones,valores[0]+valores[1]),origen)
            if origen not in marcas:self.assertRegex(valores[2],japones,origen)

    def test_catalogo_cubre_etiquetas_visibles_y_preserva_variables(self):
        datos=catalogo()
        for origen,valores in datos.items():
            tokens=sorted(re.findall(r'\{\d+\}',origen))
            self.assertEqual(len(valores),3,origen)
            for valor in valores:self.assertEqual(sorted(re.findall(r'\{\d+\}',valor)),tokens,origen)
        src=Path(__file__).resolve().parents[1]/'src'
        for nombre in ('app.py','ajustes_ui.py','prueba_microfono.py','dialogos.py','entrada.py','menu_radial.py','intro.py','avatar.py'):
            for n in ast.walk(ast.parse((src/nombre).read_text(encoding='utf8'))):
                if isinstance(n,ast.Constant) and isinstance(n.value,str) and re.fullmatch(r'[A-ZÁÉÍÓÚÑ ]{3,}',n.value) and n.value not in ('RGB','RGBA'):
                    self.assertTrue(n.value in datos,(nombre,n.value))
                if isinstance(n,ast.keyword) and n.arg in ('text','label','title') and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
                    s=n.value.value
                    if re.search('[A-Za-zÁÉÍÓÚáéíóúñ]',s) and s not in ('CAPRI','dB'):
                        self.assertIn(s,datos,(nombre,s))

    def test_json_del_traductor_no_se_muestra_como_respuesta(self):
        frase='I resumed the playback that was set on Spotify.'
        for envoltorio in ({'text':frase},{'translation':frase},{'texto':frase}):
            self.assertEqual(limpiar_traduccion(json.dumps(envoltorio)),frase)
        self.assertEqual(limpiar_traduccion('```json\n'+json.dumps({'text':frase})+'\n```'),frase)
        with self.assertRaises(ValueError):limpiar_traduccion('{"status":"done","action":"delete"}')
        with patch('core.urllib.request.urlopen',return_value=io.BytesIO(json.dumps({'message':{'content':json.dumps({'text':frase})}}).encode())):
            self.assertEqual(IA().traducir('Reanudé la reproducción.','en','local:test'),frase)

    def test_traductor_rechaza_marcadores_inventados_o_repetidos(self):
        casos=[('Resultado.','Result.__CAPRI_LITERAL_0__'),
               ('Archivo:\nC:\\Fotos\\foto.png','File: __CAPRI_LITERAL_0__ __CAPRI_LITERAL_1__'),
               ('Archivo:\nC:\\Fotos\\foto.png','File: __CAPRI_LITERAL_0__ __CAPRI_LITERAL_0__')]
        for original,salida in casos:
            with self.subTest(salida=salida),patch('core.urllib.request.urlopen',return_value=io.BytesIO(json.dumps({'message':{'content':json.dumps({'translation':salida})}}).encode())):
                with self.assertRaises(ValueError):IA().traducir(original,'en','local:test')

    def test_prompt_y_stream_respetan_idioma_elegido(self):
        for idioma in ('en','pt','ja'):
            with self.subTest(idioma=idioma):
                mensaje=texto('prueba',idioma)
                archivo=io.BytesIO(json.dumps({'message':{'content':mensaje}}).encode())
                ia=IA();ia.idioma=idioma
                with patch('core.urllib.request.urlopen',return_value=archivo) as red:
                    self.assertEqual(ia.conversar('Háblame en tu idioma','local:test'),mensaje)
                payload=json.loads(red.call_args.args[0].data)
                self.assertIn('Respond ONLY in '+IDIOMAS[idioma][1],payload['messages'][0]['content'])
                self.assertNotIn('y español latino',payload['messages'][0]['content'])
                self.assertEqual(elegir_voz('capri_latina',idioma)[0],IDIOMAS[idioma][3])
                self.assertTrue(texto_para_voz(mensaje))

    def test_traduccion_protege_rutas_no_alimenta_historial_ni_ejecuta(self):
        ruta=r'C:\Fotos\Canción japonesa.png'
        ia=IA()
        resultado='Could not delete:\n__CAPRI_LITERAL_0__'
        with patch('core.urllib.request.urlopen',return_value=io.BytesIO(json.dumps({'message':{'content':resultado}}).encode())) as red,patch('core.subprocess.Popen') as spawn:
            self.assertEqual(ia.traducir('No pude borrar:\n'+ruta,'en','local:test'),'Could not delete:\n'+ruta)
        payload=json.loads(red.call_args.args[0].data)
        self.assertNotIn(ruta,payload['messages'][-1]['content'])
        self.assertEqual(ia.historia,[]);spawn.assert_not_called()
        with patch('core.urllib.request.urlopen',return_value=io.BytesIO(b'{"message":{"content":"Done"}}')):
            with self.assertRaises(ValueError):ia.traducir('No pude borrar:\n'+ruta,'en','local:test')


class DisenoEIdioma(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_eleccion_persistente_respuesta_y_narracion_mismo_idioma(self):
        with self.capri() as (c,carpeta):
            antes={k:c.cfg[k] for k in ('microfono','modelo','modelo_whisper','voz_perfil')}
            c.guardar('idioma','ja');c.cfg['voz']=True
            with patch.object(c.voz,'hablar') as hablar:
                c.enviar('hola');limite=time.monotonic()+2
                while c.ocupada and time.monotonic()<limite:c.root.update();time.sleep(.01)
                self.assertEqual(c.historial[-1],('Capri',texto('saludo','ja')))
                self.assertEqual(hablar.call_args.args[0],texto('saludo','ja'))
            self.assertEqual(c.voz.idioma,'ja');self.assertEqual(c.ia.idioma,'ja')
            for k,v in antes.items():self.assertEqual(c.cfg[k],v)
            self.assertEqual(json.loads((carpeta/'ajustes.json').read_text(encoding='utf8'))['idioma'],'ja')
            c.guardar('idioma','es');self.assertEqual(c.cfg['voz_perfil'],antes['voz_perfil'])

    def test_chat_sin_etiqueta_vacia_y_ventanas_con_margen(self):
        with self.capri() as (c,_):
            c.abrir_chat();c.historial=[('Tú','Una prueba'),('Capri','')];c.pintar_historial();c.panel.update()
            self.assertIn(texto('preparando'),c.chat.get('1.0','end'))
            self.assertTrue(c.marco_historial.find_withtag('marco'))
            self.assertGreaterEqual(c.panel.winfo_x(),32);self.assertGreaterEqual(c.panel.winfo_y(),32)
            c.configurar();c.ajustes.update()
            self.assertGreaterEqual(c.ajustes.winfo_x(),32);self.assertGreaterEqual(c.ajustes.winfo_y(),32)
            def recorrer(w):
                for h in w.winfo_children():
                    if isinstance(h,BotonCyber):self.assertEqual(str(h.cget('bg')),str(h.master.cget('bg')))
                    recorrer(h)
            recorrer(c.ajustes)

    def test_traduccion_fallida_conserva_resultado_real(self):
        with self.capri() as (c,_):
            c.cfg['ia']=True
            with patch.object(c.ia,'traducir',side_effect=ValueError('literal alterado')):
                salida=c.localizar_respuesta('No pude confirmar la reproducción.','pt')
            self.assertIn(texto('sin_traduccion','pt'),salida)
            self.assertIn('No pude confirmar la reproducción.',salida)

    def test_interfaz_cambia_sin_cambiar_identidad_de_opciones(self):
        with self.capri() as (c,_):
            c.abrir_chat();c.configurar();c.guardar('idioma','en');c.ajustes.update()
            self.assertEqual(c.panel_ajustes.titulo.get(),'Desktop')
            c.panel_ajustes.mostrar('Voz');c.root.update()
            self.assertEqual(c.panel_ajustes.titulo.get(),ui('Voz','en'))
            self.assertNotEqual(c.panel_ajustes.titulo.get(),'Voz')
            c.idioma_combo.abrir();c.idioma_combo.popup.update()
            lista=c.idioma_combo.popup_lista
            self.assertEqual(c.idioma_combo.popup_filas,4)
            self.assertEqual(lista.yview()[0],0)
            textos=[lista.itemcget(i,'text') for i in lista.find_all() if lista.type(i)=='text']
            self.assertEqual(textos,['Español','English','Português','日本語'])
            lista.event_generate('<ButtonRelease-1>',x=20,y=19);c.root.update()
            self.assertEqual(c.cfg['idioma'],'es');self.assertEqual(c.panel_ajustes.titulo.get(),'Voz')

    def test_umbral_sin_bloques_y_automatico_sin_slider_innecesario(self):
        with self.capri() as (c,_):
            c.configurar();p=c.panel_prueba
            self.assertEqual(str(p.escala.cget('bg')),str(p.cget('bg')))
            p.automatico.set(True);p.cambiar()
            self.assertFalse(p.escala.winfo_manager())
            p.automatico.set(False);p.cambiar()
            self.assertEqual(p.escala.winfo_manager(),'pack')
            self.assertIsNotNone(c.cfg['umbral_microfono_db'])

    def test_entrada_con_indicacion_sin_flecha_ni_texto_falso(self):
        with self.capri() as (c,_):
            c.abrir_chat();c.panel.update()
            self.assertEqual(c.entrada.get(),'')
            self.assertEqual(c.placeholder_entrada.cget('text'),'Escribe un mensaje…')
            self.assertEqual(c.placeholder_entrada.winfo_manager(),'place')
            self.assertEqual(c.entrada.cget('highlightthickness'),0)
            self.assertEqual(len(c.campo_entrada.find_withtag('corchetes')),2)
            c.guardar('idioma','ja')
            self.assertEqual(c.placeholder_entrada.cget('text'),'メッセージを入力…')

    def test_textos_caben_en_marco_y_globo_tiene_espacio_inferior(self):
        with self.capri() as (c,_):
            c.guardar('idioma','en');c.abrir_chat();c.panel.geometry('420x620');c.panel.update()
            for marco in (c.marco_entrada,c.marco_historial):
                item=next(i for i in marco.find_withtag('marco') if marco.type(i)=='text')
                self.assertLessEqual(marco.bbox(item)[2],marco.winfo_width()-12)
            c.guardar('idioma','ja');c.panel.update()
            c.guardar('idioma','en');c.panel.update()
            texto=next(c.marco_entrada.itemcget(i,'text') for i in c.marco_entrada.find_withtag('marco') if c.marco_entrada.type(i)=='text')
            self.assertTrue(texto.startswith('NEW TRANSMISSION'))
            self.assertLessEqual(c.placeholder_entrada.winfo_rootx()+c.placeholder_entrada.winfo_width(),c.entrada.winfo_rootx()+c.entrada.winfo_width())
            c.dialogo.personaje=lambda:True
            c.dialogo.mostrar("Of course I can — you're right in my earpiece, like a whisper through the neon haze. What's on your mind, spark? 🔊 🫧")
            c.dialogo.visible=c.dialogo.objetivo;c.dialogo.estado='HABLANDO';c.dialogo.dibujar()
            caja=c.dialogo.canvas.bbox('cuerpo')
            self.assertGreaterEqual(c.dialogo.alto_canvas-24-caja[3],20)
            self.assertEqual(c.dialogo.canvas.itemcget(c.dialogo.canvas.find_withtag('estado_globo')[0],'text'),'SPEAKING')

    def test_ancla_tiene_impacto_brazo_levantado_y_agarre_por_delante(self):
        with self.capri() as (c,_):
            p=c.companera;p.redimensionar(1);p.x=300;p.y=100;p.direccion=1
            ahora=time.monotonic();p.estado='sujeta'
            p.ancla={'x':p.x+p.ancho*.23,'y':p.y+p.alto*.27,'inicio':ahora-.1,'hasta':ahora+5,'cuerpo_y':p.y}
            p.dibujar(c.canvas,glitch=False)
            self.assertTrue(c.canvas.find_withtag('impacto_ancla'));self.assertTrue(c.canvas.find_withtag('estaca_clavada'))
            self.assertTrue(c.canvas.find_withtag('agarre_personaje'))
            self.assertGreater(c.canvas.find_withtag('agarre_personaje')[0],c.canvas.find_withtag('personaje')[0])
            pose=next(iter(p.colgadas.values()))[0]
            self.assertNotEqual(pose.tobytes(),p.lienzos[0].tobytes())
            self.assertLessEqual(set(pose.getchannel('A').tobytes()),{0,255})
