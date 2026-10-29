"""Personaje independiente: paseo, salto y apoyo sobre ventanas visibles."""
import math
import random
import time
from functools import lru_cache
from PIL import Image,ImageTk,ImageOps,ImageFilter,ImageChops,ImageDraw
from ventanas import area_trabajo,visibles


@lru_cache(maxsize=10)
def _mascara_cuerpo(mascara_bytes,w,h):
    mascara=Image.frombytes('L',(w,h),mascara_bytes)
    unida=mascara.filter(ImageFilter.MaxFilter(5))
    datos=bytearray(unida.tobytes());mayor=[]
    for inicio in range(w*h):
        if not datos[inicio]:continue
        pila=[inicio];datos[inicio]=0;grupo=[]
        while pila:
            i=pila.pop();grupo.append(i);x=i%w
            for vecino in ((i-1 if x else -1),(i+1 if x<w-1 else -1),i-w,i+w):
                if 0<=vecino<len(datos) and datos[vecino]:datos[vecino]=0;pila.append(vecino)
        if len(grupo)>len(mayor):mayor=grupo
    cuerpo=bytearray(w*h)
    for i in mayor:cuerpo[i]=255
    return bytes(cuerpo)

def limpiar_silueta(imagen):
    """Alfa binario para color-key de Windows y sin motas desconectadas."""
    im=imagen.convert('RGBA').copy();mascara=im.getchannel('A').point(lambda a:255 if a>=96 else 0)
    cuerpo=Image.frombytes('L',im.size,_mascara_cuerpo(mascara.tobytes(),*im.size))
    im.putalpha(ImageChops.multiply(mascara,cuerpo))
    return im

def glitch_silueta(imagen,variante):
    im=imagen.copy();w,h=im.size
    for fraccion,alto,dx in ((.24,.04,5),(.46,.06,-7),(.72,.025,4)):
        y=int(h*fraccion)+variante*3;fin=min(h,y+max(1,int(h*alto)))
        im.paste(imagen.crop((0,y,w,fin)),(dx,y))
        ImageDraw.Draw(im).line((0,y,w,y),fill=(255,0,62,255),width=1)
    # Jamás dejar píxeles fuera de la silueta original, ni alfa intermedio.
    im.putalpha(ImageChops.multiply(im.getchannel('A'),imagen.getchannel('A')))
    return im

COLORES_HALO={'violeta':'#9465ed','neon':'#72f59e','hielo':'#69d6f0','rojo':'#ef446b'}

def sombra_glitch(imagen,color):
    # Copia sólida desplazada detrás del cuerpo, no una dilatación de contorno.
    alfa=imagen.getchannel('A').copy()
    sombra=Image.new('RGBA',imagen.size,color);sombra.putalpha(alfa);return sombra

def con_sombra(imagen,halo):
    if halo not in COLORES_HALO:return imagen.copy()
    fondo=Image.new('RGBA',imagen.size)
    fondo.alpha_composite(sombra_glitch(imagen,COLORES_HALO[halo]),(-5,2))
    fondo.alpha_composite(imagen);return fondo

def pose_sujeta(imagen,agarre):
    """Eleva el brazo del sprite y lleva su mano al mango fijo del anclaje."""
    w,h=imagen.size;sx=w/210;sy=h/240
    mascara=Image.new('L',imagen.size)
    ImageDraw.Draw(mascara).polygon([(x*sx,y*sy) for x,y in
        ((114,96),(121,104),(105,119),(88,131),(86,151),(44,153),(44,125),(90,113))],fill=255)
    alfa=imagen.getchannel('A');brazo=imagen.copy()
    brazo.putalpha(ImageChops.multiply(alfa,mascara))
    cuerpo=imagen.copy();cuerpo.putalpha(ImageChops.subtract(alfa,brazo.getchannel('A')))
    hombro=(116*sx,102*sy);mano=(68*sx,134*sy)
    dx,dy=mano[0]-hombro[0],mano[1]-hombro[1]
    tx,ty=agarre[0]-hombro[0],agarre[1]-hombro[1]
    angulo=math.atan2(ty,tx)-math.atan2(dy,dx)
    escala=max(.5,min(1.6,math.hypot(tx,ty)/math.hypot(dx,dy)))
    a,b=math.cos(angulo)/escala,math.sin(angulo)/escala;d,e=-b,a
    ox,oy=hombro
    brazo=brazo.transform(imagen.size,Image.Transform.AFFINE,
        (a,b,ox-a*ox-b*oy,d,e,oy-d*ox-e*oy),Image.Resampling.BICUBIC)
    brazo.putalpha(brazo.getchannel('A').point(lambda v:255 if v>=96 else 0))
    cuerpo.alpha_composite(brazo)
    return cuerpo

def boca_personaje(imagen,sentada=False,abierta=False):
    im=imagen.copy();caja=(220,219,238,227) if sentada else (226,190,239,198)
    for y in range(caja[1],caja[3]):
        for x in range(caja[0],caja[2]):
            r,g,b,a=im.getpixel((x,y))
            if r>60 and r>max(g,b)*1.4:im.putpixel((x,y),(6,6,12,a))
    puntos=([(222,222),(236,219),(230,228)] if abierta else [(222,223),(228,225),(236,220)]) if sentada else ([(227,192),(237,190),(233,199)] if abierta else [(227,193),(232,195),(237,191)])
    pintura=Image.new('RGBA',im.size);d=ImageDraw.Draw(pintura)
    if abierta:d.polygon(puntos,fill='#ffffff')
    else:d.line(puntos,fill='#ffffff',width=1)
    for y in range(min(p[1] for p in puntos),max(p[1] for p in puntos)+1):
        for x in range(min(p[0] for p in puntos),max(p[0] for p in puntos)+1):
            if pintura.getpixel((x,y))[3] and max(im.getpixel((x,y))[:3])<100 and im.getpixel((x,y))[3]>100:im.putpixel((x,y),(255,255,255,255))
    return im

class Companera:
    def __init__(self,ruta):
        self.originales=[];self.fotos=[];self.espejos=[];self.escala=1
        self.x=0.;self.y=0.;self.direccion=-1;self.soporte=None;self.salto=None
        self.ventanas=[];self.revisar=0;self.ultimo=time.monotonic();self.proxima_accion=self.ultimo+7
        self.estado='quieta';self.quieta_hasta=0;self.libre=False
        self.ancla=None;self.velocidad_caida=0.;self.gracia_fisica=0.;self.proxima_ancla=0.;self.colgadas={}
        self.pasos=[];self.pasos_tk=[];self.pasos_espejo=[];self.fase_paso=0.;self.velocidad=0.;self.soporte_lado=None
        try:
            with Image.open(ruta) as atlas:
                w,h=atlas.size
                self.originales=[atlas.crop((col*w//3+round(w/3*.176),fila*h//2,col*w//3+round(w/3*.918),(fila+1)*h//2)).convert('RGBA')
                                 for fila in range(2) for col in range(3)]
        except OSError:pass
        if len(self.originales)==6:
            normal=self.originales[0];sentada=self.originales[3]
            self.originales[0]=boca_personaje(normal)
            self.originales[4]=boca_personaje(normal,abierta=True)
            self.originales[5]=boca_personaje(self.originales[5])
            self.originales[3]=boca_personaje(sentada,sentada=True)
            self.originales.append(boca_personaje(sentada,sentada=True,abierta=True))
        # La locomoción se representa únicamente con la descarga de tránsito.
        cajas=[im.getchannel('A').point(lambda a:255 if a>100 else 0).filter(ImageFilter.MinFilter(5)).getbbox() for im in self.pasos]
        cajas=[c for c in cajas if c]
        self.caja_pasos=(max(0,min(c[0] for c in cajas)-10),max(0,min(c[1] for c in cajas)-10),max(c[2] for c in cajas)+10,max(c[3] for c in cajas)+10) if cajas else None

    def redimensionar(self,escala):
        if self.fotos and self.escala==escala:return
        self.ancla=None;self.velocidad_caida=0.;self.colgadas={}
        self.escala=escala;self.ancho=round(210*escala);self.alto=round(240*escala)
        self.fotos=[];self.espejos=[];self.glitches=[];self.glitches_espejo=[];self.lienzos=[];self.halos={}
        for indice,im in enumerate(self.originales):
            if indice in (1,2):
                self.lienzos.append(self.lienzos[0]);self.fotos.append(self.fotos[0]);self.espejos.append(self.espejos[0])
                self.glitches.append(self.glitches[0]);self.glitches_espejo.append(self.glitches_espejo[0]);continue
            margen=max(8,round(8*escala))
            lienzo=Image.new('RGBA',(self.ancho,self.alto));copia=im.copy();copia.thumbnail((self.ancho,self.alto-margen),Image.Resampling.LANCZOS)
            lienzo.alpha_composite(copia,((self.ancho-copia.width)//2,self.alto-margen-copia.height))
            lienzo=limpiar_silueta(lienzo);self.lienzos.append(lienzo)
            self.fotos.append(ImageTk.PhotoImage(lienzo));self.espejos.append(ImageTk.PhotoImage(ImageOps.mirror(lienzo)))
            variantes=[glitch_silueta(lienzo,i) for i in range(2)]
            self.glitches.append([ImageTk.PhotoImage(v) for v in variantes])
            self.glitches_espejo.append([ImageTk.PhotoImage(ImageOps.mirror(v)) for v in variantes])
        self.pasos_tk=[];self.pasos_espejo=[]
        for im in self.pasos:
            lienzo=Image.new('RGBA',(self.ancho,self.alto));copia=im.crop(self.caja_pasos) if self.caja_pasos else im.copy();copia.thumbnail((self.ancho,self.alto),Image.Resampling.LANCZOS)
            lienzo.alpha_composite(copia,((self.ancho-copia.width)//2,self.alto-copia.height))
            self.pasos_tk.append(ImageTk.PhotoImage(lienzo));self.pasos_espejo.append(ImageTk.PhotoImage(ImageOps.mirror(lienzo)))

    def iniciar(self,x=None):
        self.libre=False;self.ancla=None;self.velocidad_caida=0.
        l,t,r,b=area_trabajo();self.x=max(l,min(r-self.ancho,r-self.ancho-25 if x is None else x))
        self.y=b-self.alto;self.soporte=None;self.salto=None;self.velocidad=0.;self.ultimo=time.monotonic();self.proxima_accion=self.ultimo+5

    def refrescar(self,ahora):
        if ahora>=self.revisar:self.ventanas=visibles();self.revisar=ahora+.7

    def borde_libre(self,ventana,x):
        y=ventana['rect'][1]
        for otra in self.ventanas:
            if otra['id']==ventana['id']:return True
            l,t,r,b=otra['rect']
            if l<=x<=r and t<=y<=b:return False
        return False

    def posar(self,x,y):
        self.libre=True;self.ancla=None;self.velocidad_caida=0.;self.gracia_fisica=0.
        l,t,r,b=area_trabajo()
        self.x=max(l,min(r-self.ancho,x));self.y=max(t,min(b-self.alto,y));self.salto=None;self.soporte=None
        self.refrescar(time.monotonic());l,t,r,b=area_trabajo()
        # Cerca de una barra superior, sentarse por la cadera, no por los pies.
        candidatos=[v for v in self.ventanas if v['rect'][0]<x+self.ancho*.5<v['rect'][2] and v['rect'][1]>self.alto*.64 and
                    min(abs(y+self.alto-v['rect'][1]),abs(y+self.alto*.64-v['rect'][1]))<65*self.escala and self.borde_libre(v,x+self.ancho*.5)]
        if candidatos and min(abs(self.y+self.alto*.64-v['rect'][1]) for v in candidatos)<8*self.escala:
            v=min(candidatos,key=lambda v:abs(y+self.alto*.64-v['rect'][1]))
            self.libre=False
            self.salto={'inicio':time.monotonic(),'x':self.x,'y':self.y,
                        'destino':(self.x,v['rect'][1]-self.alto*.64),'id':v['id'],
                        'izquierda':v['rect'][0],'lado':'libre'}
        self.proxima_accion=time.monotonic()+7

    def esquina(self,v,lado=None):
        l,t,r,b=area_trabajo();a,top,d,_=v['rect'];opciones=[]
        for nombre,x in (('izquierda',a-self.ancho*.45),('derecha',d-self.ancho*.55)):
            x=max(l,min(r-self.ancho,x))
            if a<=x+self.ancho*.5<=d and self.borde_libre(v,x+self.ancho*.5):
                solape=max(0,min(x+self.ancho,d)-max(x,a))
                opciones.append((solape,abs(x-self.x),nombre,x))
        if lado:
            elegida=next((o for o in opciones if o[2]==lado),None)
            if elegida:return elegida[3],top-self.alto*.64,lado
        if not opciones:return None
        _,_,nombre,x=min(opciones)
        return x,top-self.alto*.64,nombre

    def preparar_salto(self,v,ahora):
        self.libre=False;self.ancla=None;self.velocidad_caida=0.
        destino=self.esquina(v)
        if destino:
            self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':destino[:2],'id':v['id'],'izquierda':v['rect'][0],'lado':destino[2]}

    def elegir_viaje(self,ahora,evitar=None):
        l,t,r,b=area_trabajo();cx=self.x+self.ancho/2
        candidatos=[v for v in self.ventanas if v['id']!=evitar and t+self.alto*.64<v['rect'][1]<b-self.alto*.25
                    and v['rect'][2]-v['rect'][0]>self.ancho and self.esquina(v)]
        def distancia(v):
            a,y,d,_=v['rect'];return abs(cx-max(a,min(d,cx)))+abs(self.y+self.alto*.64-y)
        cercanas=[v for v in candidatos if distancia(v)<max(360*self.escala,(r-l)*.24)]
        self.proxima_accion=ahora+random.uniform(7,13)
        self.ancla=None;self.libre=False;self.velocidad_caida=0.
        if cercanas and random.random()<.75:self.preparar_salto(min(cercanas,key=distancia),ahora)
        elif candidatos and random.random()<.3:self.preparar_salto(random.choice(candidatos),ahora)
        else:
            x=random.uniform(l+8,max(l+8,r-self.ancho-8))
            y=random.uniform(t+12,max(t+12,b-self.alto))
            self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':(x,y),'id':0,'izquierda':x,'lado':None}

    def caer(self,ahora,dt,suelo):
        if ahora<self.gracia_fisica:self.estado='quieta';return
        if self.ancla:
            if ahora<self.ancla['hasta']:
                edad=ahora-self.ancla['inicio']
                self.y=self.ancla['cuerpo_y']+self.escala*(10*(1-math.exp(-edad*14))+3*math.exp(-edad*4)*math.sin(edad*18))
                self.estado='sujeta';return
            self.ancla=None;self.proxima_ancla=ahora+5
        if self.y<suelo-self.alto*.3 and ahora>=self.proxima_ancla and random.random()<dt*1.2:
            self.ancla={'x':self.x+self.ancho*(.77 if self.direccion<0 else .23),
                        'y':self.y+self.alto*.27,'hasta':ahora+random.uniform(3.5,6),
                        'inicio':ahora,'cuerpo_y':self.y}
            self.velocidad_caida=0.;self.estado='sujeta';return
        antes=self.y
        self.velocidad_caida=min(700*self.escala,self.velocidad_caida+900*self.escala*dt)
        self.y=min(suelo,self.y+self.velocidad_caida*dt);self.estado='cayendo' if self.y<suelo else 'quieta'
        # Puede alcanzar una barra real durante la caída y quedarse sentada.
        for v in self.ventanas:
            a,top,d,_=v['rect'];cx=self.x+self.ancho/2
            if (a<cx<d and antes+self.alto*.64<=top<=self.y+self.alto*.64
                    and self.borde_libre(v,cx)):
                self.y=top-self.alto*.64;self.soporte=v['id'];self.soporte_dx=self.x-a
                self.soporte_lado='libre';self.quieta_hasta=ahora+random.uniform(3,6)
                self.velocidad_caida=0.;self.estado='sentada';return

    def tick(self,pausa=False,pasear=True,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora;dt=min(.06,max(0,ahora-self.ultimo));self.ultimo=ahora
        self.refrescar(ahora);l,t,r,b=area_trabajo();suelo=b-self.alto
        self.x=max(l,min(r-self.ancho,self.x));self.y=max(t,min(suelo,self.y))
        if self.soporte:
            v=next((v for v in self.ventanas if v['id']==self.soporte),None)
            if v and self.soporte_lado=='libre':
                esquina=(max(l,min(r-self.ancho,v['rect'][0]+self.soporte_dx)),v['rect'][1]-self.alto*.64,'libre')
            else:esquina=self.esquina(v,self.soporte_lado) if v else None
            if v and esquina and v['rect'][1]>=t+self.alto*.64:
                if abs(esquina[0]-self.x)+abs(esquina[1]-self.y)>3:
                    self.soporte=None
                    self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':esquina[:2],
                                'id':v['id'],'izquierda':v['rect'][0],'lado':esquina[2]}
                    return
                self.x=esquina[0];self.soporte_dx=self.x-v['rect'][0];self.soporte_lado=esquina[2]
                self.y=v['rect'][1]-self.alto*.64;self.estado='sentada'
                if not pausa and pasear and ahora>=self.quieta_hasta:
                    self.soporte=None;self.elegir_viaje(ahora,evitar=v['id'])
                return
            self.soporte=None;self.gracia_fisica=0.;self.velocidad_caida=0.
        if pausa:self.velocidad*=math.exp(-dt*10);self.estado='quieta';return
        if self.salto:
            s=self.salto;u=min(1,(ahora-s['inicio'])/.85);avance=u*u*(3-2*u)
            self.x=s['x']+(s['destino'][0]-s['x'])*avance
            self.y=s['y']+(s['destino'][1]-s['y'])*avance
            self.estado='saltando'
            if u>=1:
                self.soporte=s['id'];self.soporte_dx=s['destino'][0]-s['izquierda'];self.soporte_lado=s.get('lado');self.salto=None;self.quieta_hasta=ahora+random.uniform(5,9)
                self.gracia_fisica=0.;self.ancla=None;self.velocidad_caida=0.
            return
        if not pasear:self.estado='quieta';return
        self.velocidad=0.;self.estado='quieta'
        if ahora>=self.proxima_accion:
            self.elegir_viaje(ahora);return
        if self.y<suelo:self.caer(ahora,dt,suelo)

    def dibujar(self,c,hablando=False,boca=False,glitch=True,halo='violeta'):
        c.delete('all')
        if not self.fotos:return
        ahora=time.monotonic()
        if self.ancla:
            ax=self.ancla['x']-self.x;ay=self.ancla['y']-self.y
            edad=max(0,ahora-self.ancla['inicio']);lado=-1 if self.direccion<0 else 1;s=self.escala
            golpe=max(0,1-edad/.20)
            def puntos(lista):return [v for x,y in lista for v in (ax+lado*x*s,ay+y*s)]
            for rama in (((0,0),(-10,-8),(-22,-7)),((0,0),(-5,12),(-15,21)),
                         ((0,0),(8,-11),(7,-23)),((0,0),(17,3),(23,12))):
                c.create_line(*puntos(rama),fill='#160c15',width=max(2,3*s),tags=('ancla_personaje','impacto_ancla'))
                c.create_line(*puntos(rama),fill='#b04a67',width=1,tags=('ancla_personaje','impacto_ancla'))
            c.create_polygon(*puntos([(-8,0),(0,-7),(9,1),(0,8)]),fill='#170d17',outline='#ef577c',width=2,tags='ancla_personaje')
            def hoja(lista):return [(x+golpe*18,y+golpe*20) for x,y in lista]
            c.create_polygon(*puntos(hoja([(-8,-11),(5,-3),(15,9),(9,14),(1,6)])),fill='#f60031',outline='#ff99b3',tags=('ancla_personaje','estaca_clavada'))
            c.create_polygon(*puntos(hoja([(-8,-11),(9,6),(9,14),(1,6)])),fill='#8e112d',outline='',tags='ancla_personaje')
            c.create_line(*puntos([(5,14),(17,4)]),fill='#ffb3c9',width=max(2,3*s),tags='ancla_personaje')
            c.create_line(*puntos([(11,10),(21,25)]),fill='#26101f',width=max(4,6*s),tags='ancla_personaje')
            c.create_line(*puntos([(11,10),(21,25)]),fill='#d4406a',width=max(1,2*s),tags='ancla_personaje')
            if edad<.36:
                for i in range(6):
                    radio=(8+edad*62)*s;a=i*math.pi/3+.2
                    c.create_line(ax+math.cos(a)*radio,ay+math.sin(a)*radio,ax+math.cos(a)*(radio+6*s),
                                  ay+math.sin(a)*(radio+6*s),fill='#ffdfed',width=2,tags=('ancla_personaje','chispa_ancla'))
        indice=(6 if hablando and boca else 3) if self.estado=='sentada' else 0
        if indice==0:
            if hablando and boca:indice=4
            elif ahora%5.3<.13:indice=5
        fotos=self.espejos if self.direccion<0 else self.fotos
        giro=round(-2+2*math.sin((ahora-self.ancla['inicio'])*3))*(1 if self.direccion>=0 else -1) if self.ancla else 0
        if self.ancla:
            agarre=(ax+lado*14*self.escala,ay+18*self.escala)
            clave_giro=(self.direccion<0,indice,giro,round(ay))
            if clave_giro not in self.colgadas:
                objetivo=(self.ancho-agarre[0] if self.direccion<0 else agarre[0],agarre[1])
                base=pose_sujeta(self.lienzos[indice],objetivo)
                if self.direccion<0:base=ImageOps.mirror(base)
                im=base.rotate(giro,Image.Resampling.NEAREST,center=agarre)
                self.colgadas[clave_giro]=(im,ImageTk.PhotoImage(im))
                if len(self.colgadas)>64:self.colgadas.pop(next(iter(self.colgadas)))
            cuerpo_colgado,foto_colgada=self.colgadas[clave_giro]
        if halo in COLORES_HALO:
            clave=(halo,self.direccion<0,indice,giro,round(ay) if self.ancla else None)
            if clave not in self.halos:
                im=ImageOps.mirror(self.lienzos[indice]) if self.direccion<0 else self.lienzos[indice]
                if self.ancla:im=cuerpo_colgado
                self.halos[clave]=ImageTk.PhotoImage(sombra_glitch(im,COLORES_HALO[halo]))
                if len(self.halos)>96:self.halos.pop(next(iter(self.halos)))
            desplazamiento=7 if glitch and ahora%4.7<.14 else 5
            c.create_image(self.ancho//2-desplazamiento,self.alto//2+2,image=self.halos[clave],tags='sombra_personaje')
        self.imagen=fotos[indice]
        if self.ancla:self.imagen=foto_colgada
        elif glitch and ahora%4.7<.14:
            variantes=self.glitches_espejo if self.direccion<0 else self.glitches
            self.imagen=variantes[indice][int(ahora*35)%2]
        c.create_image(self.ancho//2,self.alto//2,image=self.imagen,tags='personaje')
        if self.ancla:
            for i in range(3):
                c.create_line(*puntos([(11+i*2,13+i*3),(17+i*2,10+i*3)]),fill='#150b1a',width=max(3,4*s),tags=('ancla_personaje','agarre_personaje'))
                c.create_line(*puntos([(11+i*2,13+i*3),(17+i*2,10+i*3)]),fill='#ff477e',width=max(1,s),tags=('ancla_personaje','agarre_personaje'))

    def volver_al_borde(self,ahora):
        l,t,r,b=area_trabajo();x=l+8 if self.x<(l+r)/2 else r-self.ancho-8
        self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':(x,b-self.alto),'id':0,'izquierda':x,'lado':None}
