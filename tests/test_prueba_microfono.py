import array
from contextlib import contextmanager
import io
import json
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import prueba_microfono as prueba
import voz
from test_capri import PruebasTk

class AudioPrueba(unittest.TestCase):
    def test_umbral_filtra_volumen_sin_modificar_audio_admitido(self):
        suave=array.array('h',[100,-100]*800).tobytes()
        fuerte=array.array('h',[3000,-3000]*800).tobytes()
        self.assertEqual(prueba.filtrar(suave,None),suave)
        self.assertEqual(prueba.filtrar(suave,-60),suave)
        self.assertEqual(prueba.filtrar(suave,-40),bytes(len(suave)))
        self.assertEqual(prueba.filtrar(fuerte,-40),fuerte)
        for invalido in [None,'error',float('nan')]:self.assertIsNone(prueba.umbral_db(invalido))

    def test_grabacion_limitada_a_muestras_reales_y_mismo_microfono(self):
        stop=threading.Event();cerrado=[];niveles=[]
        bloque=array.array('h',[1200]*6400).tobytes()
        @contextmanager
        def entrada(indice,datos,recibir,detener,intentos):
            self.assertEqual(indice,23)
            for _ in range(6):recibir(bloque,6400,None,None)
            try:yield 16000
            finally:cerrado.append(True)
        sd=types.SimpleNamespace(query_devices=Mock(return_value={'name':'USB'}))
        micro=types.SimpleNamespace()
        with patch.dict(sys.modules,{'sounddevice':sd}),patch.object(voz,'resolver_microfono',return_value=23),patch.object(voz,'_abrir_entrada',entrada):
            muestra=prueba.grabar(micro,stop,lambda *v:niveles.append(v),{'nombre':'USB'},duracion=1)
        self.assertTrue(cerrado);self.assertEqual(muestra.tasa,16000)
        self.assertEqual(len(muestra.pcm),32000);self.assertTrue(muestra.pcm.startswith(bloque))
        self.assertEqual(niveles[-1][2],1)
        self.assertLess(niveles[0][0],0);self.assertGreater(niveles[0][1],0)

    def test_reproduccion_cancelable_no_abre_microfono(self):
        stop=threading.Event();escritos=[];abortados=[]
        class Salida:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def write(self,pcm):escritos.append(pcm);stop.set()
            def abort(self):abortados.append(True)
        sd=types.SimpleNamespace(query_devices=lambda **k:{'default_samplerate':16000},RawOutputStream=Mock(return_value=Salida()))
        with patch.dict(sys.modules,{'sounddevice':sd}):
            prueba.reproducir(prueba.Muestra(bytes(32000),16000),stop)
        self.assertEqual(len(escritos),1);self.assertTrue(abortados)

    def test_modelo_recibe_evidencia_de_captura_solo_para_dictado(self):
        from core import IA
        enviados=[]
        def responder(req,**kwargs):
            enviados.append(json.loads(req.data))
            return io.BytesIO(json.dumps({'message':{'content':'Esta frase sí llegó.'}}).encode())
        with patch('core.urllib.request.urlopen',side_effect=responder):
            IA().conversar('A veces no me escuchas?',modelo='local',origen='voz')
            IA().conversar('A veces no me escuchas?',modelo='local')
        evidencia=lambda p:any('YA fue transcrita' in m['content'] for m in p['messages'] if m['role']=='system')
        self.assertTrue(evidencia(enviados[0]));self.assertFalse(evidencia(enviados[1]))

class Panel(PruebasTk):
    def test_no_graba_al_abrir_reproduce_solo_al_pedir_y_descarta_resultados_viejos(self):
        import tkinter as tk
        root=tk.Tk();root.withdraw();micro=Mock();cfg={}
        micro.probar.return_value=prueba.Muestra(bytes(3200),16000)
        panel=prueba.PanelPrueba(root,micro,cfg,lambda k,v:cfg.update({k:v}));panel.pack()
        try:
            micro.probar.assert_not_called();panel.grabar();panel.hilo.join(1);panel.poll()
            self.assertIsNotNone(panel.muestra);micro.reproducir_prueba.assert_not_called()
            viejo=panel.ticket;panel.descartar()
            panel.cola.put((viejo,'fin',prueba.Muestra(bytes(3200),16000),None));panel.poll()
            self.assertIsNone(panel.muestra)
            panel.automatico.set(False);panel.cambiar();panel.escala.set(-40);panel.cambiar()
            self.assertEqual(cfg['umbral_microfono_db'],-40)
            panel.destroy();self.assertTrue(panel.stop.is_set());self.assertIsNone(panel.muestra)
        finally:root.destroy()
