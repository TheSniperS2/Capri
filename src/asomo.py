"""Forma temporal curiosa: el mismo Capri se asoma y sigue el cursor."""
import math,random,time
from pathlib import Path
from PIL import Image,ImageTk
import ventanas


class AsomoCurioso:
    def __init__(self,root,canvas,ruta,duracion=None):
        self.root=root;self.c=canvas;self.anterior=root.geometry()
        self.inicio=time.monotonic();self.hasta=self.inicio+duracion if duracion is not None else float('inf')
        self.origen=(root.winfo_x(),root.winfo_y());self.w=310;self.h=248
        self.borde=random.choice(('izquierda','derecha','abajo'))
        with Image.open(ruta) as fuente:im=fuente.convert('RGBA').resize((self.w,self.h),Image.Resampling.LANCZOS)
        ojos=[(737.46/1448*self.w,751.35/1086*self.h),(957.98/1448*self.w,620.16/1086*self.h)]
        self.radios=(3.1,5.6)
        # El cuerpo continúa fuera del lienzo: ningún margen separa el corte del borde.
        if self.borde=='izquierda':
            im=im.transpose(Image.Transpose.ROTATE_270).crop((65,0,248,310))
            ojos=[(247-y-65,x) for x,y in ojos]
        elif self.borde=='derecha':
            im=im.transpose(Image.Transpose.ROTATE_90).crop((0,0,183,310))
            ojos=[(y,309-x) for x,y in ojos]
        else:im=im.crop((0,0,310,224))
        self.w,self.h=im.size;self.ojos=ojos
        l,t,r,b=ventanas.area_trabajo()
        self.x=l if self.borde=='izquierda' else r-self.w
        self.y=b-self.h if self.borde=='abajo' else t+max(0,(b-t-self.h)//2)
        im.putalpha(im.getchannel('A').point(lambda a:255 if a>110 else 0))
        from avatar import fragmentar
        self.foto=ImageTk.PhotoImage(im,master=canvas)
        self.fragmentos=[ImageTk.PhotoImage(fragmentar(im,i,True),master=canvas) for i in range(6)]
        self.ultimo_parpadeo=self.inicio+random.uniform(4,7);self.parpadeo_hasta=0

    def mirar(self,cursor):
        puntos=[]
        for x,y in self.ojos:
            dx=math.tanh((cursor[0]-self.x-x)/300)*1.0
            dy=math.tanh((cursor[1]-self.y-y)/240)*1.0
            puntos.append((x+dx,y+dy))
        return puntos

    def dibujar(self,ahora=None,cursor=None):
        ahora=time.monotonic() if ahora is None else ahora
        if ahora>=self.hasta:return False
        t=ahora-self.inicio;u=min(1,t/.42);u=u*u*(3-2*u)
        x=round(self.origen[0]+(self.x-self.origen[0])*u);y=round(self.origen[1]+(self.y-self.origen[1])*u)
        self.root.geometry(f'{self.w}x{self.h}+{x}+{y}');self.c.configure(width=self.w,height=self.h);self.c.delete('all')
        self.c.create_image(self.w/2,self.h/2,image=self.fragmentos[int(t*28)%6] if t<.42 else self.foto,tags='asomo_curioso')
        if t<.42:return True
        if ahora>=self.ultimo_parpadeo:
            self.parpadeo_hasta=ahora+.12;self.ultimo_parpadeo=ahora+random.uniform(4,8)
        posiciones=self.mirar(cursor or self.root.winfo_pointerxy())
        for (x,y),(px,py),radio in zip(self.ojos,posiciones,self.radios):
            if ahora<self.parpadeo_hasta:
                self.c.create_oval(x-5.4,y-5.4,x+5.4,y+5.4,fill='#030b13',outline='',tags='ojo_asomo')
                self.c.create_line(x-5,y,x+5,y,fill='#00d9bb',width=2,tags='ojo_asomo')
            else:
                self.c.create_oval(x-radio-1.3,y-radio-1.3,x+radio+1.3,y+radio+1.3,fill='#0099ee',outline='',tags='ojo_asomo')
                self.c.create_oval(px-radio,py-radio,px+radio,py+radio,fill='#f1f4f6',outline='',tags=('ojo_asomo','pupila_asomo'))
        return True

    def cerrar(self):self.root.geometry(self.anterior)
