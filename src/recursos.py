"""Descargas acotadas y extracción dentro de la carpeta de Capri."""
from pathlib import Path, PurePosixPath
import os
import time
import urllib.request
import zipfile

ARTE = [
    ('capri-1.png', 'https://mudae.net/uploads/3127100/yHv4qwZ~LBAH9KIJh.png'),
    ('capri-2.png', 'https://mudae.net/uploads/3127100/etkfvCP~bf712a2ea2bf.png'),
    ('capri-3.png', 'https://mudae.net/uploads/3127100/OwjeVmT~59966d2d98c2.png'),
]
MODELO_URL = 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip'
MODELO_NOMBRE = 'vosk-model-small-es-0.42'

def descargar(url, destino, progreso=lambda n,t:None, cancelar=None, maximo=200_000_000, plazo=300):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix+'.part')
    inicio = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent':'Capri/0.1'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp, parcial.open('wb') as out:
            total = int(resp.headers.get('Content-Length', 0))
            if total > maximo: raise ValueError('El archivo supera el tamaño permitido.')
            actual=0
            while True:
                if cancelar and cancelar.is_set(): raise InterruptedError('Descarga cancelada.')
                if time.monotonic()-inicio > plazo: raise TimeoutError('La descarga está tardando demasiado. Puedes reintentar.')
                bloque = resp.read(64*1024)
                if not bloque:break
                actual += len(bloque)
                if actual > maximo: raise ValueError('El archivo supera el tamaño permitido.')
                out.write(bloque); progreso(actual,total)
            if total and actual != total:raise OSError('La descarga quedó incompleta.')
            if not actual:raise OSError('El servidor devolvió un archivo vacío.')
        parcial.replace(destino)
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise

def extraer_seguro(archivo, carpeta, maximo=600_000_000):
    carpeta=Path(carpeta).resolve()
    with zipfile.ZipFile(archivo) as z:
        if sum(i.file_size for i in z.infolist()) > maximo:raise ValueError('El archivo descomprimido es demasiado grande.')
        for i in z.infolist():
            ruta=PurePosixPath(i.filename.replace('\\','/'))
            if ruta.is_absolute() or '..' in ruta.parts or ':' in i.filename or (i.external_attr >>16)&0o170000 == 0o120000:
                raise ValueError('Ruta de extracción no admitida.')
            destino=(carpeta/Path(*ruta.parts)).resolve()
            if not destino.is_relative_to(carpeta):raise ValueError('Ruta fuera de la carpeta del programa.')
        z.extractall(carpeta)
