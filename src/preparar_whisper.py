"""Prepara un modelo Whisper multilingüe local, sin descargar código de terceros."""
from pathlib import Path
from recursos import descargar
from reconocimiento import ARCHIVOS

def preparar(carpeta,estado=lambda t:None,progreso=lambda n,t:None,cancelar=None):
    carpeta=Path(carpeta)/'whisper-base'
    carpeta.mkdir(parents=True,exist_ok=True)
    for i,nombre in enumerate(ARCHIVOS):
        ruta=carpeta/nombre
        if ruta.is_file() and ruta.stat().st_size>100:continue
        estado(f'Whisper español · {i+1}/{len(ARCHIVOS)} · {nombre}')
        descargar('https://huggingface.co/Systran/faster-whisper-base/resolve/main/'+nombre,
                  ruta,progreso,cancelar,maximo=190_000_000,plazo=900)
    return carpeta

if __name__=='__main__':
    import sys
    preparar(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'modelos',estado=print)
