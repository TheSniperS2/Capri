import time
from pathlib import Path
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from despedida_camara import TRASLADO


class Grabacion(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_cierre_directo_omite_toda_la_despedida_sin_cambiar_otras_animaciones(self):
        with self.capri() as (c,_),patch.object(c,'iniciar_despedida') as animar,patch.object(c,'cerrar_inmediato') as cerrar:
            c.animacion_cierre=True;c.cfg.update(animaciones=True,despedida_cierre=False)
            c.cerrar();cerrar.assert_called_once();animar.assert_not_called()
            self.assertTrue(c.cfg['animaciones'])

    def test_frase_siempre_choom_aunque_haya_un_nombre_antiguo_guardado(self):
        from idiomas import frase_despedida
        self.assertEqual(frase_despedida('en'),"I'll see you around, choom.")
        self.assertEqual(frase_despedida('es'),'Cuídate mucho, choom.')
        with self.capri() as (c,_),patch.object(c.voz,'preparar',return_value=Mock()) as preparar:
            c.cfg.update(idioma='en',nombre_despedida='Sol',voz=True);c.iniciar_despedida()
            preparar.assert_called_once();self.assertEqual(preparar.call_args.args[0],"I'll see you around, choom.")

    def test_ajustes_guarda_interruptor_sin_campo_de_nombre(self):
        import json
        from tema_ui import tk
        original=tk.Toplevel
        class Oculta(original):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.withdraw()
            def deiconify(self):self.withdraw()
        with self.capri() as (c,carpeta),patch.object(tk,'Toplevel',Oculta),patch.object(c,'cargar_microfonos'),patch.object(c.ia,'modelos',return_value=[]):
            c.configurar();c.ajustes.withdraw()
            zona=c.panel_ajustes.secciones['Escritorio']
            def hijos(w):
                for h in w.winfo_children():yield h;yield from hijos(h)
            controles=list(hijos(zona))
            interruptor=next(w for w in controles if getattr(w,'texto','')=='Reproducir despedida al cerrar Capri')
            interruptor.invoke()
            cfg=json.loads((carpeta/'ajustes.json').read_text(encoding='utf8'))
            self.assertFalse(cfg['despedida_cierre'])
            self.assertFalse(hasattr(c,'nombre_despedida'))
            self.assertTrue(c.cfg['animaciones'])
            c.ajustes.destroy();c.root.update_idletasks()

    def test_voz_habitual_y_choom_en_una_sola_frase_sin_tratamientos(self):
        with self.capri() as (c,_),patch.object(c.voz,'preparar',return_value=Mock(archivo=Path('fixture.mp3'))) as preparar,patch.object(c.voz,'hablar') as hablar:
            preparar.return_value.listo.is_set.return_value=True
            c.cfg.update(voz=True,voz_perfil='chilena',voz_natural=False,velocidad_voz=1.15,nombre_despedida='Sol')
            c.voz.acento='pt-BR';config=dict(c.cfg);c.iniciar_despedida()
            self.assertEqual(c.frase_despedida,'Cuídate mucho, choom.')
            self.assertEqual(preparar.call_args.args,('Cuídate mucho, choom.',False))
            c.inicio_salida=time.monotonic()-TRASLADO-.9;c.pintar_despedida()
            self.assertEqual(hablar.call_args.args,('Cuídate mucho, choom.',False))
            self.assertEqual(hablar.call_args.kwargs['perfil'],'chilena')
            self.assertEqual(hablar.call_args.kwargs['velocidad'],1.15)
            self.assertNotIn('efecto',hablar.call_args.kwargs)
            self.assertEqual(c.voz.acento,'pt-BR');self.assertEqual(c.cfg,config)

    def test_expresiones_siguen_habla_pausas_y_sonrisa_final_antes_de_mano(self):
        with self.capri() as (c,_):
            c.iniciar_despedida();cam=c.salida_camara;self.assertEqual(len(cam.fotos),4)
            c.salida_generacion=c.voz.generacion
            c.inicio_salida=time.monotonic()-TRASLADO-.9
            c.eventos.put(('voz',(c.voz.generacion,True)));c.poll();c.pintar_despedida()
            self.assertEqual(cam.indice,2)
            c.eventos.put(('voz',(c.voz.generacion,('avance_voz',(c.frase_despedida,10,False)))));c.poll();c.pintar_despedida()
            self.assertEqual(cam.indice,1)
            c.eventos.put(('voz',(c.voz.generacion,False)));c.poll();c.pintar_despedida()
            self.assertEqual(cam.indice,3);self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            self.assertGreater(c.salida_sonrisa_hasta,time.monotonic())
            c.salida_sonrisa_hasta=0;c.inicio_salida=time.monotonic()-TRASLADO-2
            c.pintar_despedida();self.assertIs(c.salida.imagen,cam.fotos[3])

    def test_grano_animado_cacheado_sobre_imagen_de_camara(self):
        with self.capri() as (c,_):
            c.iniciar_despedida();cam=c.salida_camara
            self.assertEqual(len(cam.grano),6)
            c.inicio_salida=time.monotonic()-TRASLADO-.1;c.pintar_despedida()
            primero=c.canvas.itemcget(c.canvas.find_withtag('grano_grabacion')[0],'image')
            c.inicio_salida=time.monotonic()-TRASLADO-.4;c.pintar_despedida()
            segundo=c.canvas.itemcget(c.canvas.find_withtag('grano_grabacion')[0],'image')
            self.assertNotEqual(primero,segundo)

    def test_mirada_hacia_luz_y_sonrisa_antes_de_mano_sobre_cielo(self):
        with self.capri() as (c,_):
            c.cfg['voz']=False;c.iniciar_despedida();cam=c.salida_camara
            for t,indice in ((.1,0),(.8,1),(1.5,3)):
                c.inicio_salida=time.monotonic()-TRASLADO-t;c.pintar_despedida()
                self.assertEqual(cam.indice,indice)
                self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            c.inicio_salida=time.monotonic()-TRASLADO-1.8-4.4*.5;c.pintar_despedida()
            self.assertTrue(c.canvas.find_withtag('mano_despedida'))
            self.assertTrue(c.canvas.find_withtag('cielo_despedida'))
            self.assertTrue(c.canvas.find_withtag('estrella'))
            self.assertFalse(c.canvas.find_withtag('rostro_despedida'))

    def test_cielo_permanece_desde_el_traslado_hasta_la_mano(self):
        with self.capri() as (c,_):
            c.cfg['voz']=False;c.iniciar_despedida()
            imagen=c.canvas.itemcget(c.canvas.find_withtag('cielo_despedida')[0],'image')
            for t in (TRASLADO*.5,TRASLADO+.2,TRASLADO+1.5,TRASLADO+1.8+4.4*.5):
                c.inicio_salida=time.monotonic()-t;c.pintar_despedida()
                fondo=c.canvas.find_withtag('cielo_despedida')[0]
                self.assertEqual(c.canvas.itemcget(fondo,'image'),imagen)
                self.assertEqual(c.canvas.find_all()[0],fondo)

    def test_telon_recoge_el_cielo_antes_del_cierre_definitivo(self):
        from despedida import DURACION,DURACION_TELON
        with self.capri() as (c,_):
            c.cfg['voz']=False;c.iniciar_despedida()
            c.inicio_salida=time.monotonic()-TRASLADO-1.8-DURACION-DURACION_TELON*.5;c.pintar_despedida()
            self.assertFalse(c.cerrado);telon=c.canvas.find_withtag('telon_despedida')[0]
            self.assertLess(c.canvas.coords(telon)[1],0)
            self.assertGreater(c.canvas.bbox(telon)[3],0)
            self.assertFalse(c.canvas.find_withtag('mano_despedida'))
            c.salida_reanudar=time.monotonic()-DURACION-DURACION_TELON-.1;c.pintar_despedida()
            self.assertTrue(c.cerrado)

    def test_opciones_ingles_no_alteran_el_perfil_en_espanol(self):
        from voz import elegir_voz
        self.assertEqual(elegir_voz('ingles_vivaz','en','auto'),('en-US-AnaNeural','+0Hz'))
        self.assertEqual(elegir_voz('ingles_calida','en','en-US'),('en-US-JennyNeural','+12Hz'))
        self.assertEqual(elegir_voz('ingles_vivaz','es','auto'),elegir_voz('capri','es','auto'))

    def test_mano_suavizada_se_prepara_una_vez_y_tiene_borde_gradual(self):
        from PIL import ImageTk
        with self.capri() as (c,_):
            c.iniciar_despedida();s=c.salida;foto=s.mano_foto
            hist=ImageTk.getimage(foto).getchannel('A').histogram()
            self.assertGreater(sum(hist[1:255]),0)
            for t in (.4,.5):
                s.dibujar(c.canvas,t)
                item=c.canvas.find_withtag('mano_despedida')[0]
                self.assertEqual(c.canvas.itemcget(item,'image'),str(foto))
            self.assertIs(s.mano_foto,foto)
