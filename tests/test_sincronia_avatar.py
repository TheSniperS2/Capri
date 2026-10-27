from pathlib import Path
import threading
from unittest.mock import patch
from PIL import Image,ImageChops
from test_capri import PruebasTk
import app
from avatar import estados_originales,BOCA
from sincronia import alinear_marcas,avance_texto
from voz import Voz

class Sincronia(PruebasTk):
    def test_no_cambia_pelo_cuerpo_ni_pose_entre_los_tres_estados(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        estados=estados_originales(assets/'capri-base-v2.png',assets/'capri-bocas-v2.png')
        with Image.open(assets/'capri-base-v2.png') as base:self.assertEqual(estados[0].tobytes(),base.convert('RGBA').tobytes())
        self.assertEqual(len(estados),3)
        for estado in estados[1:]:
            diferencia=ImageChops.difference(estados[0].convert('RGB'),estado.convert('RGB'))
            caja=diferencia.getbbox();self.assertIsNotNone(caja)
            self.assertGreaterEqual(caja[0],BOCA[0]);self.assertGreaterEqual(caja[1],BOCA[1])
            self.assertLessEqual(caja[2],BOCA[2]);self.assertLessEqual(caja[3],BOCA[3])

    def test_marcas_repetidas_y_puntuacion_se_alinean_al_texto_original(self):
        texto='Hola, Capri. Hola.'
        eventos=[{'text':'Hola','offset':0,'duration':3_000_000},
                 {'text':'Capri','offset':5_000_000,'duration':5_000_000},
                 {'text':'Hola','offset':12_000_000,'duration':3_000_000}]
        marcas=alinear_marcas(texto,eventos)
        self.assertEqual(avance_texto(texto,-.1,2,marcas),0)
        self.assertEqual(avance_texto(texto,.75,2,marcas),8)
        self.assertEqual(avance_texto(texto,1.6,2,marcas),len(texto))
        self.assertEqual(avance_texto(texto,1,2),len(texto)//2)

    def test_reproductor_emite_avance_segun_posicion_y_no_antes_de_play(self):
        eventos=[];comandos=[];modos=iter(['playing','playing','stopped']);posiciones=iter(['0','500'])
        def mci(cmd,*args):
            comandos.append(cmd)
            if cmd.endswith(' length'):args[0].value='1000'
            elif cmd.endswith(' mode'):args[0].value=next(modos)
            elif cmd.endswith(' position'):args[0].value=next(posiciones)
            return 0
        v=Voz(lambda e:eventos.append((len(comandos),e)))
        with patch.object(v,'_mci',side_effect=mci):
            v._reproducir_archivo(Path('prueba.mp3'),v.generacion,v.cancelar,texto='Hola Capri')
        play=next(i+1 for i,c in enumerate(comandos) if c.startswith('play '))
        avances=[e[1][1][:2] for e in eventos if isinstance(e[1],tuple)]
        self.assertTrue(all(i>=play for i,e in eventos))
        self.assertEqual(avances[0],('Hola Capri',0))
        self.assertIn(('Hola Capri',5),avances)
        self.assertEqual(avances[-1],('Hola Capri',10))

    def test_panel_espera_audio_y_solo_avanza_con_eventos_del_reproductor(self):
        with patch.object(app.Voz,'parar'),patch.object(app.Voz,'hablar'):
            c=app.Capri(hotkeys=False);c.root.withdraw();c.cfg['voz']=True;c.cfg['volumen_voz']=100
            try:
                texto='Hola. Esta frase avanza con la voz.';c.peticion=25
                c.eventos.put(('respuesta_parcial',(25,texto)));c.poll()
                self.assertEqual(c.dialogo.visible,'')
                c.eventos.put(('respuesta',(25,texto)));c.poll()
                self.assertEqual(c.dialogo.visible,'')
                gen=c.voz.generacion
                c.eventos.put(('voz',(gen,True)))
                c.eventos.put(('voz',(gen,('avance_voz',(texto,6,True)))));c.poll()
                self.assertEqual(c.dialogo.visible,texto[:6])
                self.assertTrue(c.boca_activa)
                c.eventos.put(('voz',(gen,('avance_voz',(texto,6,False)))));c.poll()
                self.assertFalse(c.boca_activa)
                c.dialogo.tick();self.assertEqual(c.dialogo.visible,texto[:6])
                c.eventos.put(('voz',(gen-1,('avance_voz',(texto,len(texto))))));c.poll()
                self.assertEqual(c.dialogo.visible,texto[:6])
                c.eventos.put(('voz',(gen,('avance_voz',(texto,len(texto))))))
                c.eventos.put(('voz',(gen,False)));c.poll()
                self.assertEqual(c.dialogo.visible,texto);self.assertFalse(c.narracion_activa)
                self.assertIsNone(c.panel)
            finally:c.cerrar()
