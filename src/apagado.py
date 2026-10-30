"""Interferencia y cierre CRT exclusivos del apagado confirmado del computador."""
from pathlib import Path
import math
import random
import time
import tkinter as tk
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageTk,ImageFilter,ImageChops
from idiomas import ui

DURACION=6.6


class RendererApagado:
    def __init__(self,tamano,retrato=None,idioma='es'):
        self.w,self.h=tamano;self.idioma=idioma;self.fuentes={}
        rng=random.Random(7341)
        self.ruido=[]
        for _ in range(12):
            gris=Image.frombytes('L',(320,180),rng.randbytes(320*180))
            self.ruido.append(ImageOps.colorize(gris,'#110811','#a73a59').resize(tamano,Image.Resampling.NEAREST))
        self.retrato=None
        if retrato is not None:
            im=retrato.convert('RGBA').copy();im.thumbnail((self.w*.46,self.h*.72),Image.Resampling.LANCZOS)
            mascara=Image.new('L',im.size,0)
            ImageDraw.Draw(mascara).ellipse((im.width*.1,im.height*.02,im.width*.9,im.height*.98),fill=210)
            mascara=mascara.filter(ImageFilter.GaussianBlur(max(2,im.width*.1)))
            im.putalpha(ImageChops.multiply(im.getchannel('A'),mascara))
            self.retrato=im
            self.retrato_rojo=ImageOps.colorize(ImageOps.grayscale(im),'#13050c','#ff315a').convert('RGBA')
            self.retrato_rojo.putalpha(im.getchannel('A'))

    def fuente(self,size):
        size=max(12,round(size*self.w/1440))
        if size not in self.fuentes:
            ruta=Path(__file__).parent/'assets/fonts/ChakraPetch-Bold.ttf'
            if not ruta.exists():ruta=Path(__file__).parent.parent/'assets/fonts/ChakraPetch-Bold.ttf'
            if self.idioma=='ja' and Path('C:/Windows/Fonts/YuGothB.ttc').exists():ruta=Path('C:/Windows/Fonts/YuGothB.ttc')
            try:self.fuentes[size]=ImageFont.truetype(str(ruta),size)
            except OSError:self.fuentes[size]=ImageFont.load_default(size=size)
        return self.fuentes[size]

    def fotograma(self,t):
        w,h=self.w,self.h
        if t>=DURACION:return Image.new('RGB',(w,h),'black')
        rng=random.Random(int(t*24)+11)
        im=Image.blend(Image.new('RGB',(w,h),'#170911'),self.ruido[int(t*24)%len(self.ruido)],.56)
        if self.retrato:
            retrato=self.retrato_rojo if t>1.4 else self.retrato
            im.paste(retrato,((w-retrato.width)//2,(h-retrato.height)//2),retrato)
            im=Image.blend(im,self.ruido[int(t*24)%len(self.ruido)],.22)
            im=Image.blend(im,Image.new('RGB',(w,h),'#bd0938'),.28 if t>1 else .12)
        d=ImageDraw.Draw(im)
        for y in range(0,h,4):d.line((0,y,w,y),fill='#230c19',width=1)
        for _ in range(9):
            y=rng.randrange(h);d.rectangle((0,y,w,y+rng.randrange(1,5)),fill=rng.choice(['#6b1733','#a9294b','#391024']))
        def texto(frase,y,size=36,color='#edf9f6'):
            frase=ui(frase,self.idioma);f=self.fuente(size)
            # Reducir avisos largos para los cuatro idiomas y pantallas pequeñas.
            while d.textbbox((0,0),frase,font=f)[2]>w*.9 and size>12:size-=2;f=self.fuente(size)
            for dx,c in ((-2,'#17d7ca'),(2,'#fb1645'),(0,color)):
                d.text((w/2+dx,y),frase,font=f,fill=c,anchor='mm')
        texto('CAPRI // APAGADO AUTORIZADO',h*.13,24)
        if t<1.4:texto('CERRANDO ENLACE PERSONAL',h*.5,34)
        elif t<3.3:
            texto('ENLACE NEURONAL INESTABLE',h*.36,36)
            texto('SECUENCIA DE DESCONEXIÓN',h*.53,42)
            texto('MAXTAC // SIGNAL LOST',h*.72,25)
        else:
            texto('CIERRE DEL CONSTRUCTO',h*.33,30)
            texto('FLATLINE',h*.5,110,'#ff1749')
            texto('HASTA LA PRÓXIMA, CHOOM',h*.7,26)
        texto('Esc · cancelar apagado',h*.94,18)
        # El fotograma entero se comprime, como el cierre de un monitor CRT.
        if t>4.8:
            p=min(1,(t-4.8)/1.35);alto=max(2,round(h*(1-p)**2.3))
            banda=im.resize((w,alto),Image.Resampling.BILINEAR)
            im=Image.new('RGB',(w,h),'black');im.paste(banda,(0,(h-alto)//2))
            if p>.93:
                d=ImageDraw.Draw(im);ancho=max(1,round(w*(1-min(1,(t-6.05)/.45))))
                d.rectangle(((w-ancho)//2,h//2,(w+ancho)//2,h//2+1),fill='#ffb7cf')
        return im


class LienzoApagado:
    """Escena nativa: no copia ni amplía un bitmap de pantalla por fotograma."""
    def __init__(self,canvas,idioma='es'):
        self.c=canvas;self.idioma=idioma;self.fuentes={}

    def dibujar(self,t):
        from fuentes import FAMILIA
        from tkinter.font import Font
        c=self.c;w=int(c.cget('width'));h=int(c.cget('height'));c.delete('escena')
        if t>=DURACION:return
        rng=random.Random(int(t*18)+11)
        compresion=max(.0,1-max(0,t-4.8)/1.35)**2.3
        alto=max(2,h*compresion);arriba=(h-alto)/2
        def y(v):return arriba+v*alto
        def rect(x1,y1,x2,y2,color):
            c.create_rectangle(x1,y(y1),x2,y(y2),fill=color,outline='',tags='escena')
        if t>=6.05:
            ancho=max(0,w*(1-(t-6.05)/.45))
            if ancho>0:c.create_line((w-ancho)/2,h/2,(w+ancho)/2,h/2,fill='#ffacbf',width=2,tags='escena')
            return
        rect(0,0,w,1,'#240b17')
        for n in range(100):
            rect(0,n/100,w,(n+.22)/100,'#140a10')
        for _ in range(100):
            x=rng.randrange(w);v=rng.random()
            rect(x,v,min(w,x+rng.randrange(3,max(4,w//7))),min(1,v+.0018),rng.choice(('#78233c','#441326','#a12b46')))
        for _ in range(5):
            v=rng.random();rect(0,v,w,min(1,v+.003),'#6b1933')
        # Circuitos a ambos lados, dejando limpio el centro para leer los avisos.
        for lado in (-1,1):
            x=w/2+lado*w*.34
            c.create_line(x,y(.22),x-lado*w*.04,y(.28),x-lado*w*.04,y(.72),x,y(.78),fill='#b33651',width=2,tags='escena')
        def texto(frase,v,tamano=34,color='#f7e8ec'):
            frase=ui(frase,self.idioma)
            size=max(1,round(tamano*w/1440*compresion))
            if size not in self.fuentes:self.fuentes[size]=Font(root=c,family=FAMILIA,size=-size,weight='bold')
            f=self.fuentes[size]
            if f.measure(frase)>w*.87:
                size=max(1,int(size*w*.87/f.measure(frase)))
                if size not in self.fuentes:self.fuentes[size]=Font(root=c,family=FAMILIA,size=-size,weight='bold')
                f=self.fuentes[size]
            for dx,col in ((-2,'#54b1b0'),(2,'#cb254a'),(0,color)):
                c.create_text(w/2+dx,y(v),text=frase,fill=col,font=f,anchor='center',tags='escena')
        texto('CAPRI // APAGADO AUTORIZADO',.13,24)
        if t<1.4:texto('CERRANDO ENLACE PERSONAL',.5,38)
        elif t<3.3:
            texto('ENLACE NEURONAL INESTABLE',.36,36);texto('SECUENCIA DE DESCONEXIÓN',.53,42);texto('MAXTAC // SIGNAL LOST',.72,25)
        else:
            texto('CIERRE DEL CONSTRUCTO',.33,30);texto('FLATLINE',.5,110,'#ff315a');texto('HASTA LA PRÓXIMA, CHOOM',.7,26)
        texto('Esc · cancelar apagado',.94,18)


class SecuenciaApagado:
    def __init__(self,root,terminar,cancelar,retrato=None,idioma='es',previa=False,padre=None,al_error=None):
        self.root=root;self.terminar=terminar;self.cancelar=cancelar;self.cerrada=False;self.pendiente=None;self.enviada=False
        sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
        w,h=sw,sh
        self.al_error=al_error or (lambda e:cancelar())
        self.v=tk.Toplevel(root);self.v.withdraw();self.v.overrideredirect(True);self.v.attributes('-topmost',True)
        if previa:
            self.v.transient(padre or root)
            self.v.geometry(f'{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}')
        else:self.v.geometry(f'{w}x{h}+0+0')
        self.v.configure(bg='black')
        self.c=tk.Canvas(self.v,width=w,height=h,bg='black',highlightthickness=0);self.c.pack(fill='both',expand=True)
        self.renderer=LienzoApagado(self.c,idioma)
        self.w=w;self.h=h;self.previa=previa
        if previa:
            self.c.create_text(18,20,text=ui('VISTA PREVIA · NO APAGA EL PC',idioma),anchor='w',fill='#ffb7cf',tags='previa')
            self.c.create_text(w-24,20,text='×',fill='white',font=('Arial',22),tags='cerrar_previa')
            self.c.tag_bind('cerrar_previa','<Button-1>',lambda e:self.abortar())
        self.v.bind('<Escape>',lambda e:self.abortar());self.v.protocol('WM_DELETE_WINDOW',self.abortar)
        self.v.deiconify();self.v.update_idletasks();self.v.lift();self.v.focus_force()
        self.inicio=time.monotonic();self.tick()

    def tick(self):
        if self.cerrada:return
        try:self._fotograma()
        except Exception as error:
            self.cerrar();self.al_error(error)

    def _fotograma(self):
        inicio_frame=time.perf_counter()
        t=time.monotonic()-self.inicio
        self.renderer.dibujar(t)
        self.c.tag_raise('previa');self.c.tag_raise('cerrar_previa')
        if t>=DURACION:
            if self.previa:self.cerrar()
            else:
                self.enviada=True;self.pendiente=None;self.c.update_idletasks();self.terminar()
            return
        # Deja siempre tiempo para Escape, el bucle de Windows y los otros widgets.
        self.pendiente=self.root.after(max(16,round(1000/24-(time.perf_counter()-inicio_frame)*1000)),self.tick)

    def cerrar(self):
        self.cerrada=True
        if self.pendiente:
            try:self.root.after_cancel(self.pendiente)
            except tk.TclError:pass
        if self.v.winfo_exists():self.v.destroy()

    def abortar(self):
        if self.cerrada or self.enviada:return
        self.cerrar();self.cancelar()
