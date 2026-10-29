import io
import json
import time
import unittest
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from core import IA
from idiomas import coincide_idioma


class CaidaSinClic(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_foco_de_entrada_oculta_no_detiene_caida(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]),patch('companera.random.random',return_value=1):
            c.cfg['modo_visual']='personaje';p=c.companera;p.redimensionar(1)
            p.posar(500,120);p.proxima_accion=time.monotonic()+100
            c.dialogo.editando=True
            self.assertFalse(c.escribiendo())
            y=p.y;p.ultimo=time.monotonic()-.05;c.dibujar_personaje()
            self.assertGreater(p.y,y)

    def test_soltar_libera_edicion_y_conserva_borrador(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]):
            c.cfg['modo_visual']='personaje';c.companera.redimensionar(1)
            c.entrada_compacta.poner('un borrador');c.dialogo.editando=True
            entrada=c.dialogo.entrada
            c.drag=(0,0,300,100,time.monotonic())
            c._fin_arrastre(Mock(x_root=30,y_root=20))
            self.assertIsNone(c.drag);self.assertFalse(c.dialogo.editando)
            self.assertEqual(entrada.get(),'un borrador')

    def test_edicion_visible_con_foco_sigue_pausando(self):
        with self.capri() as (c,_):
            c.dialogo.editando=True;e=c.dialogo.entrada
            with patch.object(e,'winfo_viewable',return_value=True),patch.object(c.root,'focus_get',return_value=e):
                self.assertTrue(c.escribiendo())

    def test_idioma_corregido_es_el_mismo_que_recibe_la_voz(self):
        with self.capri() as (c,_):
            c.guardar('idioma','pt');c.cfg.update(modelo='local:test',voz=True)
            portuguesa='Oi! Sou a Capri. Como posso ajudar você hoje?'
            with patch('core.urllib.request.urlopen',side_effect=[respuesta('Hello there! How are you today?'),respuesta(json.dumps({'translation':portuguesa}))]),patch.object(c.voz,'hablar') as voz:
                c.enviar('Olá, Capri. Como você está?');limite=time.monotonic()+2
                while c.ocupada and time.monotonic()<limite:c.root.update();time.sleep(.01)
                self.assertFalse(c.ocupada)
                self.assertEqual(c.historial[-1],('Capri',portuguesa))
                self.assertEqual(voz.call_args.args[0],portuguesa)
                self.assertEqual(c.voz.idioma,'pt')


def respuesta(texto):return io.BytesIO(json.dumps({'message':{'content':texto}}).encode('utf8'))

class IdiomaReal(unittest.TestCase):
    def test_detecta_ingles_bajo_voz_portuguesa_sin_rechazar_nombres(self):
        for frase in ('Hello!',"Hey there, what's on your mind?",'Of course I can help you.'):
            self.assertFalse(coincide_idioma(frase,'pt'),frase)
        for frase in ('Olá! Sou a Capri. Como posso ajudar você?','Spotify','High Forever','Oi, vamos conversar?'):
            self.assertTrue(coincide_idioma(frase,'pt'),frase)

    def test_corrige_portugues_antes_de_exponer_texto_y_guardar_historia(self):
        ia=IA();ia.idioma='pt';ia.historia=[{'role':'assistant','content':"Hey, what's up?"}]
        parciales=[];portugues='Oi! Sou a Capri. Como posso ajudar você hoje?'
        stream=io.BytesIO(json.dumps({'message':{'content':"Hey there! How can I help you?"},'done':True}).encode()+b'\n')
        with patch('core.urllib.request.urlopen',side_effect=[stream,respuesta(json.dumps({'translation':portugues}))]) as red:
            self.assertEqual(ia.conversar('Olá, Capri','local:test',al_texto=parciales.append),portugues)
        self.assertEqual(parciales,[portugues]);self.assertEqual(ia.historia[-1]['content'],portugues)
        solicitud=json.loads(red.call_args_list[0].args[0].data)
        self.assertIn('português brasileiro',solicitud['messages'][-2]['content'])

    def test_corrige_tambien_espanol_y_japones(self):
        for idioma,correcta in (('es','Hola, soy Capri. ¿Qué hacemos hoy?'),('ja','こんにちは、カプリだよ。何をしよう？')):
            with self.subTest(idioma=idioma):
                ia=IA();ia.idioma=idioma
                with patch('core.urllib.request.urlopen',side_effect=[respuesta('Hello there! How can I help you?'),respuesta(json.dumps({'translation':correcta}))]):
                    self.assertEqual(ia.conversar('hola','local:test'),correcta)
