import time
from pathlib import Path
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from travesuras import Travesuras
import tkinter as tk


class Interacciones(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_cadencia_no_interrumpe_ni_acumula_llamadas(self):
        reloj=[0.];j=Travesuras(lambda:reloj[0])
        self.assertIsNone(j.tick(True,False));reloj[0]=901
        self.assertIsNone(j.tick(True,True));self.assertLess(j.proxima,reloj[0])
        with patch('travesuras.random.uniform',return_value=1),patch('travesuras.random.choice',return_value='llamada'):
            self.assertEqual(j.tick(True,False),'llamada')
            self.assertEqual(j.proxima,1801)
            self.assertIsNone(j.tick(True,False))
        reloj[0]=2000;self.assertIsNone(j.tick(False,False))

    def test_eventos_activables_y_frases_no_repetidas(self):
        j=Travesuras(lambda:1000);j.proxima=0
        self.assertIsNone(j.tick(False,False,asomos=True,personaje=False))
        with patch('travesuras.random.choice',side_effect=lambda x:x[-1]):
            self.assertEqual(j.tick(False,False,asomos=True,personaje=True),'asomar')
            primera=j.frase();self.assertNotEqual(j.frase(),primera)

    def test_mas_y_juegos_eliminan_opciones_antiguas(self):
        with self.capri() as (c,_):
            c.abrir_menu_radial(Mock(x_root=500,y_root=300));opciones=dict(c.radial.opciones)
            mas=[t for t,_ in opciones['Más']]
            self.assertNotIn('Escribir',mas);self.assertNotIn('Repetir intro',mas);self.assertNotIn('Pausar viajes',mas)
            self.assertIn('Simular llamada',mas);c.cerrar_radial()
            c.cfg['modo_visual']='personaje';c.companera.redimensionar(1);c.abrir_menu_radial(Mock(x_root=500,y_root=300))
            juegos=[t for t,_ in dict(c.radial.opciones)['Juegos']]
            self.assertNotIn('Atrápame',juegos)
            self.assertIn('Activar asomos automáticos',juegos)

    def test_simulacion_muestra_llamada_y_respuesta_tiene_contexto_sin_efectos(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch('ventanas.minimizar_travesura') as minimizar,patch('app.ejecutar') as ejecutar:
            c.respuesta_stop.set();c.llamar_capri()
            llamada=c.llamada_ui;self.assertFalse(llamada.cerrada)
            self.assertTrue(llamada.c.find_withtag('contestar'))
            self.assertTrue(llamada.c.find_withtag('rechazar'))
            llamada.aceptar();llamada.aceptar()
            c.revisar_interacciones()
            self.assertEqual(len(c.ia.historia),1)
            self.assertEqual(c.ia.historia[-1]['role'],'assistant');self.assertFalse(c.respuesta_stop.is_set())
            self.assertEqual(c.historial[-1][0],'Capri');minimizar.assert_not_called();ejecutar.assert_not_called()

    def test_minimizar_exige_opcion_y_llamada_ofrece_restaurar(self):
        ventana={'id':123,'pid':42,'titulo':'Ventana de prueba'}
        with self.capri() as (c,_),patch('ventanas.activa',return_value=ventana),patch('ventanas.minimizar_travesura',return_value=True) as minimizar,patch('ventanas.restaurar_travesura') as restaurar,patch('llamadas.LlamadaCapri') as llamada:
            c.hacer_travesura('minimizar');minimizar.assert_not_called()
            c.cfg['bromas_ventanas']=True;c.hacer_travesura('minimizar')
            minimizar.assert_called_once_with(ventana)
            self.assertIsNotNone(llamada.call_args.kwargs['restaurar'])
            llamada.call_args.args[2](False)
            restaurar.assert_called_once_with(ventana,False)
            self.assertIsNone(c.ventana_broma)

    def test_rechazar_o_expirar_no_hablan(self):
        from llamadas import LlamadaCapri
        root=tk.Tk();root.withdraw()
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        try:
            with patch('llamadas.tk.Toplevel',Oculta):
                aceptar=Mock();terminar=Mock();l=LlamadaCapri(root,aceptar,terminar)
                l.inicio=time.monotonic()-21;l.dibujar()
                self.assertTrue(l.cerrada);aceptar.assert_not_called();terminar.assert_called_once_with(False)
        finally:root.destroy()

    def test_asomo_va_a_esquina_y_prepara_regreso_con_llamada(self):
        with self.capri() as (c,_),patch('ventanas.area_trabajo',return_value=(0,0,1000,800)),patch.object(c,'salto_juego') as salto,patch.object(c,'llamar_capri') as llamada:
            c.cfg['modo_visual']='personaje';c.companera.redimensionar(1)
            c.hacer_travesura('asomar')
            x,y=salto.call_args.args[0]
            self.assertIn(x,(8,1000-c.companera.ancho-8))
            self.assertIn(y,(8,800-c.companera.alto*.48))
            self.assertGreater(c.asomo['hasta'],time.monotonic())
            self.assertEqual(c.asomo['volver'][1],800-c.companera.alto)
            llamada.assert_called_once_with('asomar')

    def test_apagado_sin_retrato_ni_lectura_de_imagenes(self):
        with self.capri() as (c,base),patch('apagado.SecuenciaApagado') as secuencia,patch.object(c.control_pc,'apagar_ahora') as apagar,patch('app.Image.open') as imagen:
            c.iniciar_apagado_animado(previa=True)
            self.assertEqual(len(secuencia.call_args.args),3)
            self.assertTrue(secuencia.call_args.kwargs['previa']);apagar.assert_not_called();imagen.assert_not_called()
