import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import reconocimiento as rec

def instalar_falso(carpeta,modelo):
    ruta=carpeta/('whisper-'+modelo);ruta.mkdir(parents=True,exist_ok=True)
    for nombre in rec.ARCHIVOS:(ruta/nombre).write_bytes(bytes(150))

class SeleccionModelos(unittest.TestCase):
    def test_qwen_desactiva_thinking_en_carga_chat_e_intenciones(self):
        import io,core
        from intenciones import Interprete
        respuestas=[{}, {'message':{'content':'Soy Capri.'}},
                    {'message':{'content':'{"accion":"spotify_pausa","valor":""}'}}]
        with patch.object(core.urllib.request,'urlopen',side_effect=[io.BytesIO(json.dumps(r).encode('utf-8')) for r in respuestas]) as red:
            ia=core.IA();modelo='qwen3.5:2b-q4_K_M'
            ia.preparar(modelo);ia.conversar('Hola',modelo)
            self.assertEqual(Interprete().resolver('detén la música',modelo).orden,core.Orden('spotify_pausa'))
        self.assertEqual(red.call_count,3)
        for llamada in red.call_args_list:
            self.assertIs(json.loads(llamada.args[0].data)['think'],False)

    def test_seleccion_base_small_y_respaldo_si_falta_el_preferido(self):
        with tempfile.TemporaryDirectory() as d:
            carpeta=Path(d);instalar_falso(carpeta,'base')
            self.assertEqual(rec.modelos_disponibles(carpeta),['base'])
            self.assertEqual(rec.elegir_modelo(carpeta,'small'),'base')
            instalar_falso(carpeta,'small')
            self.assertEqual(rec.elegir_modelo(carpeta,'small'),'small')
            self.assertEqual(rec.elegir_modelo(carpeta,'base'),'base')
            self.assertEqual(rec.elegir_modelo(carpeta,'../otro'),'base')
            (carpeta/'whisper-small/model.bin').unlink()
            self.assertEqual(rec.elegir_modelo(carpeta,'small'),'base')

    def test_cambio_de_modelo_recarga_una_vez_y_reutiliza_el_seleccionado(self):
        modelo=Mock();modelo.transcribe.return_value=(iter([]),None)
        with tempfile.TemporaryDirectory() as d,patch('faster_whisper.WhisperModel',return_value=modelo) as cargar:
            carpeta=Path(d)
            for n in ('base','small'):instalar_falso(carpeta,n)
            micro=types.SimpleNamespace(carpeta=carpeta,modelo_whisper='small',whisper=object(),whisper_cargado='base')
            rec.transcribir(micro,bytes(32000),16000)
            cargar.assert_called_once_with(str(carpeta/'whisper-small'),device='cpu',compute_type='int8',cpu_threads=4)
            rec.transcribir(micro,bytes(32000),16000)
            self.assertEqual(cargar.call_count,1)
            micro.modelo_whisper='base'
            rec.transcribir(micro,bytes(32000),16000)
            self.assertEqual(cargar.call_count,2)
            self.assertEqual(cargar.call_args.args[0],str(carpeta/'whisper-base'))

    def test_preparador_small_tiene_destino_y_limite_correctos_sin_tocar_base(self):
        import preparar_whisper
        with tempfile.TemporaryDirectory() as d,patch.object(preparar_whisper,'descargar') as descargar:
            p=preparar_whisper.preparar(Path(d),modelo='small')
            self.assertEqual(p,Path(d)/'whisper-small')
            self.assertEqual(descargar.call_count,len(rec.ARCHIVOS))
            for llamada in descargar.call_args_list:
                self.assertIn('faster-whisper-small/resolve/main/',llamada.args[0])
                self.assertGreater(llamada.kwargs['maximo'],483546902)
            self.assertFalse((Path(d)/'whisper-base').exists())
            with self.assertRaises(ValueError):preparar_whisper.preparar(Path(d),modelo='../otro')

if __name__=='__main__':unittest.main()
