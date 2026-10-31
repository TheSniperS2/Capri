"""Intro muda: ilustración vectorial con mirada, párpados, sonrisa y gesto propios."""
import json,math
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageTk,ImageDraw
from fuentes import FAMILIA
from idiomas import ui
from intro import suave,DURACION
from tema_ui import color

SALIDA=5.2
PASOS_MARCO=120
SALUDO='¡Hola!'
ARTE='capri-intro-vector-v4.json'
TRANSPARENTE='#010203'


def limitar(v):return max(0.,min(1.,v))


class LienzoAnimado:
    """Reutiliza primitivas Tk en lugar de destruir y reconstruir toda la escena."""
    def __init__(self,canvas):
        self.canvas=canvas;self.items={};self.opciones={};self.ocultos=set();self.usados=set();self.contadores={}

    def delete(self,tag):
        if self.items and not self.canvas.type(next(iter(self.items.values()))):
            self.items.clear();self.opciones.clear();self.ocultos.clear()
        self.usados.clear();self.contadores.clear()

    def crear(self,tipo,p,kw):
        tag=str(kw.get('tags',''));grupo=(tipo,tag);n=self.contadores.get(grupo,0);self.contadores[grupo]=n+1
        clave=(tipo,tag,n);self.usados.add(clave)
        if clave not in self.items:
            item=getattr(self.canvas,tipo)(*p,**kw);self.items[clave]=item;self.opciones[clave]=dict(kw)
        else:
            item=self.items[clave];self.canvas.coords(item,*p)
            cambios={k:v for k,v in kw.items() if self.opciones[clave].get(k)!=v}
            if clave in self.ocultos:cambios.update(state='normal',tags=kw.get('tags',()));self.ocultos.remove(clave)
            if cambios:self.canvas.itemconfigure(item,**cambios)
            self.opciones[clave]=dict(kw)
        # La creación inicial fija el orden; la transición necesita el marco por encima.
        if tipo=='create_image':self.canvas.tag_raise(item)
        return item

    def create_polygon(self,*p,**kw):return self.crear('create_polygon',p,kw)
    def create_line(self,*p,**kw):return self.crear('create_line',p,kw)
    def create_image(self,*p,**kw):return self.crear('create_image',p,kw)
    def create_text(self,*p,**kw):return self.crear('create_text',p,kw)
    def terminar(self):
        for clave in self.items.keys()-self.usados-self.ocultos:
            self.canvas.itemconfigure(self.items[clave],state='hidden',tags=());self.ocultos.add(clave)


class Bienvenida:
    def __init__(self,estados,destino,fin,ancho,alto,saludo=None,pantalla=True):
        self.w,self.h=ancho,alto;self.fin=fin;self.saludo=saludo or ui(SALUDO)
        self.centro=(ancho/2,alto/2);self.salida_desde=None;self.retenida=False
        self.f=max(.55,alto/1080)
        self.pantalla=pantalla;self.destino_tamano=destino.size;self.recorte=None
        self.lienzo=None
        ruta=next((r for r in (Path(__file__).parent/'assets'/ARTE,Path(__file__).parents[1]/'assets'/ARTE) if r.exists()),None)
        self.formas=json.loads(ruta.read_text(encoding='utf8'))['formas'] if ruta else []
        self.pesos={(x,y):self.peso(x,y) for _,p in self.formas for x,y in zip(p[::2],p[1::2])}
        self.preparar_geometria()
        self.llegada=[]
        for i in range(1 if pantalla else 21):
            zoom=1 if pantalla else 1+.28*(1-i/20)
            im=destino.resize((max(1,round(destino.width*zoom)),max(1,round(destino.height*zoom))),Image.Resampling.LANCZOS)
            self.llegada.append(ImageTk.PhotoImage(im))
        self.marcos={};self.destino=destino.copy();self.apertura_salida=0
        self.aparicion_t=None;self.numero_forma=0
        self.pendientes={};self.worker=ThreadPoolExecutor(max_workers=1,thread_name_prefix="CapriIntro") if pantalla else None
        if pantalla:self.pedir_marcos(0)

    def imagen_marco(self,indice):
        u=.32+.68*indice/PASOS_MARCO
        _,_,_,_,factor=self.geometria_salida(u)
        return Bienvenida.raster_marco(self.destino,indice,factor)

    @staticmethod
    def raster_marco(destino,indice,factor):
        # Solo datos Pillow: el trabajador nunca retiene objetos Tk ni la animación.
        u=.32+.68*indice/PASOS_MARCO
        im=destino.copy();d=ImageDraw.Draw(im)
        # El marco se construye alrededor de la cara; nunca contiene una segunda Capri.
        limite=round(im.height*suave((u-.32)/.38))
        if limite<im.height:d.rectangle((0,limite,im.width,im.height),fill=(0,0,0,0))
        escala=im.width/360;izq,arr,der,ab=(round(v*escala) for v in (20,55,340,265))
        foto=suave((u-.78)/.22)
        if foto<1:d.rectangle((izq+round((der-izq)*foto),arr,der-1,ab-1),fill=(0,0,0,0))
        tam=(max(1,round(im.width*factor)),max(1,round(im.height*factor)))
        if tam!=im.size:im=im.resize(tam,Image.Resampling.BILINEAR)
        if indice<PASOS_MARCO:im.putalpha(im.getchannel('A').point(lambda v:255 if v>=128 else 0))
        return im

    def pedir_marcos(self,indice):
        for viejo in list(self.pendientes):
            if viejo<indice:
                self.pendientes.pop(viejo).cancel()
        for i in range(indice,min(PASOS_MARCO+1,indice+5)):
            if i not in self.pendientes and i not in self.marcos:
                factor=self.geometria_salida(.32+.68*i/PASOS_MARCO)[4]
                self.pendientes[i]=self.worker.submit(Bienvenida.raster_marco,self.destino,i,factor)

    def marco(self,indice):
        self.pedir_marcos(indice)
        if indice not in self.marcos:
            futuro=self.pendientes.get(indice)
            if futuro is not None and futuro.done():
                im=futuro.result();self.pendientes.pop(indice)
            elif self.marcos and indice<PASOS_MARCO:
                # No detener el movimiento si el procesador a?n prepara un marco.
                return self.marcos[max(self.marcos)]
            else:im=self.imagen_marco(indice)
            self.marcos[indice]=ImageTk.PhotoImage(im)
            while len(self.marcos)>4:del self.marcos[next(iter(self.marcos))]
        return self.marcos[indice]

    def detener(self):
        if self.worker is not None:self.worker.shutdown(wait=False,cancel_futures=True)
        self.pendientes.clear()

    def tiempo(self,t,esperando_voz=False):
        # La bienvenida no depende de un sintetizador ni de eventos de audio.
        return t

    @staticmethod
    def peso(x,y):
        cabeza=limitar((470-y)/90)*limitar((x-260)/100)*limitar((930-x)/150)
        mano=limitar((x-815)/110)*limitar((650-y)/170) if y>350 else 0
        return cabeza,mano

    def punto(self,x,y,t,zoom,dx=0,dy=0):
        # Deformación continua compartida por el dibujo y los rasgos de la cara.
        pesos=self.pesos.get((x,y))
        cabeza,mano=pesos if pesos is not None else self.peso(x,y)
        co,si,cm,sm,s,ox,oy,respirar=self.rig
        px,py=x-564,y-410
        x+=(px*(co-1)-py*si)*cabeza;y+=(px*si+py*(co-1))*cabeza
        if mano:
            px,py=x-860,y-570
            x+=(px*(cm-1)-py*sm)*mano;y+=(px*sm+py*(cm-1))*mano
        y+=respirar*(1-cabeza)
        return (ox+(x-559)*s,oy+(y-275)*s)

    def poligono(self,c,puntos,tono,t,z,dx,dy,tag='intro_retrato'):
        coords=[]
        for x,y in zip(puntos[::2],puntos[1::2]):coords.extend(self.punto(x,y,t,z,dx,dy))
        self.pintar_poligono(c,coords,tono,tag)

    def pintar_poligono(self,c,coords,tono,tag='intro_retrato'):
        if self.recorte:coords=recortar(coords,self.recorte)
        if len(coords)<6:return
        instante=self.aparicion_t;n=self.numero_forma;self.numero_forma+=1
        if instante is not None:
            if instante<.060:
                # Restos de señal en el lugar exacto donde se materializa la silueta.
                if (n*7)%19>1:return
                xs=coords[::2];ys=coords[1::2];cx=sum(xs)/len(xs);cy=sum(ys)/len(ys)
                k=.24+.18*instante/.060;salto=(1-instante/.060)*18*self.f
                coords=[v for x,y in zip(xs,ys) for v in (cx+(x-cx)*k+salto*(-1 if n%2 else 1),cy+(y-cy)*k)]
                c.create_polygon(*coords,fill=('#49f6ff','#ff1761','#ae62ff','#fff7ed')[n%4],outline='',
                                 tags=(tag,'intro_aparicion_fragmentos'))
                return
            if instante<.110:
                c.create_polygon(*coords,fill='#fff5e5',outline='',tags=(tag,'intro_aparicion_destello'))
                return
            intensidad=(1-suave((instante-.110)/.230))
            if intensidad>0 and n%5==0:
                # Dos ecos de color, calculados sobre la geometría ya transformada.
                distancia=18*self.f*intensidad
                for direccion,tinta in ((-1,'#20eaff'),(1,'#ff145b')):
                    eco=[v+direccion*distancia if i%2==0 else v for i,v in enumerate(coords)]
                    c.create_polygon(*eco,fill=tinta,outline='',tags='intro_aparicion_rgb')
        c.create_polygon(*coords,fill=tono,outline='',tags=tag)

    def preparar_geometria(self):
        """Vértices y pesos estáticos; toda la ilustración se mueve en un solo lote."""
        puntos=[];self.tramos=[]
        for tono,p in self.formas:
            inicio=len(puntos);puntos.extend(zip(p[::2],p[1::2]));self.tramos.append((tono,inicio,len(puntos)))
        self.vertices=np.asarray(puntos,dtype=np.float64).reshape((-1,2))
        pesos=np.asarray([self.peso(x,y) for x,y in puntos],dtype=np.float64).reshape((-1,2))
        self.peso_cabeza=pesos[:,0];self.peso_mano=pesos[:,1]

    def proyectar_geometria(self):
        co,si,cm,sm,s,ox,oy,respirar=self.rig
        x,y=self.vertices[:,0],self.vertices[:,1];px=x-564;py=y-410
        x=x+(px*(co-1)-py*si)*self.peso_cabeza
        y=y+(px*si+py*(co-1))*self.peso_cabeza
        px=x-860;py=y-570
        x=x+(px*(cm-1)-py*sm)*self.peso_mano
        y=y+(px*sm+py*(cm-1))*self.peso_mano+respirar*(1-self.peso_cabeza)
        return np.column_stack((ox+(x-559)*s,oy+(y-275)*s))

    def ovalo(self,c,x,y,rx,ry,tono,t,z,dx,dy,tag):
        # Polígonos de 40 segmentos: círculos suaves también al inclinar la cara.
        p=[]
        for i in range(40):
            a=i*math.tau/40;p.extend((x+rx*math.cos(a),y+ry*math.sin(a)))
        self.poligono(c,p,tono,t,z,dx,dy,tag)

    def rostro(self,c,t,z,dx,dy):
        mirar_x=math.sin(t*1.9)*3.5;mirar_y=math.sin(t*1.1)*2
        # Parpadeos breves y sonrisa sostenida al principio y al despedirse.
        cerrado=suave((t-.18)/.10)*(1-suave((t-.55)/.25))
        for inicio in (1.86,3.28):
            cerrado=max(cerrado,max(0,1-abs(t-inicio)/.115))
        cerrado=max(cerrado,suave((t-4.35)/.40))*(1-self.apertura_salida)
        for x,y,r in ((495,332,34),(626,293,40)):
            self.ovalo(c,x,y,r+3,r+3,'#0d0913',t,z,dx,dy,'intro_ojos')
            abierto=1-cerrado
            if abierto>.12:
                self.ovalo(c,x,y,r-1,(r-1)*abierto,'#08eb37',t,z,dx,dy,'intro_ojos')
                self.ovalo(c,x,y,r-3,(r-3)*abierto,'#0d0913',t,z,dx,dy,'intro_ojos')
                self.ovalo(c,x+mirar_x,y+mirar_y,r*.72,r*.72*abierto,'#2fb9f6',t,z,dx,dy,'intro_ojos')
                self.ovalo(c,x+mirar_x,y+mirar_y,r*.33,r*.33*abierto,'#effcff',t,z,dx,dy,'intro_pupilas')
            else:
                p=[]
                for i in range(17):
                    v=i/16;p.extend(self.punto(x-r+2*r*v,y-9*math.sin(math.pi*v)+4,t,z,dx,dy))
                c.create_line(*p,fill='#09ef38',width=max(2,self.w*z/1086*5),smooth=True,tags='intro_ojos')
        # Gesto silencioso: pasa de una sonrisa ladeada a una sonrisa abierta.
        self.poligono(c,[510,379,628,337,614,396,600,429,545,410],'#0d0913',t,z,dx,dy,'intro_boca')
        abrir=.28+.72*suave((t-.90)/.65)
        abrir-=.16*math.sin(t*2.5)**2
        self.poligono(c,[519,381,535,373,543,381,555,365,568,371,582,356,591,362,621,344,
                        609,377+14*abrir,596,380+39*abrir,553,388+18*abrir],
                      '#f1f7ff',t,z,dx,dy,'intro_boca')

    def retrato(self,c,t,z,dx=0,dy=0):
        self.numero_forma=0
        giro=math.sin(t*1.65)*.022+.025*math.sin(t*.75);mano=.055*math.sin(t*3.8)
        self.rig=(math.cos(giro),math.sin(giro),math.cos(mano),math.sin(mano),
                  self.w*z/1086,self.w*.5+dx,self.h*.42+dy,math.sin(t*2.1)*3)
        puntos=self.proyectar_geometria()
        for tono,inicio,fin in self.tramos:
            tono={'#ff598e':'#ff256d','#b10061':'#d00051'}.get(tono,tono)
            self.pintar_poligono(c,puntos[inicio:fin].ravel().tolist(),tono)
        self.rostro(c,t,z,dx,dy)

    def cartel(self,c,t):
        q=suave((t-.7)/.22)*(1-suave((t-4.65)/.25))
        if q<=0:return
        x=self.w*.81+(1-q)*60*self.f;y=self.h*.16+math.sin(t*2)*5*self.f
        w=130*self.f;h=76*self.f
        c.create_polygon(x+10,y+9,x+w+14,y+9,x+w+4,y+h+10,x,y+h+10,
                         fill='#5a1cc7',outline='',tags='intro_saludo')
        c.create_polygon(x,y,x+w,y,x+w-10,y+h,x-10,y+h,
                         fill='#ff0054',outline='',tags='intro_saludo')
        c.create_text(x+w/2-4,y+h/2,text=self.saludo,fill='#ffffff',
                      font=(FAMILIA,-max(20,round(37*self.f)),'bold'),tags='intro_saludo')

    def dibujar(self,c,t,hablando=False,boca=False,bandas=()):
        if hasattr(c,'tk'):
            if self.lienzo is None or self.lienzo.canvas is not c:self.lienzo=LienzoAnimado(c)
            c=self.lienzo
        c.delete('all')
        self.recorte=None;self.apertura_salida=0;self.aparicion_t=t if 0<=t<.34 else None
        if t<SALIDA:
            z=self.encuadre(t)
            # Materialización breve en su posición definitiva, sin recorrido vertical.
            self.retrato(c,t,z)
            self.cartel(c,t)
            if isinstance(c,LienzoAnimado):c.terminar()
            return
        u=limitar((t-SALIDA)/(DURACION-SALIDA));q=suave(max(0,(u-.08)/.92))
        if self.pantalla:
            self.apertura_salida=suave(u/.22)
            z,ox,oy,caja,factor=self.geometria_salida(u)
            recorte=suave((u-.22)/.40)
            # La silueta se recoge dentro del visor mientras el marco toma forma.
            exterior=(-self.w,-self.h,self.w*2,self.h*2)
            self.recorte=tuple(a+(b-a)*recorte for a,b in zip(exterior,caja)) if recorte else None
            self.retrato(c,SALIDA,z,ox-self.w*.5,oy-self.h*.42)
            if u>=.32:
                indice=min(PASOS_MARCO,round((u-.32)/.68*PASOS_MARCO))
                escala=self.destino_tamano[0]/360
                cx=(caja[0]+caja[2])/2
                cy=(caja[1]+caja[3])/2+(23-14*escala)*factor
                c.create_image(cx,cy,image=self.marco(indice),tags='intro_llegada')
            self.recorte=None
            if isinstance(c,LienzoAnimado):c.terminar()
            return
        if u<.20:
            salida=suave(u/.20)
            self.retrato(c,SALIDA,1.25,self.w*.12*salida,self.h*salida)
        i=min(len(self.llegada)-1,round(q*(len(self.llegada)-1)))
        cx,cy=self.centro;x=cx+(self.fin[0]-cx)*q;y=cy+(self.fin[1]-cy)*q-40*math.sin(math.pi*q)
        c.create_image(x,y,image=self.llegada[i],tags='intro_llegada')
        if q<.85:
            for k in (1,2,3):
                p=max(0,q-k*.025);tx=cx+(self.fin[0]-cx)*p;ty=cy+(self.fin[1]-cy)*p-40*math.sin(math.pi*p)
                c.create_line(tx-10,ty,tx+10,ty,fill=color('#8e304a'),width=2,tags='intro_estela')
        if isinstance(c,LienzoAnimado):c.terminar()

    @staticmethod
    def encuadre(t):return 1.04+.10*suave((t-1)/1.2)+.005*math.sin(t*1.9)+.085*math.exp(-max(0,t)/.065)

    def geometria_salida(self,u):
        q=suave(u);escala=self.destino_tamano[0]/360
        s0=self.w*self.encuadre(SALIDA)/1086;s1=320*escala/600
        s=s0+(s1-s0)*q
        # Mantiene un único centro de proyección desde el primer plano hasta la cámara.
        ox=self.w*.5+(self.fin[0]-self.w*.5)*suave((u-.12)/.88)
        fin_y=self.fin[1]-(23-14*escala)-55*s1
        oy=self.h*.42+(fin_y-self.h*.42)*suave((u-.12)/.88)
        factor=s/s1;cx=ox;cy=oy+55*s
        caja=(cx-160*escala*factor,cy-105*escala*factor,cx+160*escala*factor,cy+105*escala*factor)
        return s*1086/self.w,ox,oy,caja,factor


def recortar(coords,caja):
    """Recorte de polígonos contra la cámara que se va formando (Sutherland-Hodgman)."""
    xs=coords[::2];ys=coords[1::2]
    if min(xs)>=caja[0] and max(xs)<=caja[2] and min(ys)>=caja[1] and max(ys)<=caja[3]:return coords
    if max(xs)<caja[0] or min(xs)>caja[2] or max(ys)<caja[1] or min(ys)>caja[3]:return []
    puntos=list(zip(xs,ys))
    for eje,limite,signo in ((0,caja[0],1),(0,caja[2],-1),(1,caja[1],1),(1,caja[3],-1)):
        if not puntos:break
        salida=[];anterior=puntos[-1];d0=(anterior[eje]-limite)*signo
        for actual in puntos:
            d1=(actual[eje]-limite)*signo
            if (d1>=0)!=(d0>=0):
                q=d0/(d0-d1)
                salida.append(tuple(a+(b-a)*q for a,b in zip(anterior,actual)))
            if d1>=0:salida.append(actual)
            anterior=actual;d0=d1
        puntos=salida
    return [v for p in puntos for v in p]
