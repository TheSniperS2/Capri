"""Despedida vectorial: mano roja que señala y se reúne con una estrella."""
import math
import json
from pathlib import Path
from functools import lru_cache
from intro import suave,dibujar_viaje,VIAJE,trayectoria

DURACION=4.4
DURACION_TELON=.95
COLOR_MANO='#f60031'

def estrella(c,x,y,pulso=1):
    if pulso<.004:return
    for radio,color in ((11*pulso,'#286d88'),(7*pulso,'#80efff'),(4*pulso,'#ffffff')):
        c.create_oval(x-radio,y-radio,x+radio,y+radio,fill=color,outline='',tags='estrella')
    for radio,color in ((145*pulso,'#326580'),(105*pulso,'#65dbf4'),(52*pulso,'#ffffff')):
        puntos=[]
        for dx,dy in ((0,-radio),(2,-3),(radio,0),(3,2),(0,radio),(-2,3),(-radio,0),(-3,-2)):
            a=-.55;puntos.extend((x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a)))
        c.create_polygon(*puntos,fill=color,outline='',tags='estrella')

def silueta_mano(x,y,alto):
    trazado=mano_trazada()
    if trazado:
        ax,ay=trazado['ancla'];s=alto/trazado['alto_visible']
        return [(x+(px-ax)*s,y+(py-ay)*s) for px,py in contorno_suave()]
    # Contorno trazado de la referencia 201212: conserva las articulaciones y
    # los cambios de curva del pulgar, nudillos y muñeca (error de trazo <1 px).
    referencia=[(195,60),(195,65),(197,68),(197,72),(200,82),(200,90),(196,99),
                (194,123),(183,144),(182,157),(192,178),(202,188),(209,194),
                (215,197),(230,201),(232,203),(232,214),(236,223),(236,228),
                (239,235),(246,241),(247,246),(248,262),(237,273),(223,277),
                (220,288),(212,304),(212,323),(217,344),(219,365),(226,401),
                (227,415),(231,432),(231,439),(236,463),(238,480),(244,497),
                (274,557),(301,604),(321,635),(340,670),(390,780),(205,780),
                (167,670),(154,649),(151,642),(148,639),(126,604),(121,591),
                (121,586),(124,578),(124,574),(130,559),(136,536),(140,505),
                (142,498),(142,492),(143,491),(143,485),(145,479),(147,459),
                (157,411),(158,397),(159,396),(159,384),(160,383),(160,361),
                (161,360),(160,326),(156,314),(149,301),(143,286),(138,266),
                (137,265),(108,264),(105,263),(99,259),(98,251),(101,240),
                (104,238),(116,236),(137,211),(150,184),(156,168),(157,161),
                (161,151),(163,142),(164,128),(181,98),(194,66),(195,60)]
    return [(x+(px-195)/610*alto,y+(py-60)/610*alto) for px,py in referencia]

@lru_cache(maxsize=1)
def mano_trazada():
    ruta=next((r for r in (Path(__file__).parent/'assets/mano-despedida-v3.json',Path(__file__).parents[1]/'assets/mano-despedida-v3.json') if r.exists()),None)
    return json.loads(ruta.read_text(encoding='utf8')) if ruta else None

@lru_cache(maxsize=1)
def contorno_suave():
    puntos=mano_trazada()['puntos'];n=len(puntos);tangentes=[]
    for i,p in enumerate(puntos):
        a=puntos[(i-1)%n];b=puntos[(i+1)%n];u=(p[0]-a[0],p[1]-a[1]);v=(b[0]-p[0],b[1]-p[1])
        norma=math.hypot(*u)*math.hypot(*v);coseno=(u[0]*v[0]+u[1]*v[1])/max(.001,norma)
        # La punta y los cambios deliberados de ángulo se conservan, no se redondean.
        tangentes.append(((b[0]-a[0])*.32,(b[1]-a[1])*.32) if coseno>.45 else (0,0))
    salida=[]
    for i,a in enumerate(puntos):
        b=puntos[(i+1)%n];ta=tangentes[i];tb=tangentes[(i+1)%n]
        pasos=max(3,math.ceil(math.dist(a,b)/2))
        for j in range(pasos):
            t=j/pasos;h0=2*t**3-3*t*t+1;h1=t**3-2*t*t+t;h2=-2*t**3+3*t*t;h3=t**3-t*t
            salida.append(tuple(h0*a[k]+h1*ta[k]+h2*b[k]+h3*tb[k] for k in (0,1)))
    return salida

def recortar(vertices,limite,superior,eje=1):
    resultado=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        da=(a[eje]>=limite) if superior else (a[eje]<=limite)
        db=(b[eje]>=limite) if superior else (b[eje]<=limite)
        if da:resultado.append(a)
        if da!=db:
            t=(limite-a[eje])/(b[eje]-a[eje]);resultado.append(tuple(a[j]+(b[j]-a[j])*t for j in (0,1)))
    return resultado

class EnergiaEscalada:
    """Reutiliza el renderer del personaje, ajustando su volumen alrededor de la cabeza."""
    def __init__(self,canvas,cabeza,escala,local,angulo):
        self.canvas=canvas;self.cabeza=cabeza;self.escala=escala;self.local=local;self.angulo=angulo
        self.lenguas=0

    def pintar(self,tipo,puntos,opciones):
        x,y=self.cabeza;s=self.escala;ox,oy=self.local
        opciones=dict(opciones)
        if tipo=='create_polygon' and opciones.get('tags')=='descarga' and self.lenguas<6:
            i=self.lenguas;self.lenguas+=1
            if i not in (1,3,4):return
            retraso={1:0,3:42,4:90}[i]
            # Tres puntas escalonadas que confluyen: evita un peine de rayos paralelos.
            puntos=[v for px,py in zip(puntos[::2],puntos[1::2]) for v in
                    (px-retraso,oy+(py-oy)*max(.06,min(1,(ox+36-px)/160)))]
            opciones['fill']=('#f60031' if i==1 else '#d90039')
        ca=math.cos(self.angulo);sa=math.sin(self.angulo)
        puntos=[v for px,py in zip(puntos[::2],puntos[1::2]) for v in
                (x+((px-ox)*ca-(py-oy)*sa)*s,y+((px-ox)*sa+(py-oy)*ca)*s)]
        if 'width' in opciones:opciones['width']=max(.2,opciones['width']*s)
        etiquetas=opciones.get('tags',())
        if isinstance(etiquetas,str):etiquetas=(etiquetas,)
        opciones['tags']=tuple(etiquetas)+('energia_despedida',)
        return getattr(self.canvas,tipo)(*puntos,**opciones)

    def create_polygon(self,*p,**kw):return self.pintar('create_polygon',p,kw)
    def create_line(self,*p,**kw):return self.pintar('create_line',p,kw)

class Despedida:
    def __init__(self,ancho,alto,origen,imagen=None):
        self.ancho=ancho;self.alto=alto;self.origen=origen;self.imagen=imagen
        self.destino=(ancho*.5,alto*.09)
        self.piezas=self.preparar_formacion()
        self.cielo=self.preparar_cielo()
        self.mano_foto,self.mano_esquina=self.preparar_mano_suave()
        self.contraccion=None

    def posicion_mano(self):
        return self.ancho*.495,self.alto*.43,self.alto*.57

    def preparar_mano_suave(self):
        from PIL import Image,ImageDraw,ImageTk
        mano=silueta_mano(*self.posicion_mano());margen=3
        l=math.floor(min(x for x,y in mano))-margen;t=math.floor(min(y for x,y in mano))-margen
        r=math.ceil(max(x for x,y in mano))+margen;b=min(self.alto+60,math.ceil(max(y for x,y in mano))+margen)
        w,h=r-l,b-t;k=4
        mascara=Image.new('L',(w*k,h*k));d=ImageDraw.Draw(mascara)
        d.polygon([((x-l)*k,(y-t)*k) for x,y in mano],fill=255)
        mascara=mascara.resize((w,h),Image.Resampling.LANCZOS)
        im=Image.new('RGBA',(w,h),COLOR_MANO);im.putalpha(mascara)
        return ImageTk.PhotoImage(im),(l,t)

    def preparar_cielo(self):
        """Fondo nocturno propio, sin capturas ni fotogramas del video de referencia."""
        from PIL import Image,ImageTk,ImageDraw,ImageFilter,ImageOps
        from pathlib import Path
        ruta=next((r for r in (Path(__file__).parent/'assets/capri-cielo-despedida-v2.png',Path(__file__).parents[1]/'assets/capri-cielo-despedida-v2.png') if r.exists()),None)
        if ruta:
            with Image.open(ruta) as fondo:im=ImageOps.fit(fondo.convert('RGB'),(self.ancho,self.alto),Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
        import random
        rng=random.Random(2410);w,h=640,360
        im=Image.new('RGB',(w,h));d=ImageDraw.Draw(im)
        for y in range(h):
            q=y/h;d.line((0,y,w,y),fill=(round(7+6*q),round(14+10*q),round(25+15*q)))
        nubes=Image.new('RGBA',(w,h));d=ImageDraw.Draw(nubes)
        for _ in range(48):
            x=rng.randrange(-150,w);y=rng.randrange(60,h+40);rx=rng.randrange(55,150);ry=rng.randrange(10,35)
            d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(25,40,58,rng.randrange(45,125)))
        im=Image.alpha_composite(im.convert('RGBA'),nubes.filter(ImageFilter.GaussianBlur(12)))
        im=im.resize((self.ancho,self.alto),Image.Resampling.BILINEAR)
        return ImageTk.PhotoImage(im)

    def preparar_formacion(self):
        # Cada tesela de la transmisión tiene un destino dentro de la mano.
        # Se mantiene la identidad de la pieza durante todo el recorrido.
        from PIL import ImageTk
        import tkinter as tk
        original=None
        if self.imagen is not None:
            try:original=ImageTk.getimage(self.imagen).convert('RGB')
            except (tk.TclError,AttributeError,ValueError):pass
        iw,ih=original.size if original is not None else (360,210)
        mx,my,largo=self.posicion_mano();mano=silueta_mano(mx,my,largo)
        xmin=min(x for x,y in mano);xmax=max(x for x,y in mano)
        ymin=my;ymax=max(y for x,y in mano);destinos=[]
        for fila in range(14):
            for col in range(5):
                izquierda=xmin+(xmax-xmin)*col/5;derecha=xmin+(xmax-xmin)*(col+1)/5
                arriba=ymin+(ymax-ymin)*fila/14;abajo=ymin+(ymax-ymin)*(fila+1)/14
                pieza=recortar(recortar(mano,arriba,True),abajo,False)
                pieza=recortar(recortar(pieza,izquierda,True,0),derecha,False,0)
                if len(pieza)>=3:destinos.append(pieza)
        filas=math.ceil(len(destinos)/6);piezas=[]
        for i,objetivo in enumerate(destinos):
            col=i%6;fila=i//6
            x0=self.origen[0]-iw/2+col*iw/6;y0=self.origen[1]-ih/2+fila*ih/filas
            xs=[x for x,y in objetivo];ys=[y for x,y in objetivo]
            l,r=min(xs),max(xs);a,b=min(ys),max(ys)
            fuente=[(x0+(x-l)/max(.01,r-l)*iw/6,y0+(y-a)/max(.01,b-a)*ih/filas) for x,y in objetivo]
            color=original.getpixel((min(iw-1,round((col+.5)*iw/6)),min(ih-1,round((fila+.5)*ih/filas)))) if original is not None else (75,20,65)
            piezas.append((fuente,objetivo,color,i))
        return piezas

    def formar_mano(self,c,p):
        for fuente,objetivo,color,i in self.piezas:
            retraso=(i%6)*.009+(i//6)*.002
            t=suave((p-retraso)/(.30-retraso))
            arco=math.sin(math.pi*t);lado=-1 if i%2 else 1
            puntos=[v for a,b in zip(fuente,objetivo) for v in
                    (a[0]+(b[0]-a[0])*t+lado*self.ancho*.023*arco,
                     a[1]+(b[1]-a[1])*t-self.alto*.075*arco)]
            rojo=suave(min(1,t*1.6));rgb=tuple(round(a+(b-a)*rojo) for a,b in zip(color,(246,0,49)))
            c.create_polygon(*puntos,fill='#%02x%02x%02x'%rgb,outline='',tags='fragmento_formacion')

    def dibujar(self,c,progreso):
        p=max(0,min(1,progreso));c.delete('all');sx,sy=self.destino
        c.create_image(0,0,image=self.cielo,anchor='nw',tags='cielo_despedida')
        apagar=1-suave((p-.91)/.09)
        brillo=(.78+.035*math.sin(p*23)+.65*math.exp(-((p-.89)/.025)**2))*apagar
        estrella(c,sx,sy,brillo*.28)
        centro=(self.ancho*.495,self.alto*.58)
        if p<.32:
            if self.contraccion is not None:self.contraccion.dibujar(c,p/.32)
            else:
                if p<.012 and self.imagen is not None:c.create_image(*self.origen,image=self.imagen,tags='capri_al_centro')
                self.formar_mano(c,p)
        elif self.contraccion is not None:self.contraccion.detener()
        mx,y,largo=self.posicion_mano()
        if .32<=p<.70:
            mano=silueta_mano(mx,y,largo)
            romper=max(0,(p-.58)/.12)
            if romper==0 and len(mano)>=3:
                c.create_image(*self.mano_esquina,image=self.mano_foto,anchor='nw',tags='mano_despedida')
            else:
                # El volumen de la mano se deshilacha en cortes hacia la descarga.
                for i in range(80):
                    q=suave((romper-(79-i)*.004)/.68)
                    if q>=.995:continue
                    superior=y+largo*i/68;inferior=y+largo*(i+1)/68
                    franja=recortar(recortar(mano,superior,True),inferior,False)
                    puntos=[v for px,py in franja for v in
                            (mx+(px-mx)*(1-q)+math.sin(i*.15)*largo*.008*q,
                             py-largo*.28*q*q)]
                    if len(puntos)>=6:c.create_polygon(*puntos,fill=COLOR_MANO,outline='',tags='mano_despedida')
        if .60<=p<.92:
            t=max(0,min(1,(p-.60)/.28));inicio=(mx,self.alto*.70)
            cabeza=trayectoria(t,inicio,self.destino)
            # Arranca con el ancho del antebrazo, se afila solo al aproximarse a la luz.
            absorber=1-suave((p-.88)/.04)
            escala=(self.alto/1080)*(1.65*(1-suave(t))+.25)*absorber
            distancia=math.hypot(sx-inicio[0],sy-inicio[1]);fin_local=(distancia,0)
            local=trayectoria(t,(0,0),fin_local)
            angulo=math.atan2(sy-inicio[1],sx-inicio[0])
            lienzo=EnergiaEscalada(c,cabeza,escala,local,angulo)
            dibujar_viaje(lienzo,VIAJE+(1-VIAJE)*t,(0,0),fin_local)
            # Esta punta permanece visible hasta tocar exactamente el núcleo.
            radio=max(.1,self.alto/1080*4*absorber)
            c.create_oval(cabeza[0]-radio,cabeza[1]-radio,cabeza[0]+radio,cabeza[1]+radio,
                          fill='#ff5070',outline='',tags='punta_estrella')
        if .82<p<1:
            pulso=suave((p-.82)/.10);radio=(8+pulso*65)*apagar
            for i in range(7):
                a=i*math.pi*2/7+p*.7;r=radio*(.65+(i%3)*.15)
                longitud=(2+9*(1-pulso))*apagar
                c.create_line(sx+math.cos(a)*r,sy+math.sin(a)*r,
                              sx+math.cos(a)*(r+longitud),sy+math.sin(a)*(r+longitud),
                              fill='#a9edff',width=max(1,2*apagar),tags='destello')

    def cerrar_telon(self,c,progreso):
        # El cielo queda inmóvil. La ventana pierde opacidad desde app.py,
        # revelando el escritorio sin barridos ni un corte a negro.
        c.delete('all')
        c.create_image(0,0,image=self.cielo,anchor='nw',tags='telon_despedida')

    def detener(self):
        if self.contraccion is not None:self.contraccion.detener()
