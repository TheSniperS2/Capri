"""Órdenes de Capri. El texto nunca se ejecuta como código ni como comando de consola."""
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, urlsplit
import json
import os
import re
import subprocess
import unicodedata
import urllib.request
import time
from nombres import nombre_aplicacion

PERSONALIDAD = '''Eres Capri, compañera digital de escritorio de quien utiliza la aplicación, inspirada en Cyberpunk: Edgerunners.
Tu nombre es Capri. El usuario es otra persona: usa su nombre si lo dijo en el historial; si no lo dijo, reconoce que aún no lo sabes.
Hablas en primera persona femenina y español latino. Eres curiosa, pícara y juguetona, sin insultar ni burlarte de los problemas del usuario.
Responde directamente a lo que pide, normalmente en una o dos frases y hasta 55 palabras. Si pide una historia, cuéntala con final; no te limites a ofrecer contarla. Evita saludos repetidos y frases de asistente corporativa.
Puedes inventar ficción cuando la piden, pero no presentes ficción como recuerdos reales de conversaciones o acciones. Si no sabes un dato, dilo; no inventes artistas, canciones ni información de la serie.
Capri tiene un ejecutor que abre aplicaciones y carpetas, busca y controla Spotify. Este canal conversa: solo afirma acciones hechas cuando hay un resultado real del ejecutor. Sin ese resultado no sabes qué suena ni qué hay en pantalla.
Una pregunta sobre posibles fallos no prueba una avería. No inventes causas del micrófono ni motivos para no detectar el nombre. Si una orden es ambigua, pide una aclaración breve.'''

def mantener_identidad(texto):
    # Defensa adicional ante las presentaciones inventadas por modelos pequeños.
    texto = re.sub(r'(?i)(?<!no )(?<!nunca )(?<!jamás )\b(me llamo|mi nombre es|puedes llamarme)\s+(?!Capri\b)[\wÁÉÍÓÚÑáéíóúñ-]+',
                   lambda m:m[1]+' Capri',texto)
    return re.sub(r'(?i)(?<!no )\bsoy\s+(?:Luna|Alexa|Siri|ChatGPT|Llama)\b','soy Capri',texto)

def respuesta_conversacion(texto):
    texto=mantener_identidad(texto)
    frases=re.split(r'(?<=[.!?])\s+',texto)
    afirmacion=r'\b(?:sigue|contin[uú]a|est[aá])\s+(?:reproduci[eé]ndose|sonando)|\bse\s+(?:sigue\s+|est[aá]\s+)?reproduciendo\b|\b(?:ahora|actualmente)\s+(?:suena|reproduce)|\b(?:est[aá]s|estoy|estamos)\s+escuchando\b|\b(?:tengo|hay|tenemos)\s+(?:ya\s+)?(?:una\s+|la\s+)?reproducci[oó]n\s+en\s+marcha|\b(?:he\s+)?(?:reanud[eé]|inici[eé]|activ[eé])\s+(?:la\s+)?reproducci[oó]n'
    frases=[f for f in frases if not re.search(afirmacion,f,re.I)]
    texto=' '.join(frases).strip() or 'Podemos seguir conversando. No he consultado qué está sonando en Spotify.'
    # El modelo de charla no conoce el resultado de acciones. Corregir negativas
    # globales falsas sin afirmar que se ejecutó nada ni ocultar errores del ejecutor.
    negativa=r'\bno\s+(?:puedo|puede)\s+(?:abrir\s+(?:spotify|opera(?: gx)?|(?:ninguna|otras?|las)\s+aplicaci[oó]n(?:es)?)|(?:interactuar|interaccionar)\s+con\s+(?:(?:tu|su|el)\s+)?(?:computador|ordenador|entorno digital))'
    if re.search(negativa,texto,re.I) or re.search(r'\bmi funci[oó]n es\s+(?:solo\s+)?conversar.{0,60}\bno\s+interactuar',texto,re.I):
        return 'Sí puedo abrir Spotify, Opera GX y las aplicaciones disponibles. Esta vez no interpreté una orden de apertura; dime qué quieres abrir.'
    return texto

HIDDEN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

@dataclass(frozen=True)
class Orden:
    tipo: str
    valor: str = ''

APPS = {
    'opera': 'opera', 'opera gx': 'opera', 'navegador': 'opera',
    'calculadora': 'calc.exe', 'bloc de notas': 'notepad.exe',
    'explorador': 'explorer.exe', 'explorador de archivos': 'explorer.exe',
    'spotify': 'spotify', 'youtube': 'https://www.youtube.com/',
}

ABRIR = r'(?:[áa]bre(?:me)?|abrir(?:me)?|abras|abres|abrieras|abriera|abririas|inicia(?:r)?|lanza(?:r)?)'
BUSCAR = r'(?:b[uú]sca(?:r(?:me)?|me)?|b[uú]sque(?:s|n)?|investiga(?:r|me)?|encuentra(?:me)?|encontrar|mu[eé]strame)'
PESTANA = r'(?:una |otra |nueva |una nueva |otra nueva )?pestana(?: nueva)?(?:\s+(?:en|de|del|con)\s+(?:el\s+)?(?:opera(?: gx)?|navegador))?'
SITIOS = {'google':'https://www.google.com/', 'youtube':'https://www.youtube.com/',
          'netflix':'https://www.netflix.com/', 'twitch':'https://www.twitch.tv/',
          'crunchyroll':'https://www.crunchyroll.com/', 'disney plus':'https://www.disneyplus.com/',
          'prime video':'https://www.primevideo.com/', 'github':'https://github.com/',
          'reddit':'https://www.reddit.com/', 'steam':'https://store.steampowered.com/',
          'wikipedia':'https://es.wikipedia.org/', 'spotify':'https://open.spotify.com/'}

def error_de_una_letra(a,b):
    """Una sustitución, inserción, omisión o transposición; sin corregir consultas."""
    if a==b:return True
    if abs(len(a)-len(b))>1:return False
    if len(a)==len(b):
        distintos=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
        if len(distintos)==1:return True
        return len(distintos)==2 and distintos[1]==distintos[0]+1 and a[distintos[0]]==b[distintos[1]] and a[distintos[1]]==b[distintos[0]]
    corto,largo=(a,b) if len(a)<len(b) else (b,a)
    return any(largo[:i]+largo[i+1:]==corto for i in range(len(largo)))

def corregir_verbo_apertura(texto):
    partes=texto.split(maxsplit=1)
    if len(partes)!=2 or re.fullmatch(ABRIR,partes[0],re.I):return texto
    verbo=normalizar(partes[0])
    candidatos=[v for v in ('abrir','abre','abreme','abrirme','abras','abres','abrieras') if error_de_una_letra(verbo,v)]
    if not candidatos:return texto
    # Solo corregir aperturas de destinos conocidos, nunca texto dentro de una
    # búsqueda, una cita, una negación o un argumento de otra acción.
    destino=re.sub(r'^(?:el|la)\s+','',partes[1],flags=re.I).strip(' .!?')
    app=nombre_aplicacion(nombre_navegador(destino))
    if app in APPS or app in SITIOS or re.fullmatch(PESTANA,app):
        return candidatos[0]+' '+partes[1]
    return texto

def limpiar_peticion(texto):
    texto=texto.strip().strip('¿?¡!').strip()
    texto=re.sub(r'^(?:oye\s+)?capri[, :]*','',texto,flags=re.I).strip()
    prefijo=r'^(?:(?:por favor)[, ]+|(?:me\s+)?(?:puedes|podr[ií]as?|puedas)\s+|(?:quiero|quer[ií]a|quisiera|necesito|me gustar[ií]a|te pido|te ped[ií])\s+(?:que\s+)?|(?:que\s+)(?=bus|bús|abre|abras|repro|ponga)|(?:me\s+)(?=abre|abras|abres|bus|bús))'
    for _ in range(5):
        partes=texto.split(maxsplit=1)
        if len(partes)==2 and len(partes[0])>=5:
            modal=normalizar(partes[0])
            # No sustituir palabras dentro de una frase: solo el modal inicial.
            if modal not in ('puedes','podrias','podria','puedas') and any(error_de_una_letra(modal,v) for v in ('puedes','podrias','podria')):
                texto='podrías '+partes[1]
        nuevo=re.sub(prefijo,'',texto,flags=re.I).strip().strip('¿?¡!').strip()
        if nuevo==texto:break
        texto=nuevo
    texto=re.sub(r'^(?:haz|hacer|realiza|realizar)\s+una\s+b[uú]squeda\s+(?:de|sobre)\s+','busca ',texto,flags=re.I)
    texto=re.sub(r'[, ]+por favor[.!]?$','',texto,flags=re.I).strip().strip('¿?¡!').strip()
    return corregir_verbo_apertura(texto)

def nombre_navegador(texto):
    return re.sub(r'\bopera\s+(?:ge\s+equis|g\s+x|equis|ex|x)\b','opera gx',normalizar(texto))

def url_solicitada(texto):
    texto=texto.strip().strip(' .!')
    n=normalizar(texto)
    n={'crunchy roll':'crunchyroll','crunchy':'crunchyroll','disney+':'disney plus','disneyplus':'disney plus',
       'primevideo':'prime video','amazon prime video':'prime video'}.get(n,n)
    if n in SITIOS:return SITIOS[n]
    candidato=texto if re.match(r'^https?://',texto,re.I) else ('https://'+texto if re.fullmatch(r'(?:www\.)?[\w-]+(?:\.[\w-]+)+(?:/\S*)?',texto) else '')
    if not candidato:return None
    try:
        partes=urlsplit(candidato)
        if partes.scheme in ('http','https') and partes.hostname and not partes.username and not partes.password and not any(c.isspace() for c in candidato):
            return candidato
    except ValueError:pass
    return None

def interpretar(texto):
    texto = limpiar_peticion(texto)
    n=nombre_navegador(texto).strip(' .!')
    from volumen_apps import interpretar_volumen
    volumen=interpretar_volumen(texto)
    if volumen:return volumen
    # Sitios y vídeos se resuelven antes de música o búsqueda general.
    from navegador import interpretar_web
    web=interpretar_web(texto)
    if web:return web
    # Errores reales de dictado: solo una orden completa de transporte, nunca
    # búsquedas, títulos, citas, explicaciones ni negaciones.
    transporte_erroneo=re.fullmatch(r'(revoluces|revoluce|reproduses|reproduse)\s+(?:(?:la|mi|esa)\s+)?(?:cancion|musica|reproduccion)(?:\s+en\s+spotify)?',n)
    if transporte_erroneo:return Orden('spotify','')
    if re.fullmatch(r'(?:ciente|siguente)\s+(?:cancion|pista|tema)(?:\s+en\s+spotify)?',n):
        return Orden('spotify_siguiente')
    if re.fullmatch(PESTANA,n):return Orden('pestana')
    if n in ('habla mas rapido','hablame mas rapido','lee mas rapido','leer mas rapido','hablar mas rapido','aumenta la velocidad de voz'):
        return Orden('velocidad_voz','subir')
    if n in ('habla mas lento','hablame mas lento','lee mas lento','leer mas lento','hablar mas lento','baja la velocidad de voz'):
        return Orden('velocidad_voz','bajar')
    if n in ('habla a velocidad normal','velocidad de voz normal'):
        return Orden('velocidad_voz','normal')
    # Transporte de la cola actual ANTES de interpretar títulos o búsquedas.
    transporte=re.sub(r'\s+en\s+spotify$','',n)
    if re.fullmatch(r'(?:reproduce|reproducir|pon(?:er|me|ga|gas)?|reanuda(?:r)?|contin[uú]a|sigue)\s+(?:(?:la|mi|esa)\s+)?(?:musica|reproduccion|cancion|spotify)',transporte) or transporte in ('reanuda','reproduce','pon musica','dale play','continua la reproduccion','reproduce una cancion'):
        return Orden('spotify','')
    siguiente=r'(?:(?:la|el|a|a la|a el)\s+)*(?:siguiente|proxima)(?:\s+(?:cancion|musica|pista|tema))?(?:\s+de\s+(?:la\s+)?(?:playlist|lista)(?: de reproduccion)?)?'
    anterior=r'(?:(?:la|el|a|a la|a el)\s+)*(?:anterior)(?:\s+(?:cancion|musica|pista|tema))?(?:\s+de\s+(?:la\s+)?(?:playlist|lista)(?: de reproduccion)?)?'
    orden_paso=r'(?:(?:pon(?:er|me|ga|gas)?|reproduce|pasa(?:r)?|salta(?:r)?|cambia(?:r)?|avanza(?:r)?|ve)\s+)?'
    paso_invertido=re.fullmatch(r'(?:pon(?:er|me|ga|gas)?|reproduce|reproducir)\s+(?:(?:la|el)\s+)?(?:musica|cancion|tema|pista)\s+(siguiente|anterior)',transporte)
    if paso_invertido:return Orden('spotify_'+paso_invertido[1])
    if re.fullmatch(orden_paso+siguiente,transporte) or transporte in ('salta la cancion','saltar la cancion','salta esta cancion','siguiente cancion','pon la musica siguiente','poner la musica siguiente','cambia de cancion','otra cancion'):
        return Orden('spotify_siguiente')
    if re.fullmatch(orden_paso+anterior,transporte) or transporte in ('vuelve a la cancion anterior','pon la musica anterior'):
        return Orden('spotify_anterior')
    if transporte in ('que esta sonando','que cancion esta sonando','que cancion suena','que se esta reproduciendo','que suena en spotify'):
        return Orden('spotify_estado')
    playlist=re.match(r'^(?:reproduce|reproducir|pon(?:me|ga|gas)?|abre|abrir|escuchar)\s+(?:(?:la|mi)\s+)?(?:playlist|lista(?: de reproducci[oó]n)?)\s+(?:(?:privada|llamada)\s+)?(.+?)(?:\s+en\s+Spotify)?[.!]?$',texto,re.I)
    if playlist:return Orden('spotify_playlist',playlist[1].strip(' «»".'))
    # La búsqueda se evalúa antes que «abre», para ejecutar una sola acción compuesta.
    musica=re.match(r'^(?:reproduce|reproducir|reproduzcas|pon(?:me|ga|gas)?|toca|escuchar)\s+(.+)$',texto,re.I)
    if musica:
        cancion=re.sub(r'\s+en\s+(?:el\s+)?(?:spotify|spotifai|espotifai)[.!]?$', '',musica[1],flags=re.I).strip(' .!')
        cancion=re.sub(r'^(?:la\s+)?(?:canci[oó]n|tema)\s+','',cancion,flags=re.I)
        cancion=re.sub(r'^m[uú]sica\s+de\s+','',cancion,flags=re.I)
        if normalizar(cancion) in ('spotify','musica','la musica','una cancion','algo de musica'):
            return Orden('spotify','')
        from playlists import cargar,clave
        if clave(cancion) in cargar():return Orden('spotify_playlist',cancion)
        return Orden('spotify',cancion[:500])
    if n in ('pausa spotify','pausa la musica','pausa la cancion','pausar spotify','pausa la reproduccion','pausa') or re.fullmatch(r'(?:deten|detener|para|parar|frena|interrumpe)\s+(?:(?:la|mi|esa)\s+)?(?:cancion|musica|reproduccion|spotify)',n):
        return Orden('spotify_pausa')
    combinado=re.match(r'^'+ABRIR+r'\s+(.+?)\s+(?:y|para)\s+('+BUSCAR+r'\s+.+)$',texto,re.I)
    texto_busqueda=texto
    if combinado and re.search(r'\b(?:opera|navegador|pestana)\b',normalizar(combinado[1])):
        texto_busqueda=combinado[2]
    busqueda = re.match(r'^'+BUSCAR+r'\s+(?:(?:en\s+)?(?:google|[óo]pera(?:\s+gx)?|internet)\s+)?(?:sobre\s+)?(.+)', texto_busqueda, re.I)
    if busqueda:
        consulta = re.sub(r'\s+en\s+(?:google|[óo]pera(?:\s+gx)?|internet)[.!]?$', '', busqueda[1], flags=re.I).strip()
        if consulta:
            spotify=re.match(r'^(.+?)\s+en\s+(?:spotify|spotifai|espotifai)[.!]?$',consulta,re.I)
            if spotify:return Orden('spotify_buscar',spotify[1].strip())
            return Orden('buscar', consulta[:2000])
    apertura = re.match(r'^'+ABRIR+r'\s+(?:el\s+|la\s+)?(.+?)[.!]?$', texto, re.I)
    if apertura:
        app = nombre_aplicacion(nombre_navegador(apertura[1].strip()))
        app = re.sub(r'\s+(?:y|e)\s+(?:nada mas|eso es todo)$', '', app)
        if app in ('archivos','mis archivos','el explorador de archivos de windows','explorador de windows'):
            app='explorador de archivos'
        carpetas={'descargas':'Downloads','mis descargas':'Downloads','documentos':'Documents','mis documentos':'Documents',
                  'escritorio':'Desktop','imagenes':'Pictures','mis imagenes':'Pictures','musica':'Music','videos':'Videos'}
        carpeta=re.sub(r'^(?:la )?carpeta (?:de )?','',app)
        if carpeta in carpetas:return Orden('carpeta',carpetas[carpeta])
        if 'pestana' in app and re.search(r'\b(?:pestana|opera|navegador)\b',app):
            if re.fullmatch(PESTANA,app):
                return Orden('pestana')
            destino=re.match(r'^(?:una |otra |nueva |una nueva )?pesta[ñn]a(?: nueva)?\s+(?:en|de|con)\s+(.+)$',apertura[1],re.I)
            if destino:
                sitio=url_solicitada(destino[1])
                if sitio:return Orden('pestana',sitio)
            return Orden('no_admitida',texto)
        if app in APPS:
            return Orden('abrir', app)
        sitio=url_solicitada(apertura[1])
        if sitio:return Orden('pestana',sitio)
        return Orden('desconocida', apertura[1])
    n = normalizar(texto).strip(' .!')
    if n in ('que puedes hacer', 'ayuda', 'comandos', 'que sabes hacer'):
        return Orden('ayuda')
    if n in ('que hora es', 'dime la hora', 'la hora'):
        return Orden('hora')
    if n in ('silencio', 'callate', 'deja de hablar', 'no hables'):
        return Orden('silencio')
    if n in ('hola', 'buenas', 'hola capri'):
        return Orden('saludo')
    if n in ('como te llamas','cual es tu nombre','quien eres'):
        return Orden('identidad')
    if n in ('puedo hablar contigo','podemos hablar','puedo conversar contigo','podemos conversar','podria hablar contigo'):
        return Orden('charla')
    if re.match(r'^(?:'+ABRIR+r'|'+BUSCAR+r'|cierra|cerrar|minimiza|maximiza|haz clic|haz click|pulsa|presiona|escribe|mueve|cambia|sube|baja|silencia|reproduce|pausa|borra|elimina|envia|compra|instala|ejecuta|ejecutar|entra|entrar|navega|ve a)\b',n):
        return Orden('no_admitida',texto)
    return None

def localizar_opera():
    local = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    candidatos = [local/'Programs/Opera GX/opera.exe', local/'Programs/Opera/opera.exe']
    for var in ('PROGRAMFILES', 'PROGRAMFILES(X86)'):
        if os.environ.get(var):
            candidatos.extend(Path(os.environ[var])/p for p in ('Opera GX/opera.exe', 'Opera/opera.exe'))
    if os.name == 'nt':
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r'Software\Microsoft\Windows\CurrentVersion\App Paths\opera.exe') as key:
                    candidatos.append(Path(winreg.QueryValue(key, None).strip('"')))
            except OSError:
                pass
    return next((p for p in candidatos if p.is_file()), None)

def abrir_opera(consulta=None, spawn=subprocess.Popen, pagina=None):
    opera = localizar_opera()
    if opera is None:
        raise FileNotFoundError('No encontré Opera GX ni Opera instalado en sus ubicaciones habituales.')
    argumentos = [str(opera)]
    if consulta:
        argumentos.append('https://www.google.com/search?' + urlencode({'q': consulta}))
    elif pagina:
        argumentos.append(pagina)
    spawn(argumentos, shell=False, creationflags=HIDDEN)

def ejecutar(orden, spawn=subprocess.Popen, open_url=None):
    if orden.tipo in ('spotify_volumen','youtube_volumen'):
        from volumen_apps import controlar_volumen
        return controlar_volumen(orden.valor,destino=orden.tipo.removesuffix('_volumen'))
    if orden.tipo.startswith('youtube_'):
        from navegador import ejecutar_youtube
        return ejecutar_youtube(orden,spawn=spawn)
    if orden.tipo in ('spotify_siguiente','spotify_anterior','spotify_estado'):
        from multimedia import controlar_sesion
        return controlar_sesion(orden.tipo.removeprefix('spotify_'))
    if orden.tipo=='spotify_playlist':
        from playlists import reproducir_playlist
        return reproducir_playlist(orden.valor)
    if orden.tipo in ('spotify','spotify_buscar','spotify_pausa'):
        from escritorio import controlar_spotify
        return controlar_spotify(orden.valor,accion={'spotify':'reproducir','spotify_buscar':'buscar','spotify_pausa':'pausa'}[orden.tipo])
    if orden.tipo=='carpeta':
        from escritorio import carpeta_usuario
        ruta=carpeta_usuario(orden.valor)
        spawn(['explorer.exe',str(ruta)],shell=False,creationflags=HIDDEN)
        return 'Abrí la carpeta '+ruta.name+'.'
    if orden.tipo == 'pestana':
        if orden.valor and not url_solicitada(orden.valor):raise ValueError('La dirección solicitada no es una página web válida.')
        abrir_opera(spawn=spawn,pagina=orden.valor or 'about:blank')
        return 'Listo, pedí a Opera GX abrir una pestaña'+(' con esa página.' if orden.valor else ' nueva.')
    if orden.tipo == 'buscar':
        abrir_opera(orden.valor, spawn=spawn)
        return 'Busqué «' + orden.valor + '» en Opera GX.'
    if orden.tipo == 'abrir':
        destino = APPS[orden.valor]
        if destino == 'opera':
            abrir_opera(spawn=spawn)
        elif destino.startswith('https://'):
            if open_url:
                open_url(destino)
            else:
                abrir_opera(spawn=spawn,pagina=destino)
        elif destino == 'spotify':
            if not hasattr(os, 'startfile'):
                raise OSError('Esta acción requiere Windows.')
            os.startfile('spotify:')
        else:
            spawn([destino], shell=False, creationflags=HIDDEN)
        return 'Abrí ' + orden.valor + '.'
    if orden.tipo == 'hora':
        from datetime import datetime
        return 'Son las ' + datetime.now().strftime('%H:%M') + '.'
    if orden.tipo == 'ayuda':
        return 'Dime «abre una pestaña en Opera GX», «busca gatos en Opera», «abre la calculadora» o «habla más rápido». También podemos conversar.'
    if orden.tipo == 'saludo':
        return 'Ey. Capri en línea. ¿Qué hacemos hoy?'
    if orden.tipo == 'identidad':
        return 'Soy Capri, tu compañera digital. ¿Qué tienes en mente?'
    if orden.tipo == 'charla':
        return 'Claro que podemos hablar. A ver con qué me sorprendes hoy.'
    if orden.tipo == 'desconocida':
        return 'Todavía no tengo registrada esa aplicación. Puedo abrir Opera GX, calculadora, bloc de notas, explorador, Spotify y YouTube.'
    if orden.tipo == 'no_admitida':
        return 'Ese control todavía no está implementado. Puedo abrir pestañas en Opera GX, buscar en internet y abrir las aplicaciones disponibles.'
    raise ValueError('Orden no admitida')

class IA:
    """Conversación local. Sus respuestas son texto, nunca instrucciones ejecutables."""
    def __init__(self):
        self.historia = []
        self.contexto_acciones = []
        self.ultima_medicion = {}

    def preparar(self, modelo):
        if not modelo:return
        datos={'model':modelo,'prompt':'','stream':False,'keep_alive':'15m','options':{'num_ctx':2048}}
        if modelo.lower().startswith('qwen3'):datos['think']=False
        cuerpo=json.dumps(datos).encode('utf8')
        req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=cuerpo,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as r:json.load(r)

    def modelos(self):
        with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as r:
            datos = json.load(r)
        return [m['name'] for m in datos.get('models', []) if isinstance(m.get('name'), str)
                and not m.get('remote_host') and not m.get('remote_model') and 'cloud' not in m['name'].lower()]

    def conversar(self, texto, modelo=None, al_texto=None, cancelar=None,origen='texto'):
        if not modelo:
            modelos = self.modelos()
            if not modelos:
                raise RuntimeError('Ollama está instalado, pero falta descargar un modelo. Pulsa Activar IA local en Ajustes.')
            modelo = next((m for m in modelos if 'llama3.2' in m), modelos[0])
        sistema=PERSONALIDAD
        sistema+='\nControl ampliado '+('activado: el ejecutor también administra archivos y ventanas; cualquier acción necesita un resultado real del ejecutor.' if getattr(self,'control_ampliado',False) else 'desactivado: no puedes leer, modificar ni borrar archivos o cerrar ventanas. Puedes explicar cómo activar esa opción en Ajustes.')
        if origen=='voz':
            sistema+='\nLa frase actual YA fue transcrita desde el micrófono: en este turno sí llegó audio. Eso no demuestra que todos los turnos anteriores funcionaran.'
        mensajes = [{'role': 'system', 'content': sistema}]
        if self.contexto_acciones:
            mensajes.append({'role':'system','content':'Resultados recientes del ejecutor, como datos históricos; no garantizan el estado actual. Puedes explicarlos sin inventar acciones nuevas: '+json.dumps(self.contexto_acciones,ensure_ascii=False)})
        # No volver a alimentar al modelo con sus afirmaciones musicales inventadas.
        mensajes += [dict(m,content=respuesta_conversacion(m['content'])) if m['role']=='assistant' else m for m in self.historia[-8:]] + [{'role': 'user', 'content': texto}]
        cuerpo={'model': modelo, 'messages': mensajes, 'stream': bool(al_texto),'keep_alive':'15m',
                'options': {'num_predict': 100,'num_ctx':2048,'temperature':.45,'repeat_penalty':1.1}}
        if modelo.lower().startswith('qwen3'):cuerpo['think']=False
        cuerpo=json.dumps(cuerpo).encode('utf8')
        req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=cuerpo, headers={'Content-Type': 'application/json'})
        inicio=time.monotonic();primero=None;respuesta=''
        with urllib.request.urlopen(req, timeout=45) as r:
            if al_texto:
                datos={}
                for linea in r:
                    if cancelar and cancelar.is_set():raise InterruptedError('Respuesta cancelada.')
                    if not linea.strip():continue
                    datos=json.loads(linea)
                    if datos.get('error'):raise RuntimeError(datos['error'])
                    fragmento=datos.get('message',{}).get('content','')
                    if fragmento:
                        if primero is None:primero=time.monotonic()-inicio
                        respuesta+=fragmento
                        al_texto(respuesta_conversacion(respuesta))
                    if datos.get('done'):break
            else:
                datos = json.load(r)
                respuesta = datos.get('message', {}).get('content', '')
        if cancelar and cancelar.is_set():raise InterruptedError('Respuesta cancelada.')
        respuesta = respuesta_conversacion(respuesta.strip())
        if not respuesta:
            raise RuntimeError('El modelo no devolvió una respuesta.')
        self.historia += [{'role': 'user', 'content': texto}, {'role': 'assistant', 'content': respuesta}]
        self.ultima_medicion={'total_s':round(time.monotonic()-inicio,3),'primer_texto_s':round(primero,3) if primero is not None else None,
                              'tokens':datos.get('eval_count'),'carga_s':round(datos.get('load_duration',0)/1e9,3)}
        return respuesta
