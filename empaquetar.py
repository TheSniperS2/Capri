from pathlib import Path
import base64,hashlib,io,zipfile

BASE=Path(__file__).resolve().parent
ARCHIVOS=['puente_opera.py','integraciones/opera-capri/manifest.json','integraciones/opera-capri/control.js','integraciones/opera-capri/page.js','integraciones/opera-capri/content.js','integraciones/opera-capri/worker.js','CONECTAR_OPERA.md','volumen_apps.py','aplicaciones.py','navegador.py','app.py','core.py','voz.py','recursos.py','activar_ia.py','reconocimiento.py','nombres.py','activacion.py','escritorio.py','multimedia.py','playlists.py','intenciones.py','prueba_microfono.py','dialogos.py','avatar.py','sincronia.py','entrada.py','fuentes.py','intro.py','companera.py','travesuras.py','ventanas.py','control_pc.py','assets/capri-personaje-v1.png','assets/capri-caminar-v1.png','assets/capri-base-v2.png','assets/capri-bocas-v2.png','assets/fonts/ChakraPetch-Regular.ttf','assets/fonts/ChakraPetch-Bold.ttf','assets/fonts/OFL.txt','capri.ico','preparar_whisper.py','requirements.txt','LEEME.md','ARTE_ANIMADO.md','COMPARACION_MODELOS.md','PERSONAJE_Y_CONTROL.md','PROMPT_CAMINAR.md']

ARCHIVOS.append('assets/capri-saludo-v1.png')
ARCHIVOS.append('PROMPT_SALUDO.md')
ARCHIVOS.append('menu_radial.py')
ARCHIVOS.append('ajustes_ui.py')
ARCHIVOS.append('idiomas.py')
ARCHIVOS.append('league.py')
ARCHIVOS.extend(['apagado.py','discord_control.py'])
ARCHIVOS.append('llamadas.py')
ARCHIVOS.append('audio_llamada.py')
ARCHIVOS.extend(['asomo.py','invitados.py','assets/capri-asomo-curioso-v1.png'])
ARCHIVOS.extend(['PROMPT_ASOMO.md','VOCES_INVITADAS.md'])
ARCHIVOS.extend(['assets/capri-despedida-sonrisa-v1.png','PROMPT_DESPEDIDA.md'])
ARCHIVOS.extend(['despedida_camara.py','assets/capri-asomo-tierno-v2.png','assets/capri-despedida-camara-v2.png','PROMPTS_CAPRI_V2.md'])
ARCHIVOS.extend(['assets/capri-despedida-camara-v3.png','PROMPT_DESPEDIDA_V3.md'])
ARCHIVOS.extend(['assets/capri-asomo-fiel-v3.png','assets/capri-despedida-expresiones-v4.png','PROMPTS_GESTOS_V4.md'])
ARCHIVOS.append('traducciones.json')
ARCHIVOS.append('REFERENCIAS_VOZ.md')
ARCHIVOS.extend(['despedida.py','assets/capri-base-hd-v1.png','PROMPT_HD.md'])

def origen(nombre):
    if nombre in ('PROMPT_SALUDO.md','PROMPT_HD.md','REFERENCIAS_VOZ.md','PROMPT_ASOMO.md','VOCES_INVITADAS.md','PROMPT_DESPEDIDA.md','PROMPTS_CAPRI_V2.md','PROMPT_DESPEDIDA_V3.md','PROMPTS_GESTOS_V4.md'):return BASE/'docs'/nombre
    if nombre.startswith(('assets/','integraciones/')):return BASE/nombre
    if nombre=='capri.ico':return BASE/'assets'/nombre
    if nombre=='LEEME.md':return BASE/'docs/USO.md'
    if nombre in ('ARTE_ANIMADO.md','COMPARACION_MODELOS.md','PERSONAJE_Y_CONTROL.md','PROMPT_CAMINAR.md','CONECTAR_OPERA.md'):return BASE/'docs'/nombre
    if nombre=='requirements.txt':return BASE/nombre
    return BASE/'src'/nombre

def crear():
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for nombre in ARCHIVOS:z.write(origen(nombre),nombre)
    datos=buffer.getvalue()
    plantilla=(BASE/'installer/plantilla.py').read_text(encoding='utf8')
    programa=plantilla.replace('__CAPRI_PAYLOAD__',base64.b64encode(datos).decode()).replace('__CAPRI_HASH__',hashlib.sha256(datos).hexdigest())
    salida=BASE/'dist';salida.mkdir(exist_ok=True)
    destino=salida/'Abrir Capri.pyw'
    destino.write_text(programa,encoding='utf8')
    with zipfile.ZipFile(salida/'Capri.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.write(destino,destino.name)
        z.write(BASE/'docs/USO.md','LEEME.md')
        z.write(BASE/'docs/PERSONAJE_Y_CONTROL.md','PERSONAJE_Y_CONTROL.md')
        z.write(BASE/'docs/PROMPT_CAMINAR.md','PROMPT_CAMINAR.md')
        z.write(BASE/'docs/CONECTAR_OPERA.md','CONECTAR_OPERA.md')
        for nombre in ARCHIVOS:z.write(origen(nombre),'codigo/'+nombre)
    print('Lanzador:',destino)
    print('ZIP:',salida/'Capri.zip')
    print('SHA256 del paquete:',hashlib.sha256(datos).hexdigest())

if __name__=='__main__':crear()
