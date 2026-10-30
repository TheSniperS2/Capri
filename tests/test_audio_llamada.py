import tempfile,time,wave,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from unittest.mock import Mock,patch
import unittest
import numpy as np
import tkinter as tk
from audio_llamada import preparar,barras
from voz import Voz
from llamadas import LlamadaCapri
from test_capri import PruebasTk
import test_companera_control as fixtures


class AudioTelefono(unittest.TestCase):
    def muestra(self,carpeta):
        t=np.arange(16000)/16000
        audio=(np.sin(2*np.pi*100*t)+np.sin(2*np.pi*1000*t)+np.sin(2*np.pi*6000*t))*.12
        audio=np.concatenate((audio,np.zeros(8000)))
        p=carpeta/'origen.wav'
        with wave.open(str(p),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes((audio*32767).astype('<i2').tobytes())
        return p

    def test_filtro_real_atenua_extremos_conserva_voz_y_silencio(self):
        with tempfile.TemporaryDirectory() as d:
            origen=self.muestra(Path(d));antes=origen.read_bytes();salida,niveles,adelanto=preparar(origen,True)
            try:
                self.assertEqual(origen.read_bytes(),antes);self.assertNotEqual(salida,origen)
                with wave.open(str(salida),'rb') as w:
                    self.assertEqual(w.getframerate(),16000);self.assertEqual(w.getnchannels(),1)
                    pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
                voz=pcm[round(adelanto*16000):round((adelanto+1)*16000)]
                espectro=np.abs(np.fft.rfft(voz))
                self.assertGreater(espectro[1000],espectro[100]*10)
                self.assertGreater(espectro[1000],espectro[6000]*10)
                self.assertLess(max(niveles[-12:]),.002);self.assertGreater(max(niveles),.2)
                self.assertTrue(any(abs(pcm[:round(adelanto*16000)])>0))
            finally:salida.unlink(missing_ok=True)

    def test_barras_siguen_posicion_del_audio_y_archivo_filtrado_se_elimina(self):
        v=Voz(Mock());vistas=[];contador=[0]
        def mci(cmd,res=None,longitud=0):
            if cmd.endswith(' length'):res.value='1000'
            elif cmd.endswith(' position'):res.value='400'
            elif cmd.endswith(' mode'):
                vistas.append(v.bandas_salida);contador[0]+=1;res.value='playing' if contador[0]<3 else 'stopped'
            return 0
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'convertido.wav';p.write_bytes(b'fixture')
            niveles=[0.]*10+[.6]*40
            with patch('audio_llamada.preparar',return_value=(p,niveles,.18)),patch.object(v,'_mci',side_effect=mci):
                self.assertTrue(v._reproducir_archivo(Path(d)/'original.mp3',v.generacion,v.cancelar,telefono=True,conectar=True))
            self.assertIn(barras(niveles,.4),vistas);self.assertFalse(p.exists())
            self.assertEqual(v.bandas_salida,(0.,)*28)


class LlamadaVoz(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_onda_usa_nivel_y_espera_a_la_voz_antes_de_caducar(self):
        root=tk.Tk();root.withdraw();original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        try:
            with patch('llamadas.tk.Toplevel',Oculta):
                niveles=[0.]*28;ocupada=[True]
                l=LlamadaCapri(root,Mock(),Mock(),senal=lambda:niveles,ocupada=lambda:ocupada[0]);l.aceptar()
                def alturas():return [abs(l.c.coords(i)[3]-l.c.coords(i)[1]) for i in l.c.find_withtag('onda_voz')]
                self.assertEqual(max(alturas()),1)
                niveles[:]=[.8]*28;l.dibujar();self.assertGreater(min(alturas()),14)
                niveles[:]=[0.]*28;l.ultimo_audio=time.monotonic()-20;l.dibujar()
                self.assertFalse(l.cerrada);self.assertEqual(max(alturas()),1)
                ocupada[0]=False;l.terminar_voz();self.assertTrue(l.cerrada)
        finally:root.destroy()

    def test_saludo_y_canal_solo_durante_llamada_sin_cambiar_configuracion(self):
        original=tk.Toplevel
        class Oculta(original):
            def deiconify(self):pass
            def lift(self,*a):pass
        with self.capri() as (c,_),patch('llamadas.tk.Toplevel',Oculta),patch.object(c.voz,'hablar') as hablar:
            c.cfg['voz']=True;config=dict(c.cfg);c.llamar_capri();c.llamada_ui.aceptar();c.revisar_interacciones()
            self.assertEqual(hablar.call_args.kwargs['efecto'],'llamada_inicio')
            self.assertTrue(any(c.ia.historia[-1]['content'].startswith(s) for s in (
                'Aló. Capri al aparato.','Choom, soy Capri.','Buenas, habla Capri.','Capri en línea.')))
            c.narrar_respuesta(c.peticion,'Seguimos conversando.',True)
            self.assertEqual(hablar.call_args.kwargs['efecto'],'llamada')
            c.llamada_ui.rechazar();c.narrar_respuesta(c.peticion,'Ahora voz habitual.',True)
            self.assertNotIn('efecto',hablar.call_args.kwargs);self.assertEqual(c.cfg,config)
