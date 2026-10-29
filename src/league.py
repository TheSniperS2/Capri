"""Cola y ready-check del cliente local de LoL; sin controles dentro de partida."""
from dataclasses import dataclass, field
from pathlib import Path
import base64
import json
import os
import re
import ssl
import subprocess
import threading
import unicodedata
import urllib.error
import urllib.request

FASE='/lol-gameflow/v1/gameflow-phase'
SALA='/lol-lobby/v2/lobby'
COLA=SALA+'/matchmaking/search'
LISTO='/lol-matchmaking/v1/ready-check'
ACEPTAR=LISTO+'/accept'
PERMITIDOS={('GET',FASE),('GET',SALA),('GET',LISTO),('POST',COLA),('DELETE',COLA),('POST',ACEPTAR)}
ACCIONES=('lol_buscar','lol_cancelar','lol_aceptar','lol_auto_activar','lol_auto_desactivar')


def interpretar_lol(texto):
    """Solo peticiones completas; nunca extraer acciones de citas o búsquedas."""
    n=''.join(c for c in unicodedata.normalize('NFD',texto.lower()) if unicodedata.category(c)!='Mn').strip(' .!?¿¡')
    n=re.sub(r'^(?:please |can you |could you |por favor[, ]+|voce pode )','',n)
    n=re.sub(r'[, ]+(?:por favor|please)$','',n)
    juego=r'(?:\s+(?:en|de|del|no|do|in|on)\s+(?:el\s+|o\s+|the\s+)?(?:lol|league(?: of legends)?))?'
    auto=r'(?:\s+(?:y acepta(?:la)?(?: por mi)?|y acepta automaticamente|e aceite(?: por mim)?|and (?:auto[ -]?)?accept(?: (?:it|for me|automatically))?))?'
    buscar=r'(?:busca(?:r)? (?:una |la )?partida|(?:tira|tirar|pon|poner|inicia|iniciar) (?:la )?cola|bus(?:que|car) (?:uma )?partida|(?:inicie|iniciar|entre na) (?:a )?fila|(?:find|search for) (?:a )?match|(?:start|join) (?:the )?queue|queue up)'
    if re.fullmatch(buscar+juego+auto,n):
        return ('lol_buscar','auto' if re.search(r'\b(?:acepta|aceptala|aceite|accept)\b',n) else '')
    if n in ('マッチを検索して','マッチングを開始して'):return ('lol_buscar','')
    if re.fullmatch(r'(?:acepta(?:r)? (?:la )?(?:partida|cola)|aceite (?:a )?partida|accept (?:the )?(?:match|ready check))'+juego,n) or n=='マッチを承諾して':return ('lol_aceptar','')
    if re.fullmatch(r'(?:cancela(?:r)? (?:la )?(?:cola|busqueda de partida)|sal de (?:la )?cola|cancele (?:a )?fila|cancel (?:the )?(?:queue|matchmaking))'+juego,n) or n=='マッチングをキャンセルして':return ('lol_cancelar','')
    if n in ('desactiva la aceptacion automatica del lol','no aceptes mas partidas','disable auto accept in lol','desative a aceitacao automatica no lol','自動承諾を停止して'):return ('lol_auto_desactivar','')
    if n in ('activa la aceptacion automatica del lol','acepta las partidas automaticamente','acepta las partidas por mi','vigila la cola del lol','enable auto accept in lol','auto accept my matches','ative a aceitacao automatica no lol','自動承諾を有効にして'):return ('lol_auto_activar','')
    return None


class ErrorCliente(Exception):
    def __init__(self,clave='conexion'):
        self.clave=clave
        super().__init__(clave)


@dataclass(frozen=True)
class Credenciales:
    puerto:int
    secreto:str=field(repr=False)

    def __post_init__(self):
        if not 1<=self.puerto<=65535 or not self.secreto or len(self.secreto)>512 or any(c.isspace() for c in self.secreto):raise ErrorCliente('conexion')


def descubrir():
    if os.name!='nt':raise ErrorCliente('cliente')
    # stdout queda solo en memoria: los argumentos pueden contener el token LCU.
    comando="Get-CimInstance Win32_Process -Filter \"Name='LeagueClientUx.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    try:
        p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',comando],capture_output=True,
                         encoding='utf-8',errors='replace',timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        procesos=json.loads(p.stdout or 'null')
        if not procesos:raise ErrorCliente('cliente')
        if isinstance(procesos,dict):procesos=[procesos]
        # No escoger arbitrariamente una cuenta si hay varios clientes abiertos.
        if len(procesos)!=1:raise ErrorCliente('varios')
        proceso=procesos[0];ruta=proceso.get('ExecutablePath')
        if ruta:
            lock=Path(ruta).parent/'lockfile'
            if lock.is_file():
                partes=lock.read_text(encoding='utf8').strip().split(':')
                if len(partes)==5 and partes[0]=='LeagueClient' and partes[4]=='https':return Credenciales(int(partes[2]),partes[3])
        argumentos=proceso.get('CommandLine') or ''
        puerto=re.search(r'--app-port[= ](\d+)',argumentos)
        token=re.search(r'--remoting-auth-token[= ]([^\s"]+)',argumentos)
        if puerto and token:return Credenciales(int(puerto[1]),token[1])
    except ErrorCliente:raise
    except (OSError,ValueError,TypeError,subprocess.SubprocessError):pass
    raise ErrorCliente('conexion')


class SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class ClienteLCU:
    def __init__(self,credenciales=descubrir):
        self.descubrir=credenciales;self._credenciales=None
        # El certificado autofirmado solo se admite para este origen loopback
        # fijo. No hay proxies, redirecciones ni URLs proporcionadas por la IA.
        contexto=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        contexto.check_hostname=False;contexto.verify_mode=ssl.CERT_NONE
        self.abridor=urllib.request.build_opener(urllib.request.ProxyHandler({}),SinRedireccion(),urllib.request.HTTPSHandler(context=contexto))

    def pedir(self,metodo,ruta):
        if (metodo,ruta) not in PERMITIDOS:raise ValueError('Acción LCU no permitida.')
        # Las credenciales duran hasta cerrar el cliente. No volver a lanzar
        # PowerShell durante un ready-check si la conexión sigue funcionando.
        if self._credenciales is None:
            self._credenciales=self.descubrir()
        cred=self._credenciales
        autorizacion=base64.b64encode(('riot:'+cred.secreto).encode()).decode()
        peticion=urllib.request.Request(f'https://127.0.0.1:{cred.puerto}{ruta}',method=metodo,
            headers={'Authorization':'Basic '+autorizacion,'Accept':'application/json'},data=b'' if metodo=='POST' else None)
        try:
            with self.abridor.open(peticion,timeout=3) as respuesta:
                cuerpo=respuesta.read(1024*1024)
                return json.loads(cuerpo) if cuerpo else None
        except urllib.error.HTTPError as e:
            if e.code in (401,403):self._credenciales=None
            raise ErrorCliente('rechazo' if e.code in (400,403,409,422) else 'conexion') from None
        except (OSError,ValueError,urllib.error.URLError):
            self._credenciales=None
            raise ErrorCliente('conexion') from None


MENSAJES={
    'cliente':'Abre el cliente de League of Legends y prepara una sala primero.',
    'conexion':'No pude conectar con el cliente local de LoL. Comprueba que esté abierto con los mismos permisos que Capri.',
    'varios':'Hay varios clientes de LoL abiertos. Deja uno solo para elegir la cuenta sin confusiones.',
    'rechazo':'LoL rechazó la acción. Revisa la sala, el líder del grupo y los avisos del cliente.',
    'sala':'Prepara una sala y elige el modo en LoL. Buscaré con esa selección.',
    'partida':'Ya estás en selección de campeón o en partida. No cambié la cola.',
    'buscando':'La búsqueda de partida está en marcha en LoL.',
    'auto':'La búsqueda está en marcha. Aceptaré cuando aparezca la partida; me detendré al entrar en selección de campeón.',
    'solicitud':'Envié la solicitud de búsqueda a LoL, pero aún no confirmó que esté en cola.',
    'cancelada':'LoL confirmó que la búsqueda de partida está cancelada.',
    'cancelando':'Pedí cancelar la búsqueda; el cliente aún no confirmó la salida de la cola.',
    'sin_cola':'No hay una búsqueda en marcha en LoL.',
    'lista':'Hay una partida lista para aceptar en LoL.',
    'no_cancelable':'Ya apareció una partida. Para rechazarla, usa el cliente de LoL.',
    'sin_lista':'Todavía no hay una partida lista para aceptar en LoL.',
    'aceptada':'LoL confirmó que aceptaste la partida.',
    'aceptando':'Envié la aceptación a LoL, pero aún no pude confirmar el resultado.',
    'desactivada':'Desactivé la aceptación automática de LoL.',
    'activada':'Vigilaré las colas de LoL y aceptaré cuando aparezca una partida, aunque busques desde el propio cliente.',
    'auto_apagado':'Aceptación automática desactivada',
    'auto_esperando':'Vigilancia activa · esperando una cola de LoL',
    'auto_vigilando':'En cola · pendiente de aceptar la partida',
    'auto_partida':'Vigilancia activa · esperando la siguiente cola',
    'auto_conexion':'Vigilancia activa · esperando conexión con LoL',
    'auto_confirmando':'Aceptación enviada · comprobando LoL',
    'auto_error':'Detuve la aceptación automática porque perdí la conexión con LoL. Puedes aceptar desde el cliente.',
}


class ControlLoL:
    def __init__(self,cliente=None,avisar=None):
        self.cliente=cliente or ClienteLCU();self.avisar=avisar or (lambda mensaje:None)
        self._stop=threading.Event();self._stop.set();self._lock=threading.RLock()
        self.hilo=None;self._aceptado=False
        self.permanente=False;self.estado=MENSAJES['auto_apagado'];self._omitir_ready=False
        self._estado_ready=MENSAJES['auto_confirmando']

    def detener_auto(self):
        self._stop.set();self.permanente=False;self.estado=MENSAJES['auto_apagado']
    cerrar=detener_auto

    def activar_auto(self):
        # Activar/desactivar desde Tk no espera a una petición de red en curso.
        if self.permanente and not self._stop.is_set() and self.hilo and self.hilo.is_alive():return
        self._iniciar_auto(permanente=True)

    def _fase(self):
        fase=self.cliente.pedir('GET',FASE)
        if not isinstance(fase,str):raise ErrorCliente()
        return fase

    def _aceptar(self,cancelar=None):
        if self._fase()!='ReadyCheck':return 'sin_lista'
        listo=self.cliente.pedir('GET',LISTO) or {}
        if not isinstance(listo,dict):raise ErrorCliente()
        if listo.get('playerResponse')=='Accepted':return 'aceptada'
        if listo.get('state')!='InProgress' or listo.get('playerResponse') not in ('None',None):return 'sin_lista'
        if cancelar and cancelar.is_set():raise InterruptedError()
        self.cliente.pedir('POST',ACEPTAR)
        try:
            if self._fase()=='ChampSelect':return 'aceptada'
            if (self.cliente.pedir('GET',LISTO) or {}).get('playerResponse')=='Accepted':return 'aceptada'
        except ErrorCliente:pass
        return 'aceptando'

    def ejecutar(self,accion,valor='',automatico=False,cancelar=None):
        if accion not in ACCIONES:raise ValueError('Acción de LoL desconocida.')
        if cancelar and cancelar.is_set():raise InterruptedError()
        if accion=='lol_auto_desactivar':self.detener_auto();return MENSAJES['desactivada']
        if accion=='lol_auto_activar':self.activar_auto();return MENSAJES['activada']
        with self._lock:
            try:
                if accion=='lol_aceptar':
                    resultado=self._aceptar(cancelar)
                    if resultado in ('aceptada','aceptando'):self._aceptado=True
                    self._estado_ready=MENSAJES[resultado]
                    return MENSAJES[resultado]
                if not self.permanente:self.detener_auto()
                fase=self._fase()
                if cancelar and cancelar.is_set():raise InterruptedError()
                if fase in ('ChampSelect','InProgress','GameStart','Reconnect'):return MENSAJES['partida']
                if accion=='lol_cancelar':
                    if fase=='ReadyCheck':self._omitir_ready=True;return MENSAJES['no_cancelable']
                    if fase!='Matchmaking':return MENSAJES['sin_cola']
                    self.cliente.pedir('DELETE',COLA)
                    try:confirmada=self._fase() not in ('Matchmaking','ReadyCheck')
                    except ErrorCliente:confirmada=False
                    return MENSAJES['cancelada' if confirmada else 'cancelando']
                if fase not in ('Matchmaking','ReadyCheck'):
                    if fase!='Lobby' or not self.cliente.pedir('GET',SALA):return MENSAJES['sala']
                    if cancelar and cancelar.is_set():raise InterruptedError()
                    self.cliente.pedir('POST',COLA)
                    try:fase=self._fase()
                    except ErrorCliente:return MENSAJES['solicitud']
                if fase not in ('Matchmaking','ReadyCheck'):return MENSAJES['solicitud']
                if automatico or valor=='auto':
                    if not self.permanente:self._iniciar_auto()
                    return MENSAJES['activada' if self.permanente else 'auto']
                return MENSAJES['lista' if fase=='ReadyCheck' else 'buscando']
            except ErrorCliente as e:return MENSAJES.get(e.clave,MENSAJES['conexion'])

    def _iniciar_auto(self,permanente=False):
        self._stop.set()
        stop=self._stop=threading.Event();self._aceptado=False;self._omitir_ready=False
        self.permanente=permanente;self.estado=MENSAJES['auto_esperando']
        self.hilo=threading.Thread(target=self._vigilar,args=(stop,permanente),daemon=True,name='Capri-LoL-ready-check');self.hilo.start()

    def revisar_auto(self,stop,permanente=False):
        """Un paso comprobable sin esperas ni llamadas reales en las pruebas."""
        with self._lock:
            if stop.is_set():return
            fase=self._fase()
            if stop.is_set():return
            if fase!='ReadyCheck':self._omitir_ready=False
            if fase not in ('Matchmaking','ReadyCheck'):
                self._aceptado=False
                self.estado=MENSAJES['auto_partida' if fase in ('ChampSelect','InProgress','GameStart','Reconnect') else 'auto_esperando']
                if not permanente:stop.set();self.estado=MENSAJES['auto_apagado']
                return 3 if fase in ('ChampSelect','InProgress','GameStart','Reconnect') else 1
            self.estado=MENSAJES['auto_vigilando']
            if fase=='Matchmaking':self._aceptado=False;return .25
            if self._omitir_ready:return .25
            if not self._aceptado and not stop.is_set():
                resultado=self._aceptar(stop)
                if stop.is_set():return
                if resultado in ('aceptada','aceptando'):
                    self._aceptado=True
                    self._estado_ready=MENSAJES[resultado]
                    if not stop.is_set():self.avisar(MENSAJES[resultado])
            if self._aceptado:self.estado=self._estado_ready
            return .25

    def _vigilar(self,stop,permanente=False):
        # Primera consulta inmediata. La aceptación no pasa por voz, IA ni Tk.
        while not stop.is_set():
            try:demora=self.revisar_auto(stop,permanente) or .25
            except InterruptedError:return
            except ErrorCliente:
                if stop.is_set():return
                if permanente:
                    self.estado=MENSAJES['auto_conexion'];demora=2
                else:
                    self.avisar(MENSAJES['auto_error']);stop.set();self.estado=MENSAJES['auto_apagado'];return
            if stop.wait(demora):return
