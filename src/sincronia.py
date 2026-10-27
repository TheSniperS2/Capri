"""Posición del texto según el reloj de reproducción y marcas de voz."""
import html
import re

def alinear_marcas(texto,eventos):
    marcas=[];cursor=0
    for evento in eventos:
        palabra=html.unescape(evento.get('text',''))
        if not palabra:continue
        m=re.search(re.escape(palabra),texto[cursor:],flags=re.IGNORECASE)
        if not m:continue
        inicio=cursor+m.start();fin=cursor+m.end()
        marcas.append((evento['offset']/10_000_000,max(.01,evento.get('duration',0)/10_000_000),inicio,fin))
        cursor=fin
    return marcas

def avance_texto(texto,posicion,duracion,marcas=()):
    if marcas:
        previo=0
        for offset,largo,inicio,fin in marcas:
            if posicion<offset:return previo
            if posicion<offset+largo:
                return min(len(texto),inicio+int((fin-inicio)*max(0,(posicion-offset)/largo)))
            previo=fin
        return len(texto)
    if duracion>0:return min(len(texto),max(0,int(len(texto)*posicion/duracion)))
    return 0
