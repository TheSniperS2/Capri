import base64
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import wave
import numpy as np
from voz import Voz,pausa_choom,texto_para_voz


def audio_fixture():
    salida=io.BytesIO()
    with wave.open(salida,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes(np.full(24000,6000,dtype='<i2').tobytes())
    return salida.getvalue()


def marcas_fixture(texto):
    palabras=('Cuídate','mucho','choom') if texto.startswith('Cuídate') else ('around','choom')
    tiempos=(0,.3,.65) if len(palabras)==3 else (.2,.65)
    return [(t,.3,texto.index(p),texto.index(p)+len(p)) for p,t in zip(palabras,tiempos)]


class RitmoDespedida(unittest.TestCase):
    def test_pausa_de_medio_segundo_conserva_muestras_y_desplaza_solo_choom(self):
        for texto in ('Cuídate mucho, choom.',"I'll see you around, choom."):
            with self.subTest(texto=texto),tempfile.TemporaryDirectory() as d:
                original=Path(d)/'voz.wav';original.write_bytes(audio_fixture());marcas=marcas_fixture(texto)
                nuevo,ajustadas=pausa_choom(original,texto,marcas)
                try:
                    with wave.open(str(nuevo),'rb') as w:
                        pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
                    diferencia=ajustadas[-1][0]-marcas[-1][0]
                    self.assertAlmostEqual(ajustadas[-1][0]-(ajustadas[-2][0]+ajustadas[-2][1]),.52,places=4)
                    self.assertEqual(ajustadas[:-1],marcas[:-1])
                    self.assertEqual(np.count_nonzero(pcm),24000)
                    self.assertAlmostEqual(np.count_nonzero(pcm==0)/24000,diferencia,places=4)
                    self.assertTrue(np.all(pcm[pcm!=0]==6000))
                finally:
                    if nuevo!=original:nuevo.unlink(missing_ok=True)

    def test_no_alarga_pausa_suficiente_ni_otros_dialogos(self):
        p=Path('no-se-abre.wav');texto='Cuídate mucho, choom.';marcas=marcas_fixture(texto)
        marcas[-1]=(1.2,*marcas[-1][1:])
        self.assertEqual(pausa_choom(p,texto,marcas),(p,marcas))
        self.assertEqual(pausa_choom(p,'Hola, choom.',marcas),(p,marcas))
        self.assertNotIn(',',texto_para_voz('Hola, choom.'))

    def test_tts_recibe_coma_y_audio_preparado_incluye_pausa_sin_reproducirse(self):
        texto='Cuídate mucho, choom.';peticiones=[]
        class Sintesis:
            def __init__(self,texto,nombre,**kw):peticiones.append(texto)
            async def stream(self):
                yield {'type':'audio','data':audio_fixture()}
                for offset,duracion,a,b in marcas_fixture(texto):
                    yield {'type':'WordBoundary','text':texto[a:b],'offset':round(offset*10_000_000),'duration':round(duracion*10_000_000)}
        v=Voz(Mock());v.idioma='es'
        with patch('edge_tts.Communicate',Sintesis),patch.object(v,'_reproducir_archivo') as reproducir:
            audio=v.preparar(texto)
            try:
                self.assertTrue(audio.listo.wait(3));self.assertIsNotNone(audio.archivo)
                self.assertEqual(peticiones,[texto]);reproducir.assert_not_called()
                self.assertAlmostEqual(audio.marcas[-1][0]-(audio.marcas[-2][0]+audio.marcas[-2][1]),.52,places=4)
            finally:audio.descartar()

    def test_voz_windows_utiliza_pausa_explicita_en_una_sola_frase(self):
        v=Voz(Mock());v.idioma='es'
        with patch.object(v,'_reproducir_windows',return_value=False) as windows:
            v._hablar('Cuídate mucho, choom.',False,v.generacion,v.cancelar)
            script=base64.b64decode(windows.call_args.args[0]).decode('utf-16-le')
            self.assertIn('AppendBreak([TimeSpan]::FromMilliseconds(520))',script)
            self.assertIn('$v.Speak($p)',script)
