"""Intención y contexto local: el modelo elige acciones, nunca escribe código."""
from collections import deque
from dataclasses import dataclass
import json
import re
import time
import urllib.request
from core import Orden,APPS,normalizar,url_solicitada

ACCIONES=('spotify','spotify_pausa','spotify_siguiente','spotify_anterior',
          'spotify_estado','spotify_playlist','spotify_buscar','abrir','buscar','pestana','carpeta')
SIN_ARGUMENTO=('charla','aclarar','spotify_pausa','spotify_siguiente','spotify_anterior','spotify_estado')
def esquema_accion(acciones,valor):
    return {'type':'object','additionalProperties':False,'required':['accion','valor'],
            'properties':{'accion':{'type':'string','enum':list(acciones)},'valor':valor}}
ESQUEMA={'oneOf':[esquema_accion(SIN_ARGUMENTO,{'type':'string','const':''}),
                  esquema_accion([a for a in ACCIONES if a not in SIN_ARGUMENTO],{'type':'string','maxLength':500})]}
SISTEMA='''Eres el interprete de intencion de Capri. Lee mensaje y contexto y devuelve SOLO JSON.
No converses ni confirmes ejecucion. accion=charla para conversacion, aclarar si falta el referente.
Acciones con valor VACIO: spotify (reanudar musica), spotify_pausa, spotify_siguiente, spotify_anterior, spotify_estado, charla, aclarar.
spotify_pausa significa parar/detener la musica, hacer que deje de sonar, basta de musica por ahora.
spotify_siguiente significa cambiar a otra cancion de la cola; spotify_anterior volver a la de antes.
Reconoce peticiones indirectas: no necesitan empezar con un verbo de comando.
Acciones con valor extraido del mensaje: spotify (titulo de cancion), spotify_playlist (nombre), spotify_buscar (consulta), abrir (app), buscar (consulta web), pestana (URL o vacio), carpeta.
Apps: opera, opera gx, navegador, calculadora, bloc de notas, explorador, spotify, youtube.
Carpetas: Downloads, Documents, Desktop, Pictures, Music, Videos.
No inventes parametros. Puedes reutilizar el valor del ultimo objetivo explicito.
Si tema_activo=spotify, resuelve pronombres y frases cortas con ese tema. Sin referente claro, aclarar.
Si el ultimo resultado pide aclaracion, une la respuesta actual con la peticion que quedo pendiente.
No actuar ante negaciones, ejemplos, citas, explicaciones, opiniones ni peticiones de varias acciones.
Una peticion indirecta de parar la musica SI es accion, aunque incluya «por ahora» o «un ratito».
EJEMPLOS DE SALIDAS EXACTAS:
Mensaje: deten la cancion -> {"accion":"spotify_pausa","valor":""}
Mensaje: me puedes detener lo que esta sonando -> {"accion":"spotify_pausa","valor":""}
Tema spotify, mensaje: detenla un momento -> {"accion":"spotify_pausa","valor":""}
Tema spotify, mensaje: ahora sigue -> {"accion":"spotify","valor":""}
Tema spotify, mensaje: pon otra -> {"accion":"spotify_siguiente","valor":""}
Tema spotify, mensaje: mejor la anterior -> {"accion":"spotify_anterior","valor":""}
Tema spotify, mensaje: prefiero la de antes -> {"accion":"spotify_anterior","valor":""}
Sin tema, mensaje: ahora sigue -> {"accion":"aclarar","valor":""}
Contexto: el usuario dijo «detenla», Capri pregunto a que se refiere. Mensaje: la cancion -> {"accion":"spotify_pausa","valor":""}
Mensaje: quiero volver a escuchar lo que estaba puesto -> {"accion":"spotify","valor":""}
Mensaje: puedes poner mi lista juntos -> {"accion":"spotify_playlist","valor":"juntos"}
Mensaje: abre el navegador que uso -> {"accion":"abrir","valor":"navegador"}
Mensaje: como se pausa Spotify -> {"accion":"charla","valor":""}
Mensaje: no detengas la musica -> {"accion":"charla","valor":""}
Mensaje: cuentame algo -> {"accion":"charla","valor":""}'''

@dataclass(frozen=True)
class Decision:
    orden: object = None
    pregunta: str = ''

def protegida(texto):
    n=normalizar(texto).strip(' ¿?¡!')
    return bool(re.search(r'\b(?:no|nunca|jamas)\b',n) or
                re.match(r'^(?:como\b|explica\b|explicame\b|traduce\b|que significa\b|si digo\b|dije\b|la frase\b|imagina\b)',n) or
                texto.lstrip().startswith(('"','«','“',"'")))

def requiere_contexto(orden):
    if orden is None or orden.tipo in ('no_admitida','desconocida'):return True
    if orden.tipo=='spotify' and orden.valor:
        valor=normalizar(orden.valor)
        return bool(re.match(r'^(?:otr[ao]|es[ao]|es[ao]s|la misma|lo mismo|lo de|la de|algo diferente)\b',valor) or valor in APPS)
    return False

def ultimo_tema(turnos):
    for turno in reversed(turnos):
        if not turno['accion'] and re.fullmatch(r'(?:gracias|muchas gracias|ok|vale|bien|perfecto|genial|listo)[.! ]*',normalizar(turno['peticion'])):continue
        return turno
    return {}

class Interprete:
    def __init__(self):
        self.turnos=deque(maxlen=4)

    def registrar(self,texto,orden,resultado,aclaracion=False):
        self.turnos.append({'peticion':texto[:240],'accion':orden.tipo if orden else '',
                            'valor':orden.valor if orden else '', 'resultado':resultado[:240],
                            'aclaracion':bool(aclaracion),'momento':time.monotonic()})

    def contexto(self):
        recientes=[{k:v for k,v in t.items() if k!='momento'} for t in self.turnos
                   if time.monotonic()-t['momento']<180]
        tema='spotify' if ultimo_tema(recientes).get('accion','').startswith('spotify') else ''
        return {'tema_activo':tema,'turnos':recientes}

    def validar(self,datos,texto,contexto):
        aclarar=Decision(pregunta='¿A qué te refieres? Dime qué quieres controlar o cambiar.')
        if not isinstance(datos,dict) or set(datos)!={'accion','valor'}:return aclarar
        accion=datos['accion'];valor=datos['valor']
        if not all(isinstance(v,str) for v in (accion,valor)):return aclarar
        if accion=='charla':return Decision()
        if accion not in ACCIONES:return aclarar
        if protegida(texto):return Decision()
        if re.search(r'\b(?:y luego|despues de eso|primero.+luego)\b',normalizar(texto)):return aclarar
        valor=valor.strip()
        if len(valor)>500 or any(ord(c)<32 for c in valor):return aclarar
        n=normalizar(texto)
        if accion.startswith('spotify'):
            if not re.search(r'\b(?:spotify|musica|cancion|canciones|tema|pista|playlist|lista|reproduccion|sonando|reproductor)\b',n) and contexto['tema_activo']!='spotify':return aclarar
        if accion in ('spotify_pausa','spotify_siguiente','spotify_anterior','spotify_estado'):
            return Decision(Orden(accion)) if not valor else aclarar
        if accion=='spotify' and not valor:return Decision(Orden(accion))
        if accion=='pestana' and not valor:return Decision(Orden(accion))
        # Los parámetros nuevos deben estar en las palabras del usuario. Solo se
        # permite reutilizar el objetivo del último turno activo, no uno remoto.
        ultimo=ultimo_tema(contexto['turnos'])
        reutiliza=ultimo.get('accion')==accion and ultimo.get('valor')==valor
        if accion=='abrir':
            valor=normalizar(valor)
            if valor not in APPS:return aclarar
            if valor not in n and not (valor=='navegador' and 'navegador' in n):return aclarar
        elif accion=='carpeta':
            nombres={'Downloads':('descargas',),'Documents':('documentos',),'Desktop':('escritorio',),
                     'Pictures':('imagenes','fotos'),'Music':('musica',),'Videos':('videos',)}
            if valor not in nombres or not any(x in n for x in nombres[valor]):return aclarar
        elif accion=='pestana':
            if not valor or normalizar(valor) not in n:return aclarar
            valor=url_solicitada(valor)
            if not valor:return aclarar
        elif not valor or (normalizar(valor) not in n and not reutiliza):return aclarar
        return Decision(Orden(accion,valor))

    def resolver(self,texto,modelo,cancelar=None):
        if cancelar and cancelar.is_set():raise InterruptedError('Interpretación cancelada.')
        if protegida(texto):return Decision()
        contexto=self.contexto()
        if not modelo:return Decision(pregunta='Necesito la IA local activada para entender esa petición con contexto.')
        mensajes=[{'role':'system','content':SISTEMA+'\nTema activo actual: '+(contexto['tema_activo'] or 'ninguno')+'.'}]
        for turno in contexto['turnos']:
            mensajes.append({'role':'user','content':turno['peticion']})
            if turno.get('aclaracion'):
                contenido=turno['resultado']
            else:
                contenido=json.dumps({'accion_anterior':turno['accion'],'valor':turno['valor'],'resultado_real':turno['resultado']},ensure_ascii=False)
            mensajes.append({'role':'assistant','content':contenido})
        mensajes.append({'role':'user','content':texto})
        cuerpo={'model':modelo,'stream':False,'format':ESQUEMA,'keep_alive':'15m',
                'messages':mensajes,
                'options':{'temperature':0,'num_ctx':2048,'num_predict':100}}
        if modelo.lower().startswith('qwen3'):cuerpo['think']=False
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',
                data=json.dumps(cuerpo).encode('utf-8'),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=30) as r:respuesta=json.load(r)
            datos=json.loads(respuesta.get('message',{}).get('content',''))
        except (ValueError,AttributeError):
            return Decision(pregunta='No entendí con seguridad qué quieres hacer. ¿Me lo dices de otra manera?')
        if cancelar and cancelar.is_set():raise InterruptedError('Interpretación cancelada.')
        return self.validar(datos,texto,contexto)
