"""Personaje independiente: paseo, salto y apoyo sobre ventanas visibles."""
import math
import random
import time
from PIL import Image,ImageTk,ImageOps,ImageFilter
from ventanas import area_trabajo,visibles


class Companera:
    def __init__(self,ruta):
        self.originales=[];self.fotos=[];self.espejos=[];self.escala=1
        self.x=0.;self.y=0.;self.direccion=-1;self.soporte=None;self.salto=None
        self.ventanas=[];self.revisar=0;self.ultimo=time.monotonic();self.proxima_accion=self.ultimo+7
        self.estado='quieta';self.quieta_hasta=0
        self.pasos=[];self.pasos_tk=[];self.pasos_espejo=[];self.fase_paso=0.;self.velocidad=0.;self.soporte_lado=None
        try:
            with Image.open(ruta) as atlas:
                w,h=atlas.size
                self.originales=[atlas.crop((col*w//3+round(w/3*.176),fila*h//2,col*w//3+round(w/3*.918),(fila+1)*h//2)).convert('RGBA')
                                 for fila in range(2) for col in range(3)]
        except OSError:pass
        try:
            with Image.open(ruta.with_name('capri-caminar-v1.png')) as atlas:
                w,h=atlas.size
                self.pasos=[atlas.crop((col*w//4,fila*h//2,(col+1)*w//4,(fila+1)*h//2)).convert('RGBA') for fila in range(2) for col in range(4)]
        except OSError:pass
        cajas=[im.getchannel('A').point(lambda a:255 if a>100 else 0).filter(ImageFilter.MinFilter(5)).getbbox() for im in self.pasos]
        cajas=[c for c in cajas if c]
        self.caja_pasos=(max(0,min(c[0] for c in cajas)-10),max(0,min(c[1] for c in cajas)-10),max(c[2] for c in cajas)+10,max(c[3] for c in cajas)+10) if cajas else None

    def redimensionar(self,escala):
        if self.fotos and self.escala==escala:return
        self.escala=escala;self.ancho=round(210*escala);self.alto=round(240*escala)
        self.fotos=[];self.espejos=[]
        for im in self.originales:
            lienzo=Image.new('RGBA',(self.ancho,self.alto));copia=im.copy();copia.thumbnail((self.ancho,self.alto),Image.Resampling.LANCZOS)
            lienzo.alpha_composite(copia,((self.ancho-copia.width)//2,self.alto-copia.height))
            self.fotos.append(ImageTk.PhotoImage(lienzo));self.espejos.append(ImageTk.PhotoImage(ImageOps.mirror(lienzo)))
        self.pasos_tk=[];self.pasos_espejo=[]
        for im in self.pasos:
            lienzo=Image.new('RGBA',(self.ancho,self.alto));copia=im.crop(self.caja_pasos) if self.caja_pasos else im.copy();copia.thumbnail((self.ancho,self.alto),Image.Resampling.LANCZOS)
            lienzo.alpha_composite(copia,((self.ancho-copia.width)//2,self.alto-copia.height))
            self.pasos_tk.append(ImageTk.PhotoImage(lienzo));self.pasos_espejo.append(ImageTk.PhotoImage(ImageOps.mirror(lienzo)))

    def iniciar(self,x=None):
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
        self.x=x;self.y=y;self.salto=None;self.soporte=None
        self.refrescar(time.monotonic());l,t,r,b=area_trabajo()
        # Cerca de una barra superior, sentarse por la cadera, no por los pies.
        candidatos=[v for v in self.ventanas if v['rect'][0]<x+self.ancho*.5<v['rect'][2] and v['rect'][1]>self.alto*.64 and
                    min(abs(y+self.alto-v['rect'][1]),abs(y+self.alto*.64-v['rect'][1]))<65*self.escala and self.borde_libre(v,x+self.ancho*.5)]
        if candidatos:
            v=min(candidatos,key=lambda v:abs(y+self.alto*.64-v['rect'][1]))
            self.preparar_salto(v,time.monotonic())
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
        destino=self.esquina(v)
        if destino:
            self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':destino[:2],'id':v['id'],'izquierda':v['rect'][0],'lado':destino[2]}

    def tick(self,pausa=False,pasear=True,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora;dt=min(.06,max(0,ahora-self.ultimo));self.ultimo=ahora
        self.refrescar(ahora);l,t,r,b=area_trabajo();suelo=b-self.alto
        if self.soporte:
            v=next((v for v in self.ventanas if v['id']==self.soporte),None)
            esquina=self.esquina(v,self.soporte_lado) if v else None
            if v and esquina and v['rect'][1]>=t+self.alto*.64:
                self.x=esquina[0];self.soporte_dx=self.x-v['rect'][0];self.soporte_lado=esquina[2]
                self.y=v['rect'][1]-self.alto*.64;self.estado='sentada'
                if not pausa and pasear and ahora>=self.quieta_hasta:
                    self.soporte=None;self.volver_al_borde(ahora);self.proxima_accion=ahora+8
                return
            self.soporte=None;self.volver_al_borde(ahora);return
        if pausa:self.velocidad*=math.exp(-dt*10);self.estado='quieta';return
        if self.salto:
            s=self.salto;u=min(1,(ahora-s['inicio'])/.85);avance=u*u*(3-2*u)
            self.x=s['x']+(s['destino'][0]-s['x'])*avance
            self.y=s['y']+(s['destino'][1]-s['y'])*avance
            self.estado='saltando'
            if u>=1:
                self.soporte=s['id'];self.soporte_dx=s['destino'][0]-s['izquierda'];self.soporte_lado=s.get('lado');self.salto=None;self.quieta_hasta=ahora+random.uniform(5,9)
            return
        if self.y<suelo-1:self.y=min(suelo,self.y+360*self.escala*dt);self.estado='cayendo';return
        self.y=suelo
        if not pasear:self.estado='quieta';return
        objetivo=self.direccion*45*self.escala
        self.velocidad+=(objetivo-self.velocidad)*(1-math.exp(-dt*8))
        desplazamiento=self.velocidad*dt;self.x+=desplazamiento
        self.fase_paso=(self.fase_paso+abs(desplazamiento)/(44*self.escala))%1
        if self.x<=l or self.x>=r-self.ancho:self.direccion*=-1
        self.x=max(l,min(r-self.ancho,self.x));self.estado='caminando'
        if ahora>=self.proxima_accion:
            self.proxima_accion=ahora+random.uniform(8,15)
            candidatos=[v for v in self.ventanas if t+self.alto*.64<v['rect'][1]<b-self.alto*.25 and v['rect'][2]-v['rect'][0]>self.ancho and self.borde_libre(v,(v['rect'][0]+v['rect'][2])/2)]
            if candidatos:
                self.preparar_salto(random.choice(candidatos),ahora)

    def dibujar(self,c,hablando=False,boca=False):
        c.delete('all')
        if not self.fotos:return
        ahora=time.monotonic()
        indice=3 if self.estado=='sentada' else (1+int(ahora*5)%2 if self.estado in ('caminando','saltando') else 0)
        if indice==0:
            if hablando and boca:indice=4
            elif ahora%5.3<.13:indice=5
        fotos=self.espejos if self.direccion<0 else self.fotos
        if self.estado=='caminando' and self.pasos_tk:
            pasos=self.pasos_espejo if self.direccion<0 else self.pasos_tk
            self.imagen=pasos[int(self.fase_paso*len(pasos))%len(pasos)]
        else:self.imagen=fotos[indice]
        rebote=abs(math.sin(self.fase_paso*math.pi*2))*1.3*self.escala if self.estado=='caminando' else 0
        c.create_image(self.ancho//2,self.alto//2-rebote,image=self.imagen,tags='personaje')

    def volver_al_borde(self,ahora):
        l,t,r,b=area_trabajo();x=l+8 if self.x<(l+r)/2 else r-self.ancho-8
        self.salto={'inicio':ahora,'x':self.x,'y':self.y,'destino':(x,b-self.alto),'id':0,'izquierda':x,'lado':None}
