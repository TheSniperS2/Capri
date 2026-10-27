import io
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import intenciones
from intenciones import Interprete,Decision,requiere_contexto
from core import Orden,interpretar

class Intenciones(unittest.TestCase):
    def test_detener_equivale_a_pausa_y_referencias_no_se_buscan_como_titulos(self):
        for frase in ['detén la canción','puedes detener la música','para Spotify']:
            self.assertEqual(interpretar(frase),Orden('spotify_pausa'))
        self.assertTrue(requiere_contexto(interpretar('pon otra')))
        self.assertFalse(requiere_contexto(interpretar('abre Spotify')))

    def test_contexto_se_acota_caduca_y_una_charla_cambia_el_tema(self):
        i=Interprete()
        with patch.object(intenciones.time,'monotonic',return_value=100):
            for _ in range(6):i.registrar('pausa',Orden('spotify_pausa'),'Pausé Spotify.')
            self.assertEqual(len(i.contexto()['turnos']),4)
            self.assertEqual(i.contexto()['tema_activo'],'spotify')
            i.registrar('gracias',None,'De nada.')
            self.assertEqual(i.contexto()['tema_activo'],'spotify')
            i.registrar('hablemos de cine',None,'Hablemos.')
            self.assertEqual(i.contexto()['tema_activo'],'')
        with patch.object(intenciones.time,'monotonic',return_value=281):
            self.assertEqual(i.contexto(),{'tema_activo':'','turnos':[]})

    def test_json_estructurado_local_y_contexto_real_sin_ejecutar(self):
        i=Interprete();i.registrar('detén la canción',Orden('spotify_pausa'),'Pausé Spotify.')
        respuesta={'message':{'content':json.dumps({'accion':'spotify','valor':''})}}
        with patch.object(intenciones.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(respuesta).encode())) as red:
            self.assertEqual(i.resolver('ahora sigue','modelo:local').orden,Orden('spotify'))
        req=red.call_args.args[0];cuerpo=json.loads(req.data)
        self.assertEqual(req.full_url,'http://127.0.0.1:11434/api/chat')
        self.assertEqual(cuerpo['format'],intenciones.ESQUEMA)
        self.assertEqual(cuerpo['options']['temperature'],0)
        self.assertEqual(cuerpo['messages'][-1],{'role':'user','content':'ahora sigue'})
        self.assertIn('Tema activo actual: spotify',cuerpo['messages'][0]['content'])
        datos=json.loads(cuerpo['messages'][-2]['content'])
        self.assertEqual(datos['resultado_real'],'Pausé Spotify.')

    def test_pregunta_pendiente_se_envia_como_turno_real_de_conversacion(self):
        i=Interprete();i.registrar('detenla',None,'¿A qué te refieres?',aclaracion=True)
        r={'message':{'content':'{"accion":"spotify_pausa","valor":""}'}}
        with patch.object(intenciones.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(r).encode())) as red:
            self.assertEqual(i.resolver('la canción','modelo').orden,Orden('spotify_pausa'))
        mensajes=json.loads(red.call_args.args[0].data)['messages']
        self.assertEqual(mensajes[-2],{'role':'assistant','content':'¿A qué te refieres?'})
        self.assertEqual(mensajes[-1],{'role':'user','content':'la canción'})

    def test_negaciones_citas_y_explicaciones_no_consultan_router(self):
        with patch.object(intenciones.urllib.request,'urlopen') as red:
            for frase in ['no detengas la canción','cómo se pausa Spotify','explica detenla','«pausa Spotify»']:
                self.assertEqual(Interprete().resolver(frase,'modelo'),Decision())
            red.assert_not_called()

    def test_respuesta_invalida_no_inventa_acciones_ni_parametros(self):
        i=Interprete();c=i.contexto()
        invalidas=[{'accion':'shell','valor':'calc.exe'},
                   {'accion':'abrir','valor':'powershell'},
                   {'accion':'spotify_pausa','valor':'algo'},
                   {'accion':'buscar','valor':'una consulta inventada'},
                   {'accion':'spotify','valor':'una cancion inventada'},
                   {'accion':'pestana','valor':'file:///C:/Windows'},
                   {'accion':'spotify_pausa','valor':'','codigo':'arbitrario'},
                   {'accion':'spotify_pausa','valor':None},[],None]
        for datos in invalidas:
            with self.subTest(datos=datos):
                decision=i.validar(datos,'haz algo con la música',c)
                self.assertIsNone(decision.orden)
                self.assertTrue(decision.pregunta)

    def test_pronombre_sin_referente_pide_aclaracion_aunque_modelo_adivine(self):
        i=Interprete();datos={'accion':'spotify_pausa','valor':''}
        self.assertTrue(i.validar(datos,'detenla',i.contexto()).pregunta)
        i.registrar('pon mi lista juntos',Orden('spotify_playlist','juntos'),'No confirmó reproducción.')
        self.assertEqual(i.validar(datos,'detenla',i.contexto()).orden,Orden('spotify_pausa'))
        # El resultado se conserva como lo devolvió el ejecutor, sin convertir el
        # intento fallido en una afirmación de que la playlist estaba sonando.
        self.assertIn('No confirmó',i.contexto()['turnos'][-1]['resultado'])

    def test_parametros_extraidos_se_conservan_y_no_se_interpretan_como_codigo(self):
        texto='busca gatos; $(calc) `prueba`'
        valor='gatos; $(calc) `prueba`'
        i=Interprete()
        self.assertEqual(i.validar({'accion':'buscar','valor':valor},texto,i.contexto()).orden,Orden('buscar',valor))

    def test_cancelacion_antes_y_despues_de_inferencia(self):
        i=Interprete();cancelar=threading.Event();cancelar.set()
        with patch.object(intenciones.urllib.request,'urlopen') as red:
            with self.assertRaises(InterruptedError):i.resolver('detén la música','modelo',cancelar)
            red.assert_not_called()
        cancelar.clear()
        def red(*args,**kwargs):
            cancelar.set()
            return io.BytesIO(json.dumps({'message':{'content':'{"accion":"spotify_pausa","valor":""}'}}).encode())
        with patch.object(intenciones.urllib.request,'urlopen',side_effect=red):
            with self.assertRaises(InterruptedError):i.resolver('detén la música','modelo',cancelar)

    def test_json_roto_pide_reformular_y_no_vuelve_a_charla_como_exito(self):
        with patch.object(intenciones.urllib.request,'urlopen',return_value=io.BytesIO(b'{"message":{"content":"no JSON"}}')):
            d=Interprete().resolver('detén la música','modelo')
            self.assertIsNone(d.orden);self.assertTrue(d.pregunta)

if __name__=='__main__':unittest.main()
