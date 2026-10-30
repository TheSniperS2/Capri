import time
import threading
from unittest.mock import patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from travesuras import Travesuras


class Movimiento(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def personaje(self,c):
        c.guardar('modo_visual','personaje');c.transito['inicio']-=c.transito['duracion']+.1;c.animar()

    def test_quieta_no_camina_y_solo_solicita_viaje_con_rayo(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]):
            p=c.companera;p.redimensionar(1);p.iniciar();p.x=400;p.direccion=1
            self.assertEqual(len(p.pasos_tk),0);imagenes=list(p.fotos)
            inicio=p.x;ahora=p.ultimo
            for i in range(60):p.tick(ahora=ahora+(i+1)/60)
            self.assertEqual(p.x,inicio);self.assertEqual(p.estado,'quieta')
            p.proxima_accion=ahora;p.tick(ahora=ahora+1.1)
            self.assertIsNotNone(p.salto);self.assertEqual(p.x,inicio)
            x=p.x;fase=p.fase_paso;p.tick(pausa=True,ahora=p.ultimo+.02)
            self.assertEqual(p.x,x);self.assertEqual(p.fase_paso,fase)
            p.redimensionar(1);self.assertEqual(p.fotos,imagenes)

    def test_salto_usa_estela_y_llega_a_esquina_sin_dejar_overlay(self):
        ventana={'id':7,'titulo':'Prueba','rect':(144,404,900,800)}
        with self.capri() as (c,_),patch('companera.visibles',return_value=[ventana]):
            self.personaje(c);p=c.companera
            p.salto={'inicio':time.monotonic(),'x':p.x,'y':p.y,'destino':(50,250),'id':7,'izquierda':100,'lado':'izquierda'}
            c.dibujar_personaje();self.assertIsNotNone(c.transito);self.assertTrue(c.canvas.find_withtag('fragmento_viaje'))
            self.assertFalse(c.canvas.find_withtag('descarga'))
            c.transito['inicio']-=c.transito['duracion']+.1;c.animar()
            self.assertIsNone(c.transito);self.assertFalse(hasattr(c,'intro_estilo'))
            self.assertEqual(int(c.canvas.cget('width')),p.ancho)

    def test_transformacion_mantiene_imagen_al_crecer_y_encogerse(self):
        with self.capri() as (c,_):
            c.guardar('modo_visual','personaje')
            self.assertIsNotNone(c.transito.get('morfosis'))
            c.transito['inicio']=time.monotonic()-.6
            c.dibujar_transito();self.assertTrue(c.canvas.find_withtag('morfosis_capri'))
            c.transito['inicio']=time.monotonic()-c.transito['duracion']*.78
            c.dibujar_transito();self.assertTrue(c.canvas.find_withtag('morfosis_capri'))
            c.interrumpir();self.assertIsNone(c.transito)
            self.assertFalse(hasattr(c,'intro_estilo'))

    def test_entrada_lateral_no_aumenta_la_superficie_del_personaje(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]):
            self.personaje(c);ancho=c.canvas.cget('width');alto=c.canvas.cget('height')
            c.entrada_compacta.dar_foco()
            self.assertFalse(c.entrada_compacta.winfo_manager())
            self.assertIs(c.entrada_lateral.master,c.ventana_entrada)
            self.assertEqual(c.canvas.cget('width'),ancho);self.assertEqual(c.canvas.cget('height'),alto)
            c.interrumpir();self.assertEqual(c.ventana_entrada.state(),'withdrawn')

    def test_respuesta_caduca_tres_segundos_despues_de_voz_y_no_durante(self):
        with self.capri() as (c,_):
            d=c.dialogo;d.preparar_voz('Hola, choom.');d.vence=time.monotonic()-1;d.tick()
            self.assertNotEqual(d.ventana.state(),'withdrawn')
            d.terminar_voz();self.assertLessEqual(d.vence-time.monotonic(),3)
            d.vence=time.monotonic()-1;d.tick();self.assertEqual(d.ventana.state(),'withdrawn')
            d.mostrar('Corto');d.visible=d.objetivo;d.tick();self.assertLessEqual(d.vence-time.monotonic(),3)
            d.editando=True;d.vence=time.monotonic()-1;d.tick();self.assertEqual(d.ventana.state(),'withdrawn')

    def test_interacciones_tienen_cadencia_y_solo_eventos_nuevos(self):
        reloj=[100.];j=Travesuras(lambda:reloj[0])
        with patch('travesuras.random.choice',side_effect=lambda opciones:opciones[-1]):
            self.assertIsNone(j.tick(True,False))
            reloj[0]=1001;self.assertIsNone(j.tick(True,True))
            self.assertEqual(j.tick(True,False,asomos=True,personaje=True),'asomar')
            self.assertGreater(j.proxima,reloj[0]+700)
        self.assertFalse(hasattr(j,'comenzar'));self.assertFalse(hasattr(j,'tocar'))

    def test_travesura_manual_de_apps_tambien_exige_permiso(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]),patch('app.ejecutar') as ejecutar:
            self.personaje(c);c.hacer_travesura('pestana');ejecutar.assert_not_called()

    def test_permiso_antiguo_no_permite_abrir_pestanas_ni_documentos(self):
        with self.capri() as (c,_),patch('companera.visibles',return_value=[]):
            self.personaje(c);c.cfg['travesuras_apps']=True
            with patch('app.ejecutar') as ejecutar:
                c.hacer_travesura('pestana');c.hacer_travesura('carpeta');ejecutar.assert_not_called()
