import sys
import time
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from intro import Transformacion
from avatar import Avatar
import test_companera_control as fixtures
from test_capri import PruebasTk

class Preparacion(unittest.TestCase):
    def test_pillow_en_worker_y_fotos_solo_en_hilo_de_interfaz(self):
        llamadas=[];principal=threading.get_ident()
        def foto(im):llamadas.append(threading.get_ident());return im
        with patch('intro.ImageTk.PhotoImage',side_effect=foto):
            t=Transformacion(Image.new('RGBA',(320,210)),Image.new('RGBA',(600,400)),Image.new('RGBA',(210,240)),(400,300),(550,400),640,480)
            try:
                fin=time.monotonic()+10
                while time.monotonic()<fin and (len(t.fotos)!=t.cantidad or not all(t.fotos)):
                    t.actualizar();time.sleep(.002)
                self.assertEqual(len(t.fotos),t.cantidad);self.assertTrue(all(t.fotos))
                self.assertTrue(llamadas);self.assertEqual(set(llamadas),{principal})
            finally:t.detener();t.worker.join(1)

class SalidaYFluidez(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_escucha_personaje_muestra_nivel_y_se_oculta_al_terminar(self):
        with self.capri() as (c,_):
            c.cfg['modo_visual']='personaje';c.intro_activa=False;c.transito=None
            c.escuchando=True;c.nivel=0;c.actualizar_indicador_voz();c.root.update_idletasks()
            self.assertNotEqual(c.indicador_voz.state(),'withdrawn')
            barras=c.indicador_canvas.find_withtag('nivel_escucha')
            bajo=c.indicador_canvas.coords(barras[2])
            c.nivel=1;c.actualizar_indicador_voz()
            alto=c.indicador_canvas.coords(c.indicador_canvas.find_withtag('nivel_escucha')[2])
            self.assertGreater(alto[3]-alto[1],bajo[3]-bajo[1])
            c.escuchando=False;c.actualizar_indicador_voz()
            self.assertEqual(c.indicador_voz.state(),'withdrawn')
            c.escuchando=True;c.cfg['modo_visual']='pantalla';c.actualizar_indicador_voz()
            self.assertEqual(c.indicador_voz.state(),'withdrawn')

    def test_retorno_no_amplia_ni_pasa_por_pose_gigante(self):
        with self.capri() as (c,_):
            c.cfg['modo_visual']='personaje';c.aplicar_escala(inicial=True)
            c.guardar('modo_visual','pantalla');t=c.transito['morfosis']
            self.assertTrue(t.directa);self.assertLess(c.transito['duracion'],1)
            for q in (0,.25,.5,.75,1):self.assertLessEqual(t.geometria(q)[1][0],360*c.cfg['escala_avatar'])

    def test_indicador_pensando_no_desborda_y_no_muestra_barra_suelta(self):
        with self.capri() as (c,_):
            c.cfg['modo_visual']='personaje';d=c.dialogo
            d.preparar_voz('Hola, choom.',estado='GENERANDO RESPUESTA');d.dibujar()
            self.assertEqual(d.canvas.itemcget(d.canvas.find_withtag('estado_globo')[0],'text'),'PENSANDO')
            self.assertEqual(d.canvas.itemcget(d.canvas.find_withtag('cuerpo')[0],'text'),'')
            self.assertEqual(len(d.canvas.find_withtag('pensando')),3)

    def test_cierre_senala_estrella_y_destruye_la_aplicacion(self):
        with self.capri() as (c,_):
            c.animacion_cierre=True;c.cerrar()
            self.assertTrue(c.saliendo);self.assertFalse(c.cerrado)
            self.assertTrue(c.canvas.find_withtag('capri_al_centro'));self.assertTrue(c.canvas.find_withtag('estrella'))
            from despedida import DURACION
            c.inicio_salida=time.monotonic()-DURACION-.1;c.pintar_despedida();self.assertTrue(c.cerrado)

    def test_f8_durante_despedida_cierra_sin_reabrir_microfono(self):
        with self.capri() as (c,_),patch.object(c,'hablar') as hablar:
            c.animacion_cierre=True;c.cerrar();c.eventos.put(('micro',None));c.poll()
            self.assertTrue(c.cerrado);hablar.assert_not_called()

    def test_mano_centrada_desaparece_y_rayo_viaja_hasta_estrella(self):
        with self.capri() as (c,_):
            c.animacion_cierre=True;c.cerrar();s=c.salida
            self.assertEqual(s.destino[0],s.ancho/2)
            s.dibujar(c.canvas,.5)
            self.assertTrue(c.canvas.find_withtag('mano_despedida'))
            self.assertEqual(c.canvas.itemcget(c.canvas.find_withtag('mano_despedida')[0],'fill'),'#f60031')
            self.assertLess(c.canvas.coords(c.canvas.find_withtag('mano_despedida')[0])[0],s.destino[0])
            self.assertGreater(c.canvas.bbox('mano_despedida')[3],s.alto+30)
            self.assertFalse(c.canvas.find_withtag('descarga'))
            s.dibujar(c.canvas,.82)
            self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            self.assertTrue(c.canvas.find_withtag('descarga'))
            lejos=c.canvas.bbox('descarga')[1]
            s.dibujar(c.canvas,.875)
            self.assertLess(c.canvas.bbox('descarga')[1],lejos)
            self.assertTrue(c.canvas.find_withtag('estrella'))

    def test_despedida_electrica_y_estrella_se_apagan_antes_del_cierre(self):
        with self.capri() as (c,_):
            from despedida import Despedida
            s=Despedida(1920,1080,(1700,880))
            s.dibujar(c.canvas,.76)
            self.assertTrue(c.canvas.find_withtag('descarga'))
            bbox=c.canvas.bbox('descarga')
            self.assertGreater(bbox[2]-bbox[0],50)
            self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            s.dibujar(c.canvas,.88);antes=c.canvas.bbox('estrella')
            s.dibujar(c.canvas,.97);despues=c.canvas.bbox('estrella')
            self.assertLess(despues[2]-despues[0],(antes[2]-antes[0])/2)
            self.assertFalse(c.canvas.find_withtag('descarga'))
            s.dibujar(c.canvas,1)
            self.assertFalse(c.canvas.find_withtag('estrella'))

    def test_capri_llega_al_centro_antes_de_formar_la_mano(self):
        with self.capri() as (c,_):
            from despedida import Despedida
            s=Despedida(1920,1080,(1700,880),c.avatar.fotos[0])
            s.dibujar(c.canvas,0)
            self.assertEqual(c.canvas.coords('capri_al_centro'),[1700,880])
            s.dibujar(c.canvas,.09)
            self.assertTrue(c.canvas.find_withtag('fragmento_formacion'))
            self.assertFalse(c.canvas.find_withtag('descarga'))
            self.assertFalse(c.canvas.find_withtag('capri_al_centro'))
            self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            s.dibujar(c.canvas,.18)
            self.assertTrue(c.canvas.find_withtag('fragmento_formacion'))
            # La imagen de origen nunca vuelve a aparecer después de salir.
            for p in (.02,.09,.175,.18,.21,.23,.28,.5,.69,.84):
                s.dibujar(c.canvas,p)
                self.assertFalse([i for i in c.canvas.find_all() if c.canvas.type(i)=='image'])
            s.dibujar(c.canvas,.33)
            self.assertFalse(c.canvas.find_withtag('capri_al_centro'))
            self.assertTrue(c.canvas.find_withtag('mano_despedida'))

    def test_punta_llega_a_estrella_antes_de_ser_absorbida(self):
        with self.capri() as (c,_):
            from despedida import Despedida
            s=Despedida(1920,1080,(1700,880))
            distancias=[]
            for p in (.75,.83,.87,.88,.90):
                s.dibujar(c.canvas,p)
                punta=c.canvas.coords('punta_estrella')
                self.assertEqual(len(punta),4)
                x=(punta[0]+punta[2])/2;y=(punta[1]+punta[3])/2
                distancias.append(((x-s.destino[0])**2+(y-s.destino[1])**2)**.5)
            self.assertEqual(distancias,sorted(distancias,reverse=True))
            self.assertAlmostEqual(distancias[-2],0)
            self.assertAlmostEqual(distancias[-1],0)

    def test_avatar_hd_tiene_fuente_mayor_que_tamano_del_zoom(self):
        with self.capri() as (c,_):
            assets=Path(__file__).resolve().parents[1]/'assets'
            avatar=Avatar(assets/'capri-base-v2.png');self.assertTrue(avatar.estados_hd)
            self.assertGreaterEqual(avatar.estados_hd[0].width,1000)
            avatar.redimensionar(1.6)
            self.assertEqual(avatar.fotos[0].width(),512);self.assertEqual(avatar.fotos[0].height(),336)
