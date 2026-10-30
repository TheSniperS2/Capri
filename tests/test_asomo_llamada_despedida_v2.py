import time
from types import SimpleNamespace
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from voz import Voz,elegir_voz
from idiomas import ui


class InteraccionesV2(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_asomo_tres_bordes_recortados_click_no_lo_cierra_arrastre_si(self):
        with self.capri() as (c,_):
            for borde in ('izquierda','derecha','abajo'):
                with patch('asomo.random.choice',return_value=borde),patch('ventanas.area_trabajo',return_value=(0,0,1920,1040)):
                    c.iniciar_asomo();a=c.asomo['curioso'];a.dibujar(a.inicio+1)
                if borde=='izquierda':self.assertEqual(a.x,0);self.assertEqual(a.w,183)
                if borde=='derecha':self.assertEqual(a.x+a.w,1920);self.assertEqual(a.w,183)
                if borde=='abajo':self.assertEqual(a.y+a.h,1040);self.assertEqual(a.h,224)
                self.assertTrue(all(0<x<a.w and 0<y<a.h for x,y in a.ojos))
                self.assertTrue(a.dibujar(a.inicio+120))
                e=SimpleNamespace(x_root=600,y_root=400,x=30,y=30)
                c._inicio_arrastre(e);c._fin_arrastre(e);self.assertIs(c.asomo['curioso'],a)
                c._inicio_arrastre(e);c._arrastrar(SimpleNamespace(x_root=650,y_root=450))
                self.assertIsNone(c.asomo);self.assertIsNotNone(c.drag)
                c._fin_arrastre(SimpleNamespace(x_root=650,y_root=450,x=30,y=30))

    def test_subtitulos_invitado_dentro_llamada_sin_globo_con_y_sin_voz(self):
        with self.capri() as (c,_),patch('ventanas.mostrar_no_activar'),patch.object(c.voz,'hablar'):
            for voz in (False,True):
                c.cfg['voz']=voz;c.llamar_capri(invitado='roman');ll=c.llamada_ui
                ll.aceptar();c.revisar_interacciones()
                self.assertTrue(ll.transcripcion);self.assertGreater(ll.h,124)
                self.assertEqual(c.dialogo.objetivo,'')
                if voz:
                    alto_inicial=ll.h;posicion=(ll.x,ll.y,ll.w)
                    c.eventos.put(('voz',(c.voz.generacion,('avance_voz',(ll.transcripcion,15,True)))));c.poll()
                    self.assertEqual(ll.texto_visible,ll.transcripcion[:15]);self.assertFalse(c.boca_activa)
                    self.assertEqual(ll.h,alto_inicial)
                    c.eventos.put(('voz',(c.voz.generacion,('avance_voz',(ll.transcripcion,len(ll.transcripcion),True)))));c.poll()
                    self.assertGreater(ll.h,alto_inicial);self.assertEqual((ll.x,ll.y,ll.w),posicion)
                    caja=ll.c.bbox('subtitulo_llamada');self.assertLess(caja[3],ll.h-10)
                else:self.assertEqual(ll.texto_visible,ll.transcripcion)
                ll.dibujar();self.assertTrue(ll.c.find_withtag('subtitulo_llamada'))
                ll.rechazar();c.voz_ticket=None;c.hablando=False

    def test_invitado_siempre_usa_su_voz_aunque_natural_desactivada_y_no_suplanta_al_fallar(self):
        nombres=[]
        class Sintesis:
            def __init__(self,texto,nombre,**kw):nombres.append(nombre)
            async def stream(self):yield {'type':'audio','data':b'fixture'}
        v=Voz(Mock());v.idioma='es';v.acento='pt-BR'
        with patch('edge_tts.Communicate',Sintesis),patch.object(v,'_reproducir_archivo',return_value=True),patch.object(v,'_reproducir_windows') as windows:
            v._hablar('Roman.',False,v.generacion,v.cancelar,invitado='roman')
            self.assertEqual(nombres,['es-MX-DaliaNeural']);windows.assert_not_called()
        with patch('edge_tts.Communicate',side_effect=RuntimeError('sin red')),patch.object(v,'_reproducir_windows') as windows:
            v._hablar('Roman.',False,v.generacion,v.cancelar,invitado='roman');windows.assert_not_called()
        self.assertEqual(v.acento,'pt-BR')

    def test_despedida_localizada_rostro_antes_mano_sin_voz(self):
        from despedida_camara import TRASLADO
        self.assertEqual(ui('Nos vemos.','en'),"I'll see you around.")
        with self.capri() as (c,_):
            opacidad=float(c.root.attributes('-alpha'))
            c.iniciar_despedida();self.assertTrue(c.canvas.find_withtag('fragmento_viaje'))
            c.inicio_salida=time.monotonic()-TRASLADO-.1;c.pintar_despedida()
            self.assertTrue(c.canvas.find_withtag('rostro_despedida'))
            self.assertTrue(c.canvas.find_withtag('marco_grabacion'))
            self.assertAlmostEqual(float(c.root.attributes('-alpha')),opacidad)
            self.assertFalse(hasattr(c,'intro_alpha'))
            self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            c.inicio_salida=time.monotonic()-TRASLADO-1.8-4.4*.5;c.pintar_despedida()
            self.assertTrue(c.canvas.find_withtag('mano_despedida'))

    def test_asomo_persistente_no_impide_siguiente_llamada_automatica(self):
        with self.capri() as (c,_),patch('ventanas.mostrar_no_activar'),patch.object(c.juego,'tick',return_value='llamada') as tick:
            c.iniciar_asomo();self.assertIsNotNone(c.asomo)
            c.revisar_interacciones();self.assertFalse(tick.call_args.args[1])
            self.assertIsNone(c.asomo);self.assertIsNotNone(c.llamada_ui)
