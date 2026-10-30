import time
from pathlib import Path
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from despedida_camara import TRASLADO


class Grabacion(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_voz_habitual_y_frase_choom_sin_aplicar_nombre_ni_tratamientos(self):
        with self.capri() as (c,_),patch.object(c.voz,'preparar',return_value=Mock(archivo=Path('fixture.mp3'))) as preparar,patch.object(c.voz,'hablar') as hablar:
            preparar.return_value.listo.is_set.return_value=True
            c.cfg.update(voz=True,voz_perfil='chilena',voz_natural=False,velocidad_voz=1.15,nombre_despedida='Sol')
            c.voz.acento='pt-BR';config=dict(c.cfg);c.iniciar_despedida()
            self.assertEqual(c.frase_despedida,'Cuídate mucho, choom.')
            self.assertEqual(preparar.call_args.args,('Cuídate mucho, choom.',False))
            c.inicio_salida=time.monotonic()-TRASLADO-.4;c.pintar_despedida()
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
