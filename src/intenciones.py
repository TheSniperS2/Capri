"""Intención y contexto local: el modelo elige acciones, nunca escribe código."""
from collections import deque
from dataclasses import dataclass
import json
import re
import time
import urllib.request
from core import Orden,APPS,normalizar,url_solicitada,limpiar_peticion,ABRIR

ACCIONES=('spotify','spotify_pausa','spotify_siguiente','spotify_anterior',
          'spotify_estado','spotify_playlist','spotify_playlist_cancion','spotify_buscar','spotify_volumen','abrir','buscar','pestana','carpeta',
          'youtube_buscar','youtube_video','youtube_resultado','youtube_siguiente','youtube_anterior','youtube_pausa','youtube_reanudar','youtube_volumen','spotify_playlist_pendiente')
SIN_ARGUMENTO=('charla','aclarar','spotify_pausa','spotify_siguiente','spotify_anterior','spotify_estado',
               'youtube_siguiente','youtube_anterior','youtube_pausa','youtube_reanudar')
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
Si pide una canción dentro de una playlist, spotify_playlist_cancion usa valor como JSON con claves cancion y nombre, extraídos literalmente del mensaje. Nunca convertirlo en búsqueda general de Spotify.
Apps: opera, opera gx, navegador, calculadora, bloc de notas, explorador, spotify, youtube.
Sitios conocidos (pestana con valor nombre): youtube, netflix, twitch, crunchyroll, disney plus, prime video, github, reddit, steam, google, wikipedia. Buscar un nombre exacto de sitio es navegar; buscar opiniones o buscar en Google es buscar. Nunca programa_abrir para una búsqueda web.
spotify_volumen: valor subir:10 o bajar:10 (diez puntos), fijar:50 para un porcentaje explícito, silenciar, activar o consultar. Mueve el deslizador interno de Spotify.
youtube_volumen: mismos valores para el deslizador del reproductor de YouTube. "Sube el volumen del vídeo" se refiere a YouTube; sin nombre usa el tema activo.
youtube_buscar lleva consulta literal: una petición con «en YouTube» abre resultados para elegir. youtube_video conserva la reproducción directa de un vídeo por título cuando se pide sin esa búsqueda por servicio.
youtube_resultado lleva un número de 1 a 10 expresamente solicitado: primer vídeo=1, segundo=2. Selecciona resultados existentes, sin buscar el ordinal como título. El servicio explícito del mensaje siempre gana frente al tema anterior. spotify_playlist_pendiente conserva la canción y pide el nombre de la playlist; nunca sustituirlo por búsqueda general.
youtube_siguiente, youtube_anterior, youtube_pausa, youtube_reanudar llevan valor vacío. Si tema_activo=youtube, siguiente video o paúsalo controlan YouTube, no Spotify.
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

def nombre_playlist_respuesta(texto):
    """Extrae el nombre de una aclaración sin incluir sus palabras de enlace."""
    texto=texto.strip()
    prefijo=r'^(?:(?:de|en|desde|dentro de)\s+)?(?:(?:mi|la|esa)\s+)?(?:playlist|lista(?: de reproducci[oó]n)?)(?:\s+(?:(?:que\s+)?se llama|llamada))?\s+'
    texto=re.sub(prefijo,'',texto,flags=re.I)
    texto=re.sub(r'^(?:se llama|es|la que se llama)\s+','',texto,flags=re.I)
    return texto.strip(' «»\"\'“”.!?')

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
        ultimo=ultimo_tema(recientes)
        tema='spotify' if ultimo.get('accion','').startswith('spotify') else ''
        if ultimo.get('accion','').startswith('youtube_') or (ultimo.get('accion') in ('pestana','abrir') and 'youtube' in ultimo.get('valor','')):tema='youtube'
        return {'tema_activo':tema,'turnos':recientes}

    def ajustar_orden(self,texto,orden,control_ampliado=False):
        if protegida(texto):return orden
        t=limpiar_peticion(texto);n=normalizar(t).strip(' .!')
        ultimo=ultimo_tema(self.contexto()['turnos'])
        if orden and orden.tipo=='spotify_playlist_pendiente':
            datos=json.loads(orden.valor)
            for turno in reversed(self.contexto()['turnos']):
                if turno['accion']=='spotify_playlist':datos['nombre']=turno['valor'];break
                if turno['accion']=='spotify_playlist_cancion':
                    datos['nombre']=json.loads(turno['valor'])['nombre'];break
            return Orden('spotify_playlist_cancion' if datos['nombre'] else 'spotify_playlist_pendiente',json.dumps(datos,ensure_ascii=False))
        if ultimo.get('accion') in ('spotify_playlist_pendiente','spotify_playlist_cancion') and orden is None:
            datos=json.loads(ultimo['valor'])
            nombre=nombre_playlist_respuesta(texto) if not datos['nombre'] else texto.strip(' «»\"\'“”.!?')
            if 0<len(nombre)<=200 and normalizar(nombre) not in ('hola','gracias','ok','cancelar','olvidalo'):
                if not datos['nombre']:datos['nombre']=nombre
                elif not datos['cancion']:datos['cancion']=nombre
                else:datos=None
                if datos:return Orden('spotify_playlist_cancion',json.dumps(datos,ensure_ascii=False))
        from volumen_apps import interpretar_volumen
        volumen=interpretar_volumen(t,contexto=self.contexto()['tema_activo'])
        if volumen:return volumen
        if self.contexto()['tema_activo']=='youtube':
            from navegador import indice_resultado
            indice=indice_resultado(t,contexto=True)
            if indice:return Orden('youtube_resultado',indice)
            opciones={'siguiente':'siguiente','pon otra':'siguiente','pon otro':'siguiente','la siguiente':'siguiente',
                      'el siguiente':'siguiente','la anterior':'anterior','el anterior':'anterior',
                      'pausa':'pausa','pausalo':'pausa','detenlo':'pausa','continua':'reanudar','reanuda':'reanudar','ahora sigue':'reanudar'}
            if n in opciones:return Orden('youtube_'+opciones[n])
        if control_ampliado:
            apertura=re.fullmatch(ABRIR+r'\s+(?:el\s+|la\s+)?(.+?)[.!]?',t,re.I)
            if apertura and orden and orden.tipo=='desconocida':return Orden('programa_abrir',apertura[1])
            cierre=re.fullmatch(r'(?:cierra|cerrar|cierre|cierres|termina)\s+(?:el\s+|la\s+)?(?!ventana\b)(.+?)[.!]?',t,re.I)
            if cierre:return Orden('programa_cerrar',cierre[1])
        return orden

    def validar(self,datos,texto,contexto,control_ampliado=False):
        aclarar=Decision(pregunta='¿A qué te refieres? Dime qué quieres controlar o cambiar.')
        if not isinstance(datos,dict) or set(datos)!={'accion','valor'}:return aclarar
        accion=datos['accion'];valor=datos['valor']
        if not all(isinstance(v,str) for v in (accion,valor)):return aclarar
        if not protegida(texto):
            from core import interpretar
            directa=interpretar(texto)
            if directa and (directa.tipo in ('youtube_buscar','youtube_video','youtube_resultado','spotify_playlist_cancion','spotify_playlist_pendiente') or (not directa.tipo.endswith('_volumen') and re.search(r'\ben\s+spotify[.!?]*$',texto,re.I))):
                return Decision(self.ajustar_orden(texto,directa,control_ampliado))
        if accion=='charla':return Decision()
        from playlists import interpretar_cancion_playlist
        en_lista=interpretar_cancion_playlist(limpiar_peticion(texto)) if not protegida(texto) else None
        if en_lista:return Decision(Orden('spotify_playlist_cancion',json.dumps(en_lista,ensure_ascii=False)))
        from navegador import interpretar_web
        directa=interpretar_web(limpiar_peticion(texto)) if not protegida(texto) else None
        if directa and accion in ('abrir','buscar','programa_abrir'):return Decision(directa)
        if accion in ('spotify_volumen','youtube_volumen'):
            from volumen_apps import interpretar_volumen
            volumen=interpretar_volumen(texto,contexto=contexto['tema_activo'])
            return Decision(volumen) if volumen and volumen.tipo==accion and volumen.valor==valor and not protegida(texto) else aclarar
        if accion=='abrir' and valor:
            from core import SITIOS
            if normalizar(valor) in SITIOS and normalizar(valor) not in APPS and normalizar(valor) in normalizar(texto):
                accion='pestana'
        if control_ampliado:
            from control_pc import ACCIONES as PC,validar
            if accion=='programa_abrir' and re.match(r'^(?:busca|buscar|buscame|encuentra|investiga)\b',normalizar(limpiar_peticion(texto))):
                from core import interpretar
                web=interpretar(texto)
                return Decision(web) if web and web.tipo in ('buscar','pestana','youtube_buscar','spotify_buscar') else aclarar
            if accion=='abrir' and normalizar(valor) not in APPS and valor and normalizar(valor) in normalizar(texto):
                accion='archivo_abrir' if re.search(r'\b(?:archivo|imagen|foto|documento)\b',normalizar(texto)) or re.search(r'[\\/]|\.(?:png|jpg|jpeg|pdf|txt|docx|xlsx)$',valor,re.I) else 'programa_abrir'
            if accion in ('ventana_minimizar','ventana_maximizar','ventana_cerrar') and not valor:
                objetivo=re.search(r'\bventana\s+[«"\']?(.+?)[»"\']?[.?!]*$',texto,re.I)
                if objetivo:valor=objetivo[1].strip()
            if accion in PC:
                return Decision(Orden(accion,valor)) if not protegida(texto) and validar(accion,valor,texto) else aclarar
        if accion not in ACCIONES:return aclarar
        if protegida(texto):return Decision()
        if re.search(r'\b(?:y luego|despues de eso|primero.+luego)\b',normalizar(texto)):return aclarar
        valor=valor.strip()
        if len(valor)>500 or any(ord(c)<32 for c in valor):return aclarar
        n=normalizar(texto)
        if accion=='spotify_playlist_cancion':
            try:objetivo=json.loads(valor)
            except ValueError:return aclarar
            if not isinstance(objetivo,dict) or set(objetivo)!={'cancion','nombre'}:return aclarar
            if not all(isinstance(v,str) and v.strip() and len(v)<=200 and normalizar(v) in n for v in objetivo.values()):return aclarar
            lista=normalizar(objetivo['nombre'])
            if not re.search(r'\b(?:playlist|lista(?: de reproduccion)?)\s+[«"\'“]?'+re.escape(lista)+r'(?:[»"\'”]|\s|[.!?]|$)',n):return aclarar
            return Decision(Orden(accion,json.dumps(objetivo,ensure_ascii=False)))
        if accion.startswith('spotify'):
            if not re.search(r'\b(?:spotify|musica|cancion|canciones|tema|pista|playlist|lista|reproduccion|sonando|reproductor)\b',n) and contexto['tema_activo']!='spotify':return aclarar
        if accion.startswith('youtube_'):
            if 'youtube' not in n and 'video' not in n and contexto['tema_activo']!='youtube':return aclarar
            if accion in SIN_ARGUMENTO:return Decision(Orden(accion)) if not valor else aclarar
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
            from core import SITIOS
            destino=next((sitio for nombre,sitio in SITIOS.items() if normalizar(valor)==normalizar(sitio) and re.search(r'\b'+re.escape(nombre)+r'\b',n)),None)
            if destino:return Decision(Orden('pestana',destino))
            if not valor or normalizar(valor) not in n:return aclarar
            valor=url_solicitada(valor)
            if not valor:return aclarar
        elif not valor or (normalizar(valor) not in n and not reutiliza):return aclarar
        return Decision(Orden(accion,valor))

    def resolver(self,texto,modelo,cancelar=None,control_ampliado=False):
        if cancelar and cancelar.is_set():raise InterruptedError('Interpretación cancelada.')
        if protegida(texto):return Decision()
        contexto=self.contexto()
        if not modelo:return Decision(pregunta='Necesito la IA local activada para entender esa petición con contexto.')
        sistema=SISTEMA;esquema=ESQUEMA
        if control_ampliado:
            from control_pc import ACCIONES as PC,SISTEMA as INSTRUCCIONES
            sistema+='\n'+INSTRUCCIONES
            esquema={'oneOf':ESQUEMA['oneOf']+[esquema_accion(PC,{'type':'string','maxLength':500})]}
        mensajes=[{'role':'system','content':sistema+'\nTema activo actual: '+(contexto['tema_activo'] or 'ninguno')+'.'}]
        for turno in contexto['turnos']:
            mensajes.append({'role':'user','content':turno['peticion']})
            if turno.get('aclaracion'):
                contenido=turno['resultado']
            else:
                contenido=json.dumps({'accion_anterior':turno['accion'],'valor':turno['valor'],'resultado_real':turno['resultado']},ensure_ascii=False)
            mensajes.append({'role':'assistant','content':contenido})
        mensajes.append({'role':'user','content':texto})
        cuerpo={'model':modelo,'stream':False,'format':esquema,'keep_alive':'15m',
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
        return self.validar(datos,texto,contexto,control_ampliado)
