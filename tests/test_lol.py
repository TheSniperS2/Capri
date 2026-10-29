import base64
import sys
from pathlib import Path
import json
import threading
import unittest
import urllib.error
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import interpretar
from league import (ControlLoL,ClienteLCU,Credenciales,ErrorCliente,MENSAJES,FASE,SALA,COLA,LISTO,ACEPTAR,descubrir)


class ClienteFalso:
    def __init__(self,fase='Lobby'):
        self.fase=fase;self.llamadas=[];self.listo={'state':'InProgress','playerResponse':'None'}
    def pedir(self,metodo,ruta):
        self.llamadas.append((metodo,ruta))
        if (metodo,ruta)==('GET',FASE):return self.fase
        if (metodo,ruta)==('GET',SALA):return {'gameConfig':{'queueId':400}}
        if (metodo,ruta)==('GET',LISTO):return self.listo
        if (metodo,ruta)==('POST',COLA):self.fase='Matchmaking'
        if (metodo,ruta)==('DELETE',COLA):self.fase='Lobby'
        if (metodo,ruta)==('POST',ACEPTAR):self.listo['playerResponse']='Accepted'


class ColaLoL(unittest.TestCase):
    def test_resultados_tienen_traduccion_local_sin_modelo(self):
        from idiomas import ui
        for mensaje in MENSAJES.values():
            for idioma in ('en','pt','ja'):
                with self.subTest(mensaje=mensaje,idioma=idioma):self.assertNotEqual(ui(mensaje,idioma),mensaje)

    def test_peticiones_directas_en_cuatro_idiomas_y_proteccion_de_contexto(self):
        for frase,tipo,valor in [
            ('Capri, busca partida.','lol_buscar',''),('tira cola en el lol','lol_buscar',''),
            ('busca partida en LoL y acepta por mí','lol_buscar','auto'),
            ('can you queue up in lol and accept for me','lol_buscar','auto'),
            ('por favor busque uma partida no lol','lol_buscar',''),
            ('activa la aceptación automática del lol','lol_auto_activar',''),
            ('enable auto accept in lol','lol_auto_activar',''),
            ('ative a aceitação automática no lol','lol_auto_activar',''),
            ('自動承諾を有効にして','lol_auto_activar',''),
            ('マッチを検索して','lol_buscar',''),('acepta la partida','lol_aceptar',''),
            ('cancela la cola','lol_cancelar',''),('no aceptes más partidas','lol_auto_desactivar','')]:
            with self.subTest(frase=frase):
                orden=interpretar(frase);self.assertEqual((orden.tipo,orden.valor),(tipo,valor))
        for frase in ('no busques partida','explica cómo aceptar partida','busca partida en Google','busca "acepta partida"','"busca partida"','qué significa tira cola en lol'):
            with self.subTest(frase=frase):
                orden=interpretar(frase);self.assertFalse(orden and orden.tipo.startswith('lol_'))

    def test_buscar_verifica_cliente_y_usa_solo_sala_existente(self):
        cliente=ClienteFalso();c=ControlLoL(cliente)
        self.assertEqual(c.ejecutar('lol_buscar'),MENSAJES['buscando'])
        self.assertEqual(cliente.llamadas,[('GET',FASE),('GET',SALA),('POST',COLA),('GET',FASE)])
        self.assertIsNone(c.hilo)
        cliente.llamadas=[];c.ejecutar('lol_buscar')
        self.assertNotIn(('POST',COLA),cliente.llamadas)

    def test_no_inicia_sin_sala_ni_durante_partida_y_respeta_cancelacion(self):
        for fase in ('None','ChampSelect','InProgress','Reconnect'):
            cliente=ClienteFalso(fase);c=ControlLoL(cliente);c.ejecutar('lol_buscar')
            self.assertFalse(any(m!='GET' for m,r in cliente.llamadas))
        cancelado=threading.Event();cancelado.set();cliente=ClienteFalso()
        with self.assertRaises(InterruptedError):ControlLoL(cliente).ejecutar('lol_buscar',cancelar=cancelado)
        self.assertFalse(cliente.llamadas)

    def test_aceptar_verifica_estado_y_no_envia_doble_aceptacion(self):
        cliente=ClienteFalso('ReadyCheck');c=ControlLoL(cliente)
        self.assertEqual(c.ejecutar('lol_aceptar'),MENSAJES['aceptada'])
        c.ejecutar('lol_aceptar')
        self.assertEqual(cliente.llamadas.count(('POST',ACEPTAR)),1)
        cliente.fase='Matchmaking';cliente.llamadas=[]
        self.assertEqual(c.ejecutar('lol_aceptar'),MENSAJES['sin_lista'])
        self.assertNotIn(('POST',ACEPTAR),cliente.llamadas)

    def test_cancelar_no_rechaza_ready_check_y_desarma_auto(self):
        cliente=ClienteFalso('Matchmaking');c=ControlLoL(cliente);c._stop.clear()
        self.assertEqual(c.ejecutar('lol_cancelar'),MENSAJES['cancelada']);self.assertTrue(c._stop.is_set())
        cliente.fase='ReadyCheck';cliente.llamadas=[]
        self.assertEqual(c.ejecutar('lol_cancelar'),MENSAJES['no_cancelable'])
        self.assertFalse(any(m!='GET' for m,r in cliente.llamadas))

    def test_auto_solo_a_peticion_y_se_detiene_en_seleccion(self):
        cliente=ClienteFalso();c=ControlLoL(cliente)
        with patch.object(c,'_iniciar_auto') as iniciar:
            c.ejecutar('lol_buscar');iniciar.assert_not_called()
            c.ejecutar('lol_buscar','auto');iniciar.assert_called_once()
        avisos=[];c.avisar=avisos.append;stop=threading.Event()
        cliente.fase='ReadyCheck';c.revisar_auto(stop);c.revisar_auto(stop)
        self.assertEqual(cliente.llamadas.count(('POST',ACEPTAR)),1)
        self.assertEqual(avisos,[MENSAJES['aceptada']])
        cliente.fase='ChampSelect';c.revisar_auto(stop);self.assertTrue(stop.is_set())
        cliente.llamadas=[];c.revisar_auto(stop);self.assertFalse(cliente.llamadas)

    def test_no_afirma_exito_que_cliente_no_confirmo(self):
        cliente=ClienteFalso();real=cliente.pedir
        def sin_confirmar(m,r):
            if m=='POST':return None
            return real(m,r)
        cliente.pedir=sin_confirmar;c=ControlLoL(cliente)
        self.assertEqual(c.ejecutar('lol_buscar'),MENSAJES['solicitud'])
        cliente.fase='ReadyCheck'
        self.assertEqual(c.ejecutar('lol_aceptar'),MENSAJES['aceptando'])

    def test_error_auto_emite_aviso_y_para(self):
        cliente=Mock();cliente.pedir.side_effect=ErrorCliente();avisos=[];c=ControlLoL(cliente,avisos.append)
        stop=threading.Event()
        # El primer fallo termina el seguimiento; no reintenta aceptar a ciegas.
        c._vigilar(stop)
        self.assertTrue(stop.is_set());self.assertEqual(avisos,[MENSAJES['auto_error']])

    def test_vigilancia_persistente_acepta_colas_externas_y_sigue_despues_de_partida(self):
        cliente=ClienteFalso();avisos=[];c=ControlLoL(cliente,avisos.append);stop=threading.Event()
        fases=iter(['Matchmaking','ReadyCheck','ChampSelect','InProgress','Lobby','Matchmaking','ReadyCheck',None])
        demoras=[]
        def siguiente(demora):
            demoras.append(demora);fase=next(fases)
            if fase is None:stop.set();return True
            cliente.fase=fase
            if fase=='ReadyCheck':cliente.listo['playerResponse']='None'
            return False
        with patch.object(stop,'wait',side_effect=siguiente):c._vigilar(stop,permanente=True)
        self.assertEqual(cliente.llamadas.count(('POST',ACEPTAR)),2)
        self.assertNotIn(('POST',COLA),cliente.llamadas)
        self.assertEqual(avisos,[MENSAJES['aceptada']]*2)
        self.assertEqual(demoras[1],.25)

    def test_persistente_reconecta_sin_desactivarse_ni_repetir_avisos(self):
        cliente=ClienteFalso('ReadyCheck');original=cliente.pedir;fallos=2
        def pedir(metodo,ruta):
            nonlocal fallos
            if fallos:fallos-=1;raise ErrorCliente('cliente')
            return original(metodo,ruta)
        cliente.pedir=pedir;avisos=[];c=ControlLoL(cliente,avisos.append);stop=threading.Event();estados=[]
        def esperar(demora):
            estados.append((demora,c.estado))
            if len(estados)==3:stop.set();return True
            return False
        with patch.object(stop,'wait',side_effect=esperar):c._vigilar(stop,permanente=True)
        self.assertEqual(estados[:2],[(2,MENSAJES['auto_conexion'])]*2)
        self.assertEqual(avisos,[MENSAJES['aceptada']])
        self.assertEqual(cliente.llamadas.count(('POST',ACEPTAR)),1)

    def test_activar_una_vez_desactivar_y_no_esperar_bloqueo_de_red(self):
        c=ControlLoL(ClienteFalso())
        with patch('league.threading.Thread') as hilo:
            c.activar_auto();stop=c._stop;c.activar_auto()
            self.assertEqual(hilo.call_count,1);hilo.return_value.start.assert_called_once()
            self.assertTrue(c.permanente);self.assertFalse(stop.is_set())
            c.detener_auto();self.assertTrue(stop.is_set());self.assertFalse(c.permanente)
            c.activar_auto();self.assertEqual(hilo.call_count,2);c.cerrar()
            self.assertTrue(c._stop.is_set())

    def test_cancelar_ready_check_impide_autoaceptarlo_pero_conserva_vigilancia(self):
        cliente=ClienteFalso('ReadyCheck');c=ControlLoL(cliente);c.permanente=True
        stop=threading.Event();self.assertEqual(c.ejecutar('lol_cancelar'),MENSAJES['no_cancelable'])
        c.revisar_auto(stop,True);self.assertNotIn(('POST',ACEPTAR),cliente.llamadas)
        cliente.fase='Matchmaking';c.revisar_auto(stop,True)
        cliente.fase='ReadyCheck';c.revisar_auto(stop,True)
        self.assertIn(('POST',ACEPTAR),cliente.llamadas)


class TransporteLoL(unittest.TestCase):
    def test_solo_loopback_rutas_fijas_sin_proxy_y_secreto_fuera_repr(self):
        cred=Credenciales(12345,'secreto-falso');cliente=ClienteLCU(lambda:cred)
        respuesta=Mock();respuesta.__enter__=Mock(return_value=respuesta);respuesta.__exit__=Mock();respuesta.read.return_value=b'"Lobby"'
        cliente.abridor=Mock();cliente.abridor.open.return_value=respuesta
        self.assertEqual(cliente.pedir('GET',FASE),'Lobby')
        peticion=cliente.abridor.open.call_args.args[0]
        self.assertEqual(peticion.full_url,'https://127.0.0.1:12345'+FASE)
        self.assertEqual(peticion.get_header('Authorization'),'Basic '+base64.b64encode(b'riot:secreto-falso').decode())
        # Consultar de nuevo no lanza otro descubrimiento de credenciales.
        with patch.object(cliente,'descubrir') as descubrir_de_nuevo:
            cliente.pedir('GET',FASE);descubrir_de_nuevo.assert_not_called()
        self.assertNotIn('secreto',repr(cred))
        for metodo,ruta in [('POST','/lol-champ-select/v1/session'),('GET','https://example.com'),('GET','//example.com')]:
            with self.assertRaises(ValueError):cliente.pedir(metodo,ruta)
        self.assertEqual(cliente.abridor.open.call_count,2)

    def test_credenciales_invalidas_y_errores_no_filtran_token(self):
        for puerto,secreto in [(0,'abc'),(65536,'abc'),(12,''),(12,'a\nb')]:
            with self.assertRaises(ErrorCliente):Credenciales(puerto,secreto)
        cliente=ClienteLCU(lambda:Credenciales(12345,'token-privado'))
        cliente.abridor=Mock();cliente.abridor.open.side_effect=urllib.error.HTTPError('https://127.0.0.1',401,'token-privado',{},None)
        with self.assertRaises(ErrorCliente) as e:cliente.pedir('GET',FASE)
        self.assertNotIn('token-privado',str(e.exception));self.assertIsNone(cliente._credenciales)

    def test_descubrimiento_con_argumentos_no_imprime_ni_persiste_token(self):
        datos={'ProcessId':123,'ExecutablePath':None,'CommandLine':'LeagueClientUx.exe --app-port=34567 --remoting-auth-token=falso'}
        with patch('league.subprocess.run',return_value=Mock(stdout=json.dumps(datos))) as ejecutar:
            self.assertEqual(descubrir(),Credenciales(34567,'falso'))
            self.assertNotIn('falso',repr(ejecutar.call_args))
        with patch('league.subprocess.run',return_value=Mock(stdout='null')):
            with self.assertRaises(ErrorCliente) as e:descubrir()
            self.assertEqual(e.exception.clave,'cliente')


if __name__=='__main__':unittest.main()
