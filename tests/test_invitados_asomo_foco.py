import ctypes,os,time,tkinter as tk
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from voz import Voz
from ventanas import preparar_no_activar,mostrar_no_activar


class NuevasInteracciones(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_aviso_se_aplaza_en_juego_y_solo_aparece_al_salir(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta):
            with patch('escritorio.proteger_foco',return_value=True),patch.object(c.root,'after') as after:
                c.llamar_capri();c.llamar_capri()
                self.assertIsNone(c.llamada_ui);after.assert_called_once()
                self.assertEqual(after.call_args.args[0],2000);reintentar=after.call_args.args[1]
            reintentar();self.assertIsNotNone(c.llamada_ui);self.assertFalse(c.llamada_aplazada)

    def test_invitado_habla_con_nombre_y_voz_propios_luego_reacciona_capri(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar') as hablar:
            c.cfg['voz']=True;config=dict(c.cfg);c.llamar_capri(invitado='roman')
            self.assertEqual(c.llamada_ui.nombre,'ROMAN');c.llamada_ui.aceptar();c.revisar_interacciones()
            self.assertEqual(c.dialogo.autor,'ROMAN');self.assertEqual(c.historial[-1][0],'Roman')
            self.assertEqual(hablar.call_args.kwargs['invitado'],'roman')
            c.eventos.put(('voz',(c.voz.generacion,True)));c.poll()
            self.assertFalse(c.boca_activa)
            c.eventos.put(('voz',(c.voz.generacion,False)));c.poll()
            self.assertTrue(c.llamada_ui.cerrada);self.assertIsNotNone(c.reaccion_pendiente)
            self.assertEqual(c.dialogo.objetivo,'')
            c.reaccion_pendiente=(0,c.reaccion_pendiente[1]);c.revisar_interacciones()
            self.assertEqual(c.dialogo.autor,'CAPRI');self.assertEqual(c.historial[-1][0],'Capri')
            self.assertNotIn('invitado',hablar.call_args.kwargs);self.assertNotIn('efecto',hablar.call_args.kwargs)
            self.assertEqual(c.cfg,config)

    def test_colgar_invitado_no_completa_no_dispara_comentario(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta):
            c.llamar_capri(invitado='talia');c.llamada_ui.aceptar();c.llamada_ui.rechazar()
            self.assertIsNone(c.reaccion_pendiente);self.assertIsNone(c.mensaje_llamada_pendiente)

    def test_asomo_automatico_en_ambos_modos_mira_cursor_y_restaura_sin_cfg(self):
        with self.capri() as (c,_):
            for modo in ('pantalla','personaje'):
                c.cfg['modo_visual']=modo
                if modo=='personaje':c.companera.redimensionar(1);c.companera.iniciar()
                config=dict(c.cfg);c.proximo_asomo=0;c.ultima_interaccion=time.monotonic()-200
                c.revisar_interacciones();self.assertIsNotNone(c.asomo)
                a=c.asomo['curioso']
                a.dibujar(a.inicio+1,cursor=(-1000,-1000));izq=[a.c.coords(i) for i in a.c.find_withtag('pupila_asomo')]
                a.dibujar(a.inicio+1.1,cursor=(9000,9000));der=[a.c.coords(i) for i in a.c.find_withtag('pupila_asomo')]
                self.assertEqual(len(izq),2);self.assertTrue(all(b[0]>a[0] and b[1]>a[1] for a,b in zip(izq,der)))
                self.assertFalse(a.dibujar(a.hasta+.1));c.terminar_asomo()
                self.assertIsNone(c.asomo);self.assertEqual(c.cfg,config)

    def test_juego_impide_asomo_y_reaccion_posterior(self):
        with self.capri() as (c,_),patch('escritorio.proteger_foco',return_value=True):
            c.proximo_asomo=0;c.ultima_interaccion=time.monotonic()-200;c.reaccion_pendiente=(0,'Comentario de Capri')
            c.revisar_interacciones();self.assertIsNone(c.asomo);self.assertIsNotNone(c.reaccion_pendiente)

    def test_voz_invitada_no_usa_acento_de_capri_ni_lo_sobrescribe(self):
        llamada=[]
        class Sintesis:
            def __init__(self,texto,nombre,**kw):llamada.append((nombre,kw))
            async def stream(self):yield {'type':'audio','data':b'fixture'}
        v=Voz(Mock());v.idioma='es';v.acento='pt-BR'
        with patch('edge_tts.Communicate',Sintesis),patch.object(v,'_reproducir_archivo',return_value=True):
            v._hablar('Mensaje invitado.',True,v.generacion,v.cancelar,invitado='king')
            v._hablar('Mensaje invitado.',True,v.generacion,v.cancelar,invitado='roman')
        self.assertEqual(llamada[0][0],'es-MX-JorgeNeural')
        self.assertNotEqual(llamada[0][1]['pitch'],llamada[1][1]['pitch']);self.assertEqual(v.acento,'pt-BR')

    def test_estilo_windows_noactiva_sobre_ventana_retirada(self):
        if os.name!='nt':self.skipTest('Windows')
        root=tk.Tk();root.withdraw();v=tk.Toplevel(root);v.withdraw()
        try:
            hwnd=preparar_no_activar(v);u=ctypes.windll.user32
            flags=u.GetWindowLongPtrW(hwnd,-20)
            self.assertTrue(flags&0x08000000);self.assertTrue(flags&0x80);self.assertFalse(flags&0x40000)
            self.assertEqual(v.state(),'withdrawn')
        finally:root.destroy()

    def test_presentacion_usa_show_noactivate_y_no_cambia_foreground(self):
        v=Mock();v.state.return_value='normal'
        with patch('ventanas.preparar_no_activar',return_value=123),patch('ventanas.ctypes.windll.user32') as u:
            mostrar_no_activar(v);u.ShowWindow.assert_called_once_with(123,4)
            self.assertTrue(u.SetWindowPos.call_args.args[-1]&0x10)
            u.SetForegroundWindow.assert_not_called();v.lift.assert_not_called();v.focus_force.assert_not_called()
