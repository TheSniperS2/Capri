"""Geometrías del monitor y su entrada, independientes de la señal y el color."""
from tema_ui import color

DISENOS={'clasico':'Clásico','terminal':'Terminal','visor':'Nexo',
         'retro':'Retro','compacto':'Estudio','minimal':'Vector'}
ANTERIORES={'original':'clasico','neon':'terminal','hielo':'visor','ambar':'retro','nocturna':'compacto','vhs':'minimal'}

def normalizar(diseno):return ANTERIORES.get(diseno,diseno) if diseno in DISENOS or diseno in ANTERIORES else 'clasico'

def chaflan(izq,arr,der,ab,corte=8):
    """Tres cortes a 45°; el inferior izquierdo permanece cuadrado."""
    corte=max(0,min(corte,(der-izq)/2-1,(ab-arr)/2-1))
    return (izq+corte,arr,der-corte,arr,der,arr+corte,
            der,ab-corte,der-corte,ab,izq,ab,izq,arr+corte)

def ancho_entrada(diseno,w):
    reserva=90 if normalizar(diseno)=='compacto' else (98 if normalizar(diseno)=='minimal' else 78)
    return max(110,w-reserva)

def superficie(c,diseno,w,h,chat=False):
    diseno=normalizar(diseno);fondo=color('#170c12' if chat else '#120b10');borde=color('#8e304a');acento=color('#ff4267')
    tags='marco'
    contorno=('marco','borde_entrada') if chat else tags
    def linea(*p,**kw):c.create_line(*p,fill=borde,tags=tags,**kw)
    def rect(*p,**kw):c.create_rectangle(*p,fill=fondo,outline=borde,tags=contorno,**kw)
    def poly(*p,**kw):c.create_polygon(*p,fill=fondo,outline=borde,tags=contorno,**kw)
    izq,arr,der,ab=(5,4,w-4,h-4) if chat else (8,11,w-8,h-3)
    if diseno=='clasico':
        poly(*chaflan(izq,arr,der,ab,8 if chat else 10))
    elif diseno=='terminal':
        c.create_rectangle(izq,arr,der,ab,fill=color('#101016') if not chat else fondo,outline=borde,tags=contorno)
        if not chat:
            from fuentes import FAMILIA
            c.create_text(22,h-12,text='SEÑAL VIVA',anchor='w',fill=color('#bb929f'),font=(FAMILIA,7),tags=tags)
            c.create_rectangle(w-34,h-16,w-28,h-10,fill=acento,outline='',tags=tags)
            c.create_rectangle(w-23,h-16,w-17,h-10,fill=borde,outline='',tags=tags)
    elif diseno=='visor':
        if chat:
            # El borde superior queda fuera de la ventana nativa del Entry.
            poly(*chaflan(izq,arr,der,ab,8))
            c.create_rectangle(izq+2,arr+12,izq+4,ab-9,fill=acento,outline='',tags=tags)
            c.create_rectangle(der-4,arr+12,der-2,ab-9,fill=acento,outline='',tags=tags)
        else:
            poly(8,23,20,11,122,11,132,17,w-25,17,w-8,34,w-8,h-15,w-20,h-3,
                 218,h-3,210,h-10,150,h-10,142,h-3,8,h-3)
            c.create_polygon(*chaflan(20,17,118,40,5),fill=acento,outline='',tags=tags)
            rect(18,53,w-18,h-25)
            c.create_rectangle(10,83,13,h-56,fill=acento,outline='',tags=tags)
            c.create_rectangle(w-13,96,w-10,h-69,fill=acento,outline='',tags=tags)
    elif diseno=='retro':
        r=12 if chat else 19
        poly(izq+r,arr,der-r,arr,der,arr,der,arr+r,der,ab-r,der,ab,der-r,ab,
             izq+r,ab,izq,ab,izq,ab-r,izq,arr+r,izq,arr,smooth=True,splinesteps=18,width=2)
        if not chat:
            c.create_oval(der-25,arr+12,der-20,arr+17,fill=acento,outline='',tags=tags)
            linea(izq+15,ab-7,der-15,ab-7)
    elif diseno=='compacto':
        if chat:
            rect(izq,arr,der,ab)
            c.create_rectangle(der-39,arr+1,der-1,ab-1,fill=color('#35101d'),outline='',tags=tags)
            linea(der-40,arr,der-40,ab)
        else:
            rect(8,11,w-8,h-3)
            c.create_rectangle(9,12,w-9,43,fill=color('#35101d'),outline='',tags=tags)
            c.create_rectangle(19,24,25,30,fill=acento,outline='',tags=tags)
            rect(17,52,w-17,h-24)
            for dx in range(0,70,5):c.create_rectangle(22+dx,h-15,24+dx,h-10,fill=borde,outline='',tags=tags)
            linea(w-42,h-12,w-22,h-12)
    else:
        if chat:
            poly(izq+8,arr,w-48,arr,w-48,ab,izq,ab,izq,arr+8)
            c.create_polygon(*chaflan(w-40,arr,der,ab,6),fill=color('#35101d'),outline=borde,tags=contorno)
        else:
            # Cabecera y visor son piezas cerradas, separadas por un margen real.
            c.create_polygon(*chaflan(8,11,w-8,41,6),fill=color('#211018'),outline=borde,tags=tags)
            poly(8,48,w-20,48,w-8,60,w-8,h-16,w-20,h-4,8,h-4)
            c.create_polygon(23,26,28,21,33,26,28,31,fill=acento,outline='',tags=tags)
            c.create_polygon(w/2-5,h-13,w/2,h-18,w/2+5,h-13,w/2,h-8,fill=acento,outline='',tags=tags)
    if not chat:
        if diseno in ('clasico','terminal','retro'):linea(23,43,w-21,43)
        if diseno=='clasico':
            # Un único trazo cerrado: no hay piezas ni empalmes superpuestos.
            c.create_rectangle(17,52,w-17,h-24,fill='',outline=acento,width=1,tags=tags)

def cabecera(c,diseno,estado='F8',tinta=None,escala=1):
    from fuentes import FAMILIA
    diseno=normalizar(diseno)
    x=30 if diseno=='visor' else (39 if diseno=='compacto' else (180 if diseno=='minimal' else 25))
    c.create_text(x,28,text='> CAPRI_' if diseno=='terminal' else 'CAPRI',anchor='center' if diseno=='minimal' else 'w',
                  fill=color('#10090d' if diseno=='visor' else ('#ffb1c2' if diseno=='terminal' else '#edf6f6')),
                  font=('Consolas' if diseno=='terminal' else FAMILIA,round((12 if diseno=='terminal' else 13)*escala),'bold'))
    c.create_text(310,29,text=estado,anchor='e',fill=color(tinta or '#ed6684'),font=(FAMILIA,max(8,round(9*escala))))
