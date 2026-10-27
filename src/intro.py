"""Secuencia visual de enlace. No bloquea el audio ni simula carga del modelo."""
import math
import random
from PIL import Image,ImageTk,ImageChops,ImageDraw
from fuentes import FAMILIA

DURACION=2.8
VIAJE=.58


class Fragmentos:
    """Bandas del avatar preparadas una vez; ninguna imagen se genera por frame."""
    def __init__(self,vista,escala):
        self.fotos=[];self.bandas=[]
        original=vista.convert('RGBA');r,g,b,_=original.split()
        mascara=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda v:0 if v<40 else min(255,(v-40)*5))
        original.putalpha(mascara)
        roja=Image.new('RGBA',original.size,'#ff003e');roja.putalpha(mascara)
        cortes=(0,16,42,57,91,107,139,153,181,210)
        for i,(y,fin) in enumerate(zip(cortes,cortes[1:])):
            h=fin-y;rng=random.Random(81+i)
            # Recortes oblicuos y longitudes distintas evitan barras rectangulares.
            borde=Image.new('L',(320,h));d=ImageDraw.Draw(borde)
            izq=rng.randint(4,55);der=rng.randint(260,316)
            d.polygon([(izq,0),(der-26,0),(der-42,h*.35),(der,h*.66),(der-62,h),
                       (izq+12,h),(izq+38,h*.58),(max(0,izq-20),h*.25)],fill=255)
            par=[]
            for j,imagen in enumerate((original,roja)):
                tira=imagen.crop((0,y,320,fin))
                tira.putalpha(ImageChops.multiply(tira.getchannel('A'),borde))
                if j:tira=tira.rotate((-1 if i%2 else 1)*(3+i%4),expand=True,resample=Image.Resampling.BILINEAR)
                tira=tira.resize((round(tira.width*escala),max(1,round(tira.height*escala))),Image.Resampling.BILINEAR)
                foto=ImageTk.PhotoImage(tira);self.fotos.append(foto);par.append(foto)
            self.bandas.append(((y+fin)/2-105,par))

    def dibujar(self,c,centro,dispersion,rojo,tiempo):
        for i,(altura,par) in enumerate(self.bandas):
            rng=random.Random(310+i);sentido=-1 if i%3 else 1
            x=centro[0]+sentido*dispersion*rng.uniform(30,125)
            y=centro[1]+altura+dispersion*math.sin(i*2.7)*15
            # El color migra por las bandas, dejando entrever ojos y rostro.
            coloreada=((i*7+int(tiempo*16))%10)/10<rojo
            c.create_image(x,y,image=par[int(coloreada)],tags='fragmento_capri')


def descarga(c,puntos,intensidad=1,grueso=1):
    """Silueta roja plana: se ensancha en los codos y termina en agujas."""
    centros=list(zip(puntos[::2],puntos[1::2]));izquierda=[];derecha=[]
    for i,(x,y) in enumerate(centros):
        antes=centros[max(0,i-1)];despues=centros[min(len(centros)-1,i+1)]
        dx=despues[0]-antes[0];dy=despues[1]-antes[1];largo=max(1,math.hypot(dx,dy))
        # Grosor muy desigual, independiente de un trazo de ancho constante.
        ancho=0 if i in (0,len(centros)-1) else (12 if i%2 else 2.4)*grueso*intensidad
        izquierda.extend((x-dy/largo*ancho,y+dx/largo*ancho))
        derecha[0:0]=[x+dy/largo*ancho,y-dx/largo*ancho]
    c.create_polygon(*(izquierda+derecha),fill='#ff003e',outline='',tags='descarga')
    # Pequeñas aletas angulares en los codos, como cortes de tinta roja.
    for i in range(1,len(centros)-1,2):
        x,y=centros[i];px,py=centros[i-1];dx=x-px;dy=y-py;largo=max(1,math.hypot(dx,dy))
        s=grueso*intensidad
        c.create_polygon(x,y,x-dx/largo*17*s-dy/largo*8*s,y-dy/largo*17*s+dx/largo*8*s,
                         x+dx/largo*9*s,y+dy/largo*9*s,fill='#ff003e',outline='',tags='descarga')


def trayectoria(t,inicio,fin):
    t=max(0,min(1,t));avance=t*t*(3-2*t)
    return (inicio[0]+(fin[0]-inicio[0])*avance,
            inicio[1]+(fin[1]-inicio[1])*avance-32*math.sin(math.pi*t))


def dibujar_viaje(c,p,inicio=(70,150),fin=(290,150),imagen=None,fragmentos=None):
    t=max(0,min(1,(p-VIAJE)/(1-VIAJE)));rng=random.Random(180+int(t*55))
    dx=fin[0]-inicio[0];dy=fin[1]-inicio[1];distancia=max(1,math.hypot(dx,dy))
    nx=-dy/distancia;ny=dx/distancia
    cabeza=trayectoria(t,inicio,fin)
    salida=min(1,t/.2);llegada=max(0,min(1,(t-.70)/.30))
    energia=math.sin(math.pi*min(1,t))**.45
    # Grandes lenguas de energía: cada una tiene su propio ancho y sus cortes.
    # El personaje se pierde dentro del barrido y se recompone al llegar.
    for i in range(6):
        cola=trayectoria(max(0,t-rng.uniform(.22,.47)),inicio,fin)
        desplazamiento=(i-2.5)*27*energia
        cx=cabeza[0]+nx*desplazamiento;cy=cabeza[1]+ny*desplazamiento
        tx=cola[0]+nx*desplazamiento*1.4-35*energia;ty=cola[1]+ny*desplazamiento*1.4
        largo=cx-tx;alto=cy-ty;ancho=rng.uniform(8,20)*energia
        c.create_polygon(tx-45*energia,ty,cx-largo*.62-nx*ancho,cy-alto*.62-ny*ancho,
                         cx-largo*.49-nx*ancho*.25,cy-alto*.49-ny*ancho*.25,
                         cx-15*energia,cy-ny*ancho,cx+35*energia,cy,
                         cx-largo*.24+nx*ancho,cy-alto*.24+ny*ancho,
                         cx-largo*.36+nx*ancho*.3,cy-alto*.36+ny*ancho*.3,
                         tx+nx*ancho*.35,ty+ny*ancho*.35,
                         fill='#ff003e' if i%2 else '#ed003a',outline='',tags='descarga')
    if fragmentos:
        dispersion=salida*(1-llegada)*.85
        fragmentos.dibujar(c,cabeza,dispersion,min(.9,salida*.9)*(1-llegada),t)
    # Pocas chispas aisladas, dejando espacio vacío entre descargas.
    for i in range(7):
        retraso=rng.uniform(.015,.4);u=max(0,t-retraso)
        x,y=trayectoria(u,inicio,fin);salto=rng.uniform(-65,65)*min(1,t*5)
        x+=nx*salto;y+=ny*salto
        longitud=rng.uniform(5,17)
        c.create_polygon(x,y,x-longitud,y+3,x-longitud*.6,y-2,fill='#ff003e',outline='',tags='chispa')
    # Glitch horizontal, con ecos rojos desplazados y una descarga al aterrizar.
    for i in range(3):
        x=cabeza[0]+rng.uniform(-65,20);y=cabeza[1]+rng.uniform(-35,35)
        c.create_line(x-rng.uniform(12,65),y,x,y,fill='#e40038',width=1,tags='estela')
    pulso=max(0,1-abs(t-.08)*7)+max(0,(t-.85)/.15)
    for i in range(4 if pulso>.25 else 0):
        a=i*math.pi/2+rng.uniform(-.3,.3);r=12+pulso*35
        x,y=cabeza;descarga(c,[x,y,x+math.cos(a)*r*.5,y+math.sin(a)*r*.5,
                                x+math.cos(a+.22)*r,y+math.sin(a+.22)*r],grueso=.3)
    if t>.97 and imagen is not None:
        c.create_image(fin[0],fin[1],image=imagen)


def dibujar_carga(c,p):
    carga=max(0,min(1,(p-.43)/(VIAJE-.43)));rng=random.Random(40+int(p*95))
    for i in range(8):
        a=i*math.pi/4;radio=40+75*carga
        x=180+math.cos(a)*radio;y=153+math.sin(a)*radio*.7
        descarga(c,[x,y,x+rng.uniform(-18,18),y+rng.uniform(-12,12),
                    x+math.cos(a)*28,y+math.sin(a)*24],grueso=.35)
    for i in range(5):
        y=rng.uniform(65,245);x=rng.uniform(25,230)
        c.create_line(x,y,min(337,x+40+80*carga),y,fill='#fb355b',width=rng.choice((1,2,3)))


def romper_carcasa(c,p):
    """El marco se cuartea en su sitio y se consume antes de cambiar de ventana."""
    q=max(0,min(1,(p-.39)/.17))
    if q<=0:
        c.create_polygon(13,11,343,11,352,20,352,280,342,290,8,290,8,20,
                         fill='#070d16',outline='#6b969e')
        return
    # Teselas con tiempos de ruptura distintos: dejan huecos transparentes.
    for fila in range(5):
        for columna in range(6):
            rng=random.Random(510+fila*6+columna)
            muerte=rng.uniform(.28,.95)
            if q>=muerte:continue
            rotura=max(0,(q-(muerte-.25))/.25)
            x=13+columna*55+rng.uniform(-10,10)*rotura
            y=11+fila*55+rng.uniform(-8,8)*rotura
            c.create_polygon(x,y,x+55,y+3*rotura,x+52-rotura*8,y+55,x+rotura*10,y+52,
                             fill='#070d16' if rotura<.7 else '#a70b32',outline='',tags='carcasa_rota')
            if rotura>.1:
                c.create_line(x,y,x+35*(1-rotura),y+8*rotura,fill='#ff003e',width=1,tags='carcasa_rota')
    # Los bordes pierden segmentos y se convierten en esquirlas muy cortas.
    for i in range(18):
        rng=random.Random(890+i)
        if q>rng.uniform(.3,.97):continue
        x=13+(i%6)*55;y=11 if i<6 else (286 if i<12 else 55+(i-12)*36)
        if i>=12:x=13 if i%2 else 343
        avance=max(0,q-.15)*rng.uniform(8,24)
        c.create_polygon(x-avance,y,x+25*(1-q),y-2,x+8,y+3+avance*.2,
                         fill='#ff003e',outline='',tags='carcasa_rota')


def dibujar(c,progreso,imagen=None,escala=1,ruta=None,fragmentos=None):
    p=max(0,min(1,progreso));c.delete('all')
    if p>=VIAJE:
        dibujar_viaje(c,p,*(ruta or ((70,150),(290,150))),imagen=imagen,fragmentos=fragmentos)
        return
    romper_carcasa(c,p)
    if imagen is not None and p>.12:
        if p>.43 and fragmentos:
            disolver=min(1,(p-.43)/(VIAJE-.43))
            fragmentos.dibujar(c,(180,153),disolver*.5,disolver,p)
        else:c.create_image(180,153,image=imagen)
        apertura=min(1,(p-.12)/.38);margen=(1-apertura)*105
        if p<=.39:
            c.create_rectangle(19,47,341,47+margen,fill='#070d16',outline='')
            c.create_rectangle(19,257-margen,341,258,fill='#070d16',outline='')
    if p<.43:
        radio=35+14*math.sin(p*math.pi)
        for i in range(8):
            a=p*8+i*math.pi/4;x=180+radio*math.cos(a);y=151+radio*math.sin(a)
            c.create_line(x,y,x+9*math.cos(a),y+9*math.sin(a),fill='#f1d65e' if i%2 else '#7de0df',width=2)
    titulo='CAPRI'[:min(5,1+int(p*13))]
    if p<.27:titulo+=' /_'[int(p*100)%3]
    if p<.46:
        c.create_text(180,30,text=titulo,fill='#f0da68',font=(FAMILIA,round(22*escala),'bold'))
        c.create_rectangle(103,133,257,173,fill='#0b111b',outline='#e83c61')
        c.create_text(180,153,text='CONECTANDO',fill='#f3d568',font=(FAMILIA,max(8,round(12*escala)),'bold'))
    if p>.43:dibujar_carga(c,p)
    if p<.43:
        longitud=300*p;c.create_line(30,285,30+longitud,285,fill='#ec3c62',width=2)
    if .12<p<.48 or .7<p<.77:
        for i in range(3):
            y=65+(int(p*650)+i*39)%170
            c.create_line(25+i*12,y,330-i*8,y,fill='#6cdad9' if i%2 else '#ec3c62',width=2)
