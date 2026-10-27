"""Tipografía privada de Capri: no instala fuentes para otros programas."""
import os
from pathlib import Path

FAMILIA='Chakra Petch'
_cargadas=set()

def cargar(base):
    carpetas=[Path(base)/'assets/fonts',Path(__file__).resolve().parent.parent/'assets/fonts']
    if os.name!='nt':return
    import ctypes
    for nombre in ('ChakraPetch-Regular.ttf','ChakraPetch-Bold.ttf'):
        ruta=next((p/nombre for p in carpetas if (p/nombre).is_file()),None)
        if ruta is None or str(ruta) in _cargadas:continue
        if ctypes.windll.gdi32.AddFontResourceExW(str(ruta),0x10,None):_cargadas.add(str(ruta))
