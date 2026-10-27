"""Prepara un modelo Whisper multilingüe local, sin descargar código de terceros."""
from pathlib import Path
from recursos import descargar
from reconocimiento import ARCHIVOS

def preparar(carpeta,estado=lambda t:None,progreso=lambda n,t:None,cancelar=None,modelo='base'):
    if modelo not in ('base','small'):raise ValueError('Modelo de reconocimiento no admitido.')
    carpeta=Path(carpeta)/('whisper-'+modelo)
    carpeta.mkdir(parents=True,exist_ok=True)
    for i,nombre in enumerate(ARCHIVOS):
        ruta=carpeta/nombre
        if ruta.is_file() and ruta.stat().st_size>100:continue
        estado(f'Whisper {modelo} · {i+1}/{len(ARCHIVOS)} · {nombre}')
        descargar('https://huggingface.co/Systran/faster-whisper-'+modelo+'/resolve/main/'+nombre,
                  ruta,progreso,cancelar,maximo=550_000_000 if modelo=='small' else 190_000_000,plazo=900)
    return carpeta

if __name__=='__main__':
    import sys
    preparar(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'modelos',estado=print,modelo=sys.argv[2] if len(sys.argv)>2 else 'base')
