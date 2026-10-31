"""Secuencia visual de enlace. No bloquea el audio ni simula carga del modelo."""
import math
import random
import threading
import queue
import time
import os
from PIL import Image,ImageTk,ImageChops,ImageDraw,ImageFont
from pathlib import Path
from fuentes import FAMILIA

DURACION=8.2
VIAJE=.72

def suave(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

class TrasladoTeselas:
    """El propio sprite se desarma y recompone; no usa lenguas rojas externas."""
    def __init__(self,origen,destino,inicio,fin,tamanos_propios=False):
        self.inicio=inicio;self.fin=fin;self.piezas=[];self.offset_destinos=[]
        if not tamanos_propios:destino=destino.resize(origen.size,Image.Resampling.LANCZOS)
        w,h=origen.size
        dw,dh=destino.size
        for fila in range(8):
            for col in range(6):
                caja=(col*w//6,fila*h//8,(col+1)*w//6,(fila+1)*h//8)
                caja_destino=(col*dw//6,fila*dh//8,(col+1)*dw//6,(fila+1)*dh//8)
                a=origen.crop(caja);b=destino.crop(caja_destino)
                if not a.getbbox() and not b.getbbox():continue
                def rojo(im):
                    tinta=Image.new('RGBA',im.size,'#f60031')
                    tinta=Image.blend(im,tinta,.48);tinta.putalpha(im.getchannel('A'));return tinta
                fotos=[ImageTk.PhotoImage(im) for im in (a,rojo(a),rojo(b),b)]
                offset=((caja[0]+caja[2]-w)/2,(caja[1]+caja[3]-h)/2)
                self.piezas.append((fotos,offset,fila,col))
                self.offset_destinos.append(((caja_destino[0]+caja_destino[2]-dw)/2,(caja_destino[1]+caja_destino[3]-dh)/2))

    def dibujar(self,c,p):
        for (fotos,(ox,oy),fila,col),(dx,dy) in zip(self.piezas,self.offset_destinos):
            retraso=(fila%3)*.025+col*.009
            u=max(0,min(1,(p-retraso)/(1-retraso)));t=suave(u)
            arco=math.sin(math.pi*u)
            ox+=(dx-ox)*t;oy+=(dy-oy)*t
            x=self.inicio[0]+(self.fin[0]-self.inicio[0])*t+ox+(col-2.5)*7*arco
            y=self.inicio[1]+(self.fin[1]-self.inicio[1])*t+oy-35*arco+(fila-3.5)*5*arco
            indice=0 if u<.16 else (1 if u<.48 else (2 if u<.78 else 3))
            c.create_image(x,y,image=fotos[indice],tags='fragmento_viaje')

def geometria_morfosis(q,inicio,centro,fin,normal,grande,pequena):
    """Primero centrar y crecer; después encoger y solo al final desplazarse."""
    def mezclar(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
    if q<.42:
        return mezclar(inicio,centro,suave(q/.30)),mezclar(normal,grande,suave(q/.42))
    if q<.62:return centro,grande
    return mezclar(centro,fin,suave((q-.78)/.22)),mezclar(grande,pequena,suave((q-.62)/.38))

class Transformacion:
    def __init__(self,vista,saludo,personaje,inicio,fin,ancho,alto,escala=1,inversa=False,fotos=None,directa=False,panel=None):
        from PIL import ImageOps
        self.fotos=[];self.inicio=inicio;self.fin=fin;self.centro=(ancho/2,alto/2);self.inversa=inversa
        self.directa=directa;self.cantidad=31 if directa else 85
        self.cancelar=threading.Event();self.cola=queue.Queue(maxsize=8)
        if panel is None:
            panel=Image.new('RGBA',(1080,876));d=ImageDraw.Draw(panel)
            d.polygon([(24,60),(60,24),(1020,24),(1056,60),(1056,840),(1020,870),(24,870)],fill='#10090d',outline='#ed6684',width=6)
            panel.alpha_composite(vista.resize((960,630),Image.Resampling.LANCZOS),(60,165))
            fuente=Path(__file__).resolve().parent/'assets/fonts/ChakraPetch-Bold.ttf'
            if not fuente.exists():fuente=Path(__file__).resolve().parents[1]/'assets/fonts/ChakraPetch-Bold.ttf'
            from idiomas import ui,idioma_actual
            if idioma_actual()=='ja':fuente='YuGothB.ttc'
            try:fuente=ImageFont.truetype(str(fuente),38)
            except OSError:fuente=ImageFont.load_default()
            d.text((54,60),ui('CAPRI // ENLACE PERSONAL'),fill='#ffb0c3',font=fuente)
        self.normal=(360*escala,360*escala*panel.height/panel.width)
        self.grande=(min(ancho*.78,alto*.8*saludo.width/saludo.height),alto*.8)
        self.pequena=personaje.size
        self.preview=ImageTk.PhotoImage(personaje if inversa else panel.resize(tuple(round(v) for v in self.normal),Image.Resampling.LANCZOS))
        if fotos is not None:self.fotos=fotos;return
        # Pillow trabaja fuera de Tk; PhotoImage se crea en pequeños lotes en el hilo UI.
        self.worker=threading.Thread(target=Transformacion.preparar,args=(self.cola,self.cancelar,panel,saludo,personaje,self.cantidad,directa,inversa,
                                    inicio,self.centro,fin,self.normal,self.grande,self.pequena),daemon=True,name='CapriFrames')
        self.worker.start()

    def geometria(self,q):
        if self.directa:
            t=suave(q)
            return (tuple(a+(b-a)*t for a,b in zip(self.inicio,self.fin)),tuple(a+(b-a)*t for a,b in zip(self.normal,self.pequena)))
        return geometria_morfosis(q,self.inicio,self.centro,self.fin,self.normal,self.grande,self.pequena)

    @staticmethod
    def preparar(cola,cancelar,panel,saludo,personaje,cantidad,directa,inversa,inicio,centro,fin,normal,grande,pequena):
        from PIL import ImageOps
        # Separar color y máscara evita la conversión premultiplicada de RGBA
        # repetida en cada redimensionamiento grande durante la transición.
        fuentes={id(im):(im.convert('RGB'),im.getchannel('A')) for im in (panel,saludo,personaje)}
        anterior=None
        for i in range(cantidad):
            if cancelar.is_set():return
            # En retorno se preparan primero los estados próximos al personaje.
            indice=cantidad-1-i if inversa else i
            q=indice/(cantidad-1)
            if not directa and .42<q<.62 and anterior is not None and anterior/(cantidad-1)>.42:
                while not cancelar.is_set():
                    try:cola.put((indice,anterior),timeout=.05);break
                    except queue.Full:pass
                continue
            if directa:tam=tuple(a+(b-a)*suave(q) for a,b in zip(normal,pequena))
            else:_,tam=geometria_morfosis(q,inicio,centro,fin,normal,grande,pequena)
            caja=(max(1,round(tam[0])),max(1,round(tam[1])))
            def encajar(im):
                filtro=Image.Resampling.LANCZOS if q in (0,1) or .42<q<.62 else Image.Resampling.NEAREST
                rgb,alfa=fuentes[id(im)]
                rgb=ImageOps.contain(rgb,caja,filtro)
                mascara=alfa.resize(rgb.size,filtro)
                rgb.putalpha(mascara)
                fondo=Image.new('RGBA',caja);fondo.paste(rgb,((caja[0]-rgb.width)//2,(caja[1]-rgb.height)//2));return fondo
            if directa:a,b,mezcla=panel,personaje,suave(q)
            elif q<.42:a,b,mezcla=panel,saludo,suave((q-.14)/.28)
            else:a,b,mezcla=saludo,personaje,suave((q-.62)/.16)
            if mezcla<=0:im=encajar(a)
            elif mezcla>=1:im=encajar(b)
            else:
                a=encajar(a);b=encajar(b)
                mascara=Image.new('L',caja);p=ImageDraw.Draw(mascara)
                for y in range(0,caja[1],8):
                    borde=round((mezcla+math.sin(y*.17)*.07*math.sin(mezcla*math.pi))*caja[0])
                    if borde>0:p.rectangle((0,y,min(caja[0],borde),y+7),fill=255)
                im=Image.composite(b,a,mascara)
            im.putalpha(im.getchannel('A').point(lambda v:255 if v>=96 else 0))
            limite=im.getchannel('A').getbbox()
            offset=(0,0)
            if limite:
                offset=((limite[0]+limite[2]-im.width)/2,(limite[1]+limite[3]-im.height)/2)
                im=im.crop(limite)
            if os.name=='nt':
                # La ventana usa este color como transparencia. Enviar RGB
                # evita la conversión RGBA de Tk en cada fotograma grande.
                rgb=Image.new('RGB',im.size,'#010203');rgb.paste(im,mask=im.getchannel('A'));im=rgb
            dato=(im,offset);anterior=indice
            while not cancelar.is_set():
                try:cola.put((indice,dato),timeout=.05);break
                except queue.Full:pass

    def actualizar(self):
        inicio=time.perf_counter()
        for _ in range(2):
            try:indice,im=self.cola.get_nowait()
            except queue.Empty:break
            while len(self.fotos)<self.cantidad:self.fotos.append(None)
            if isinstance(im,int):self.fotos[indice]=self.fotos[im]
            else:
                im,offset=im;foto=ImageTk.PhotoImage(im);foto.offset=offset;self.fotos[indice]=foto
            if time.perf_counter()-inicio>.004:break

    def detener(self):self.cancelar.set()

    def dibujar(self,c,progreso):
        self.actualizar()
        q=1-progreso if self.inversa else progreso;q=max(0,min(1,q))
        indice=round(q*(self.cantidad-1))
        lista=[i for i,f in enumerate(self.fotos) if f is not None]
        elegido=min(lista,key=lambda i:abs(i-indice)) if lista else None
        # La posición y el tamaño pertenecen al MISMO estado preparado: nunca
        # llevar una foto grande atrasada hasta el destino del sprite pequeño.
        listo=elegido is not None and abs(elegido-indice)<=1
        centro,_=self.geometria(q if listo else (elegido/(self.cantidad-1) if elegido is not None else (1 if self.inversa else 0)))
        self.imagen=self.fotos[elegido] if elegido is not None else self.preview
        offset=getattr(self.imagen,'offset',(0,0))
        pos=(centro[0]+offset[0],centro[1]+offset[1])
        item=getattr(self,'item',None)
        if item is not None and c.type(item)=='image':
            c.coords(item,*pos)
            if getattr(self,'ultima_imagen',None) is not self.imagen:c.itemconfigure(item,image=self.imagen)
        else:self.item=c.create_image(*pos,image=self.imagen,tags='morfosis_capri')
        self.ultima_imagen=self.imagen

class Saludo:
    """Pose grande independiente del sprite de escritorio, preparada una vez."""
    def __init__(self,ruta,ancho,alto,solo_fuente=False):
        self.imagen=None;self.variantes=[];self.alto=alto*.72;self.vista=None;self.original=None
        try:
            from companera import limpiar_silueta,glitch_silueta
            with Image.open(ruta) as archivo:im=archivo.convert('RGBA')
            im.thumbnail((round(ancho*.80),round(alto*.80)),Image.Resampling.LANCZOS)
            im.putalpha(im.getchannel('A').point(lambda a:255 if a>=96 else 0));self.alto=im.height
            self.original=im
            copia=im.copy();copia.thumbnail((320,210),Image.Resampling.LANCZOS)
            self.vista=Image.new('RGBA',(320,210));self.vista.alpha_composite(copia,((320-copia.width)//2,(210-copia.height)//2))
            if not solo_fuente:
                self.imagen=ImageTk.PhotoImage(im)
                self.variantes=[ImageTk.PhotoImage(glitch_silueta(im,i)) for i in range(2)]
        except OSError:pass

    def dibujar(self,c,tiempo,x,y,glitch=True):
        imagen=self.imagen
        if imagen is not None:
            if glitch and (.12<tiempo<.23 or 1.24<tiempo<1.36):imagen=self.variantes[int(tiempo*35)%2]
            c.create_image(x,y+math.sin(tiempo*2)*3,image=imagen,tags='saludo_capri')
        if tiempo<.32 or 2.18<tiempo<2.4:
            for i in range(3):
                a=i*math.pi*2/3+tiempo*2;r=min(self.alto*.5,160+tiempo*40)
                descarga(c,[x+math.cos(a)*r*.7,y+math.sin(a)*r*.7,x+math.cos(a+.1)*r,y+math.sin(a+.1)*r,
                            x+math.cos(a)*r*1.2,y+math.sin(a)*r*1.2],grueso=.4)
        c.create_text(x,y+self.alto*.45,text='ENLACE ESTABLECIDO',fill='#78e6cb',font=(FAMILIA,16,'bold'),tags='saludo_texto')


class Fragmentos:
    """Bandas del avatar preparadas una vez; ninguna imagen se genera por frame."""
    def __init__(self,vista,escala):
        self.fotos=[];self.bandas=[]
        original=vista.convert('RGBA');r,g,b,_=original.split()
        mascara=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda v:0 if v<40 else min(255,(v-40)*5))
        mascara=ImageChops.multiply(mascara,original.getchannel('A'))
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
                tira.putalpha(tira.getchannel('A').point(lambda a:255 if a>=96 else 0))
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
    carga=suave((p-.43)/(VIAJE-.43))
    for lado in (-1,1):
        x=180+lado*(100+40*carga);y=130+lado*35
        descarga(c,[x-lado*18,y-24,x,y-8,x-lado*5,y+4,x+lado*28,y+35],grueso=.25+.25*carga)
    for i in range(3):
        y=80+i*65;avance=suave((carga-i*.12)/.65)
        if avance>0:c.create_line(28,y,28+300*avance,y,fill='#ff3864',width=1,tags='carga_enlace')


def romper_carcasa(c,p):
    """El marco se cuartea en su sitio y se consume antes de cambiar de ventana."""
    q=max(0,min(1,(p-.39)/.17))
    if q<=0:
        c.create_polygon(13,11,343,11,352,20,352,280,342,290,8,290,8,20,
                         fill='#10090d',outline='#ed6684')
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
                             fill='#10090d' if rotura<.7 else '#a70b32',outline='',tags='carcasa_rota')
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
    if imagen is not None and p>.06:
        if p>.43 and fragmentos:
            disolver=min(1,(p-.43)/(VIAJE-.43))
            fragmentos.dibujar(c,(180,153),disolver*.5,disolver,p)
        else:c.create_image(180,153,image=imagen)
        apertura=suave((p-.06)/.28);margen=(1-apertura)*105
        if p<=.39:
            c.create_rectangle(19,47,341,47+margen,fill='#10090d',outline='')
            c.create_rectangle(19,257-margen,341,258,fill='#10090d',outline='')
    if p<.43:
        for x,y,lado,vertical in ((25,52,1,1),(335,52,-1,1),(25,253,1,-1),(335,253,-1,-1)):
            c.create_line(x,y+vertical*14,x,y,x+lado*20,y,fill='#ff718f',width=2,tags='revelado_intro')
        if .06<p<.34:
            y=47+210*suave((p-.06)/.28)
            c.create_line(25,y,335,y,fill='#ffb1c5',width=2,tags='revelado_intro')
    titulo='CAPRI'
    if p<.46:
        c.create_text(180,29,text=titulo,fill='#ffb0c3',font=(FAMILIA,round(22*escala),'bold'))
        c.create_text(180,272,text='CONECTANDO',fill='#ff8ca8',font=(FAMILIA,max(8,round(9*escala)),'bold'))
    if p>.43:dibujar_carga(c,p)
    if p<.43:
        longitud=300*p;c.create_line(30,285,30+longitud,285,fill='#ec3c62',width=2)
    if .12<p<.48 or .7<p<.77:
        for i in range(3):
            y=65+(int(p*650)+i*39)%170
            c.create_line(25+i*12,y,330-i*8,y,fill='#ff819f' if i%2 else '#ec3c62',width=1)
