"""Puente local con la extensión Capri. HTTP solo transporta tareas creadas aquí."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import re
import threading
import time
import uuid

PUERTO=18741
EXTENSION_ID='hcikngipgcmgdmibkilomnedmhpgdnob'
ORIGEN='chrome-extension://'+EXTENSION_ID

def validar(accion,datos):
    if accion=='resultado':return set(datos)=={'indice'} and type(datos['indice']) is int and 1<=datos['indice']<=10
    if accion in ('pausa','reanudar','siguiente','anterior','estado'):return datos=={}
    if accion!='volumen' or set(datos)!={'operacion','restaurar'}:return False
    op=datos['operacion'];valor=datos['restaurar']
    if not isinstance(op,str) or not isinstance(valor,(int,float)) or not 0<=valor<=100:return False
    m=re.fullmatch(r'(subir|bajar|fijar):(\d{1,3})',op)
    return bool((m and int(m[2])<=100) or op in ('silenciar','activar','consultar'))

class Puente:
    def __init__(self,puerto=PUERTO):
        self.lock=threading.Lock();self.pendientes={};self.ultimo=0;self.servidor=None
        self.error=''
        propietario=self
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup();self.connection.settimeout(2)
            def log_message(self,*args):pass
            def permitido(self):
                return (self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port)
                        and self.headers.get('Origin') in (None,ORIGEN)
                        and self.headers.get('X-Capri-Puente')==EXTENSION_ID)
            def responder(self,estado,datos):
                cuerpo=json.dumps(datos,allow_nan=False).encode('utf8')
                self.send_response(estado);self.send_header('Content-Type','application/json; charset=utf-8')
                self.send_header('Cache-Control','no-store')
                if self.headers.get('Origin')==ORIGEN:self.send_header('Access-Control-Allow-Origin',ORIGEN)
                self.send_header('Content-Length',str(len(cuerpo)));self.end_headers();self.wfile.write(cuerpo)
            def do_OPTIONS(self):
                if self.headers.get('Origin')!=ORIGEN:
                    self.responder(403,{});return
                self.send_response(204);self.send_header('Access-Control-Allow-Origin',ORIGEN)
                self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers','X-Capri-Puente, Content-Type')
                self.end_headers()
            def do_GET(self):
                if not self.permitido():self.responder(403,{});return
                if self.path!='/siguiente':self.responder(404,{});return
                tarea=None
                with propietario.lock:
                    propietario.ultimo=time.monotonic()
                    for id,p in propietario.pendientes.items():
                        if not p['entregada'] and time.monotonic()<p['vence']:
                            p['entregada']=True;tarea={'id':id,'accion':p['accion'],'datos':p['datos']};break
                self.responder(200,{'tarea':tarea})
            def do_POST(self):
                try:
                    cantidad=int(self.headers.get('Content-Length','0'))
                    if not 0<cantidad<=4096:raise ValueError()
                    # Consumir el cuerpo acotado antes de rechazar evita un RST en Windows.
                    cuerpo=self.rfile.read(cantidad)
                    if not self.permitido():self.responder(403,{});return
                    if self.path!='/resultado':self.responder(404,{});return
                    if self.headers.get_content_type()!='application/json':raise ValueError()
                    datos=json.loads(cuerpo);id=datos['id'];resultado=datos['resultado']
                    if not isinstance(resultado,dict) or type(resultado.get('ok')) is not bool:raise ValueError()
                    limpio={'ok':resultado['ok']}
                    for campo in ('volumen','anterior'):
                        if campo in resultado:
                            v=resultado[campo]
                            if type(v) not in (float,int) or not 0<=v<=100:raise ValueError()
                            limpio[campo]=v
                    if 'silenciado' in resultado:
                        if type(resultado['silenciado']) is not bool:raise ValueError()
                        limpio['silenciado']=resultado['silenciado']
                    if resultado.get('estado') in ('Playing','Paused','Solicitado'):limpio['estado']=resultado['estado']
                    if resultado.get('codigo') in ('sin_video','sin_control','pagina_invalida','operacion_invalida','reproduccion_bloqueada','cambio_no_confirmado','varios_videos','sin_resultados','varios_resultados','resultado_no_disponible'):
                        limpio['codigo']=resultado['codigo']
                    with propietario.lock:
                        p=propietario.pendientes.get(id)
                        if not p or not p['entregada'] or time.monotonic()>=p['vence'] or p['evento'].is_set():
                            self.responder(409,{});return
                        p['resultado']=limpio;p['evento'].set()
                    self.responder(200,{'ok':True})
                except (ValueError,TypeError,KeyError):self.responder(400,{})
        class Servidor(ThreadingHTTPServer):
            daemon_threads=True
            allow_reuse_address=False
        try:
            self.servidor=Servidor(('127.0.0.1',puerto),Handler)
            self.hilo=threading.Thread(target=self.servidor.serve_forever,kwargs={'poll_interval':.1},daemon=True)
            self.hilo.start()
        except OSError:self.error='El puerto local de la conexión con Opera está ocupado.'

    def conectado(self):return bool(self.servidor and self.ultimo and time.monotonic()-self.ultimo<4)

    def ejecutar(self,accion,datos,espera=4):
        if not validar(accion,datos):raise ValueError('Operación del puente no válida.')
        if not self.conectado():return None
        id=uuid.uuid4().hex
        p={'accion':accion,'datos':dict(datos),'vence':time.monotonic()+espera,'entregada':False,
           'evento':threading.Event(),'resultado':None}
        with self.lock:self.pendientes[id]=p
        try:
            if p['evento'].wait(espera):return p['resultado']
            return {'ok':False,'codigo':'cambio_no_confirmado'}
        finally:
            with self.lock:self.pendientes.pop(id,None)

    def cerrar(self):
        if self.servidor:self.servidor.shutdown();self.servidor.server_close();self.servidor=None
        with self.lock:
            for p in self.pendientes.values():p['resultado']={'ok':False,'codigo':'cambio_no_confirmado'};p['evento'].set()

_puente=None

def iniciar():
    global _puente
    if _puente is None:_puente=Puente()
    return _puente

def ejecutar(accion,datos=None):
    return _puente.ejecutar(accion,datos or {}) if _puente else None

def cerrar():
    global _puente
    if _puente:_puente.cerrar();_puente=None

def mensaje_error(resultado):
    return {'sin_video':'No encontré un vídeo cargado en la pestaña de YouTube.',
            'sin_resultados':'No encontré una página de resultados de YouTube. Haz primero una búsqueda en YouTube.',
            'varios_resultados':'Hay varias búsquedas de YouTube abiertas. Selecciona la pestaña de resultados que quieres usar.',
            'resultado_no_disponible':'Ese resultado no está disponible entre los vídeos de esta búsqueda de YouTube.',
            'varios_videos':'Hay varios vídeos de YouTube disponibles. Selecciona la pestaña del que quieres controlar y repite la orden.',
            'sin_control':'Ese vídeo no ofrece el control solicitado.',
            'pagina_invalida':'La pestaña seleccionada no es YouTube.',
            'reproduccion_bloqueada':'YouTube bloqueó el inicio automático; inicia el vídeo una vez.',
            'operacion_invalida':'La operación del reproductor no es válida.'}.get(resultado.get('codigo'),
            'YouTube no confirmó el cambio; no repetí la orden para evitar ejecutarla dos veces.')
