import time
from types import SimpleNamespace
from unittest.mock import Mock,patch
import tkinter as tk
from test_capri import PruebasTk
import test_companera_control as fixtures


class PersonajeLlamadas(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def personaje(self,c):
        c.cfg['modo_visual']='personaje';c.companera.redimensionar(1);c.companera.iniciar()

    def test_pose_sentada_mira_hacia_fuera_en_los_dos_bordes(self):
        with self.capri() as (c,_),patch('companera.area_trabajo',return_value=(0,0,1200,900)):
            self.personaje(c);p=c.companera;v={'id':7,'rect':(250,400,900,700),'titulo':'Prueba'}
            p.soporte=7;p.soporte_dx=0
            for lado,direccion in (('izquierda',-1),('derecha',1)):
                p.soporte_lado=lado;p.revisar=0
                with patch('companera.visibles',return_value=[v]):p.tick(pausa=True,ahora=p.ultimo+1)
                self.assertEqual(p.direccion,direccion);p.dibujar(c.canvas,glitch=False,halo='ninguno')
                self.assertIs(p.imagen,(p.espejos if lado=='izquierda' else p.fotos)[3])
            p.x=260;p.orientar_sentada(v,'libre');self.assertEqual(p.direccion,-1)
            p.x=750;p.orientar_sentada(v,'libre');self.assertEqual(p.direccion,1)

    def test_llamada_pausa_regreso_asomo_y_salto_pendiente(self):
        with self.capri() as (c,_),patch.object(c,'salto_juego') as salto,patch.object(c,'iniciar_transito') as transito:
            self.personaje(c);p=c.companera;c.llamada_ui=Mock(cerrada=False,conectada=False)
            c.asomo={'hasta':time.monotonic()-2,'volver':(400,500)};p.salto={'inicio':0}
            with patch.object(p,'tick') as tick:
                c.dibujar_personaje();self.assertTrue(tick.call_args.kwargs['pausa'])
            salto.assert_not_called();transito.assert_not_called();self.assertIsNotNone(c.asomo)
            c.llamada_ui.cerrada=True;c.dibujar_personaje();salto.assert_called_once_with((400,500))

    def test_arrastre_fuerza_glitch_en_pantalla_y_personaje_y_respeta_opcion(self):
        with self.capri() as (c,_),patch.object(c.root,'geometry'),patch.object(c.dialogo,'posicionar'):
            for modo in ('pantalla','personaje'):
                c.cfg['modo_visual']=modo;c.companera.redimensionar(1)
                senal=c.avatar if modo=='pantalla' else c.companera
                c.drag=(100,100,200,200,0);senal.glitch_hasta=0
                c._arrastrar(SimpleNamespace(x_root=140,y_root=130))
                self.assertGreater(senal.glitch_hasta,time.monotonic())
                c.cfg['efecto_glitch']=False;senal.glitch_hasta=0
                c._arrastrar(SimpleNamespace(x_root=150,y_root=140));self.assertEqual(senal.glitch_hasta,0)
                c.cfg['efecto_glitch']=True
            c.drag=None

    def test_globo_personaje_no_reaparece_tras_colgar_y_otro_traslado(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar'),patch('companera.visibles',return_value=[]):
            self.personaje(c);c.cfg['voz']=True;c.llamar_capri();c.llamada_ui.aceptar();c.revisar_interacciones()
            c.eventos.put(('voz',(c.voz.generacion,True)));c.poll()
            c.eventos.put(('voz',(c.voz.generacion,False)));c.poll()
            self.assertTrue(c.llamada_ui.cerrada);self.assertEqual(c.dialogo.objetivo,'')
            self.assertFalse(c.dialogo.sincronizada);self.assertEqual(c.dialogo.ventana.state(),'withdrawn')
            with patch.object(c.dialogo.ventana,'deiconify') as abrir:
                p=c.companera;c.transito={'tipo':'salto','salto':{'destino':(300,400),'id':0,'izquierda':300,'x':p.x}}
                c.finalizar_transito();abrir.assert_not_called()

    def test_llamada_espera_a_terminar_traslado_antes_de_mostrar_aviso(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta):
            c.transito={'tipo':'salto'}
            with patch.object(c.root,'after') as after:
                c.llamar_capri();self.assertIsNone(c.llamada_ui)
                callback=after.call_args.args[1]
            c.transito=None;callback();self.assertIsNotNone(c.llamada_ui)
