"""Secuencia visual de enlace. No bloquea el audio ni simula carga del modelo."""
import math
import random
from fuentes import FAMILIA

DURACION=2.8
VIAJE=.58


def descarga(c,puntos,intensidad=1,grueso=1):
    """Halo por capas y núcleo blanco; sin rectángulos que tapen el escritorio."""
    capas=[('#471020',17),('#8e142c',11),('#ec2249',6),('#ff697d',3),('#ffe9e9',1)]
    if grueso<.9:capas=capas[:3]
    for color,ancho in capas:
        c.create_line(*puntos,fill=color,width=max(1,ancho*grueso*intensidad),joinstyle='bevel',tags='descarga')


def trayectoria(t,inicio,fin):
    t=max(0,min(1,t));avance=t*t*(3-2*t)
    return (inicio[0]+(fin[0]-inicio[0])*avance,
            inicio[1]+(fin[1]-inicio[1])*avance-32*math.sin(math.pi*t))


def dibujar_viaje(c,p,inicio=(70,150),fin=(290,150),imagen=None):
    t=max(0,min(1,(p-VIAJE)/(1-VIAJE)));rng=random.Random(180+int(t*55))
    dx=fin[0]-inicio[0];dy=fin[1]-inicio[1];distancia=max(1,math.hypot(dx,dy))
    nx=-dy/distancia;ny=dx/distancia
    cabeza=trayectoria(t,inicio,fin)
    # Un relámpago principal con pocos quiebres grandes y retrocesos.
    # Los destellos cambian de polaridad y longitud, sin haces paralelos.
    cola=trayectoria(max(0,t-rng.uniform(.26,.39)),inicio,fin)
    amplitud=min(42,12+math.hypot(cabeza[0]-cola[0],cabeza[1]-cola[1])*.12)
    signo=rng.choice((-1,1));puntos=[]
    for avance,desvio in ((0,0),(.37,-1),(.24,.35),(.74,-.28),(.60,1),(1,0)):
        x=cola[0]+(cabeza[0]-cola[0])*avance+nx*desvio*amplitud*signo
        y=cola[1]+(cabeza[1]-cola[1])*avance+ny*desvio*amplitud*signo
        puntos.extend((x,y))
    descarga(c,puntos,grueso=1 if int(t*55)%3 else .65)
    # Una o dos bifurcaciones breves; nunca otra cinta de extremo a extremo.
    for j in rng.sample((1,3,4),rng.choice((1,2))):
        x,y=puntos[j*2:j*2+2];lado=rng.choice((-1,1));largo=rng.uniform(22,48)
        descarga(c,[x,y,x+nx*largo*.55*lado-8,y+ny*largo*.55*lado,
                    x+nx*largo*.32*lado+3,y+ny*largo*.32*lado-5,
                    x+nx*largo*lado-14,y+ny*largo*lado],grueso=.28)
    # Pocas chispas aisladas, dejando espacio vacío entre descargas.
    for i in range(7):
        retraso=rng.uniform(.015,.4);u=max(0,t-retraso)
        x,y=trayectoria(u,inicio,fin);salto=rng.uniform(-65,65)*min(1,t*5)
        x+=nx*salto;y+=ny*salto
        longitud=rng.uniform(7,27);color=rng.choice(('#ff335c','#ff6982','#ffd3db'))
        c.create_line(x-longitud,y+3,x,y,fill=color,width=rng.choice((1,1,2)),tags='chispa')
    # Glitch horizontal, con ecos rojos desplazados y una descarga al aterrizar.
    for i in range(3):
        x=cabeza[0]+rng.uniform(-65,20);y=cabeza[1]+rng.uniform(-35,35)
        c.create_line(x-rng.uniform(12,65),y,x,y,fill='#c9224b' if i%2 else '#ff5676',width=rng.choice((1,2,3)),tags='estela')
    pulso=max(0,1-abs(t-.08)*7)+max(0,(t-.85)/.15)
    for i in range(4 if pulso>.25 else 0):
        a=i*math.pi/2+rng.uniform(-.3,.3);r=12+pulso*35
        x,y=cabeza;descarga(c,[x,y,x+math.cos(a)*r*.5,y+math.sin(a)*r*.5,
                                x+math.cos(a+.22)*r,y+math.sin(a+.22)*r],grueso=.3)
    if t>.89 and imagen is not None:
        # Reaparición con cortes breves, no una espera inmóvil antes del panel.
        if int(t*85)%3!=0:c.create_image(fin[0],fin[1],image=imagen)


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

def dibujar(c,progreso,imagen=None,escala=1,ruta=None):
    p=max(0,min(1,progreso));c.delete('all')
    if p>=VIAJE:
        dibujar_viaje(c,p,*(ruta or ((70,150),(290,150))),imagen=imagen)
        return
    c.create_polygon(13,11,343,11,352,20,352,280,342,290,8,290,8,20,fill='#070d16',outline='#6b969e')
    if imagen is not None and p>.12:
        c.create_image(180,153,image=imagen)
        apertura=min(1,(p-.12)/.38);margen=(1-apertura)*105
        c.create_rectangle(19,47,341,47+margen,fill='#070d16',outline='')
        c.create_rectangle(19,257-margen,341,258,fill='#070d16',outline='')
    if p<.64:
        radio=35+14*math.sin(p*math.pi)
        for i in range(8):
            a=p*8+i*math.pi/4;x=180+radio*math.cos(a);y=151+radio*math.sin(a)
            c.create_line(x,y,x+9*math.cos(a),y+9*math.sin(a),fill='#f1d65e' if i%2 else '#7de0df',width=2)
    titulo='CAPRI'[:min(5,1+int(p*13))]
    if p<.27:titulo+=' /_'[int(p*100)%3]
    c.create_text(180,30,text=titulo,fill='#f0da68',font=(FAMILIA,round(22*escala),'bold'))
    c.create_rectangle(103,133,257,173,fill='#0b111b',outline='#e83c61')
    c.create_text(180,153,text='CONECTANDO',fill='#f3d568',font=(FAMILIA,max(8,round(12*escala)),'bold'))
    if p>.43:dibujar_carga(c,p)
    longitud=300*p;c.create_line(30,285,30+longitud,285,fill='#ec3c62',width=2)
    if .12<p<.48 or .7<p<.77:
        for i in range(3):
            y=65+(int(p*650)+i*39)%170
            c.create_line(25+i*12,y,330-i*8,y,fill='#6cdad9' if i%2 else '#ec3c62',width=2)
