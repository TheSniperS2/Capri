from pathlib import Path
import base64,hashlib,io,zipfile

BASE=Path(__file__).resolve().parent
ARCHIVOS=['app.py','core.py','voz.py','recursos.py','activar_ia.py','reconocimiento.py','nombres.py','activacion.py','escritorio.py','multimedia.py','playlists.py','intenciones.py','prueba_microfono.py','dialogos.py','avatar.py','sincronia.py','entrada.py','fuentes.py','intro.py','assets/capri-base-v2.png','assets/capri-bocas-v2.png','assets/fonts/ChakraPetch-Regular.ttf','assets/fonts/ChakraPetch-Bold.ttf','assets/fonts/OFL.txt','capri.ico','preparar_whisper.py','requirements.txt','LEEME.md','ARTE_ANIMADO.md','COMPARACION_MODELOS.md']

def origen(nombre):
    if nombre.startswith('assets/'):return BASE/nombre
    if nombre=='capri.ico':return BASE/'assets'/nombre
    if nombre=='LEEME.md':return BASE/'docs/USO.md'
    if nombre in ('ARTE_ANIMADO.md','COMPARACION_MODELOS.md'):return BASE/'docs'/nombre
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
        for nombre in ARCHIVOS:z.write(origen(nombre),'codigo/'+nombre)
    print('Lanzador:',destino)
    print('ZIP:',salida/'Capri.zip')
    print('SHA256 del paquete:',hashlib.sha256(datos).hexdigest())

if __name__=='__main__':crear()
