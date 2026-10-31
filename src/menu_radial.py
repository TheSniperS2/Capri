"""Menú circular del personaje, con acciones existentes y navegación por teclado."""
import math
from tema_ui import tk
from tema_ui import LienzoUI as CanvasUI
from fuentes import FAMILIA

def sector(x,y,centro,radio,cantidad):
    dx=x-centro;dy=y-centro;distancia=math.hypot(dx,dy)
    if distancia<radio*.34:return -1
    if distancia>radio:return None
    angulo=(math.atan2(dy,dx)+math.pi/2+math.pi/cantidad)%(2*math.pi)
    return min(cantidad-1,int(angulo/(2*math.pi/cantidad)))

def colocar_menu(personaje,pantalla,tamano):
    x,y,w,h=personaje;sw,sh=pantalla;margen=10
    candidatos=[(x+(w-tamano)/2,y-tamano-margen),
                (x+w+margen,y+(h-tamano)/2),(x-tamano-margen,y+(h-tamano)/2),
                (x+(w-tamano)/2,y+h+margen)]
    posiciones=[(max(6,min(round(a),sw-tamano-6)),max(6,min(round(b),sh-tamano-6))) for a,b in candidatos]
    def solape(p):
        a,b=p;return max(0,min(a+tamano,x+w)-max(a,x))*max(0,min(b+tamano,y+h)-max(b,y))
    return min(enumerate(posiciones),key=lambda par:(solape(par[1]),par[0]))[1]

def icono(c,x,y,indice,color):
    def linea(*p):c.create_line(*[v+(x if i%2==0 else y) for i,v in enumerate(p)],fill=color,width=2)
    if indice==9:
        # Cuentagotas: cuerpo diagonal, boquilla y empuñadura separada.
        linea(-11,11,-8,4,2,-6,7,-1,-3,9,-11,11)
        linea(-4,0,2,6)
        linea(0,-9,5,-14,14,-5,9,0,0,-9)
        linea(4,-5,8,-1)
    elif indice==8:
        linea(-9,8,-7,1,5,-11,11,-5,-1,7,-9,8)
        linea(-5,0,1,6)
    elif indice==0:
        puntos=[]
        for i in range(16):
            a=i*math.pi/8;r=10 if i%2==0 else 7;puntos.extend((x+math.cos(a)*r,y+math.sin(a)*r))
        c.create_polygon(*puntos,fill='',outline=color,width=2);c.create_oval(x-3,y-3,x+3,y+3,outline=color)
    elif indice==1:linea(-10,-7,10,-7,10,6,0,6,-6,11,-6,6,-10,6,-10,-7)
    elif indice==2:
        linea(-11,-5,11,-5,13,6,7,7,3,3,-3,3,-7,7,-13,6,-11,-5)
        linea(-8,-1,-2,-1);linea(-5,-4,-5,2);linea(5,-1,8,2)
    elif indice==3:linea(0,-11,10,0,0,11,-10,0,0,-11);linea(-4,0,4,0)
    elif indice==4:linea(-11,-8,11,-8,11,7,-11,7,-11,-8);linea(-11,-3,11,-3)
    elif indice==5:linea(-9,-2,-9,-9,-2,-9);linea(2,9,9,9,9,2);linea(-9,-9,9,9)
    elif indice==6:
        c.create_oval(x-4,y-10,x+4,y+3,outline=color,width=2)
        linea(-8,-1,-8,5,0,8,8,5,8,-1);linea(0,8,0,12)
    else:
        for dx in (-8,0,8):c.create_oval(x+dx-2,y-2,x+dx+2,y+2,fill=color,outline='')

class MenuRadial:
    def __init__(self,root,x,y,opciones,terminar=None,personaje=None):
        self.cerrado=False
        self.ventana=tk.Toplevel(root);self.ventana.withdraw();self.ventana.overrideredirect(True)
        self.ventana.attributes('-topmost',True);self.ventana.configure(bg='#010203')
        try:self.ventana.wm_attributes('-transparentcolor','#010203')
        except tk.TclError:pass
        self.tamano=min(430,root.winfo_screenheight()-40);self.centro=self.tamano/2;self.radio=self.centro-12
        if personaje is not None:
            px,py,pw,ph=personaje
            espacio=max(py-16,root.winfo_screenheight()-py-ph-16,px-16,root.winfo_screenwidth()-px-pw-16)
            self.tamano=min(self.tamano,root.winfo_screenwidth()-12,max(180,espacio))
            self.centro=self.tamano/2;self.radio=self.centro-12
        self.canvas=CanvasUI(self.ventana,width=self.tamano,height=self.tamano,bg='#010203',highlightthickness=0)
        self.canvas.pack();self.pila=[];self.opciones=opciones;self.seleccion=-1;self.terminar=terminar
        x=max(6,min(round(x-self.centro),root.winfo_screenwidth()-self.tamano-6))
        y=max(6,min(round(y-self.centro),root.winfo_screenheight()-self.tamano-6))
        if personaje is not None:x,y=colocar_menu(personaje,(root.winfo_screenwidth(),root.winfo_screenheight()),self.tamano)
        self.ventana.geometry(f'{self.tamano}x{self.tamano}+{x}+{y}')
        self.canvas.bind('<Motion>',self.mover);self.ventana.bind('<Button-1>',self.click)
        self.ventana.bind('<Escape>',lambda e:self.cerrar());self.ventana.bind('<Button-3>',lambda e:self.cerrar())
        self.ventana.bind('<Return>',lambda e:self.ejecutar(self.seleccion))
        self.ventana.bind('<Right>',lambda e:self.tecla(1));self.ventana.bind('<Left>',lambda e:self.tecla(-1))
        self.ventana.deiconify();self.ventana.grab_set();self.ventana.focus_force();self.dibujar()

    def tecla(self,paso):
        self.seleccion=(self.seleccion+paso)%len(self.opciones);self.dibujar()

    def giro(self):
        if self.pila:
            for i,(texto,_) in enumerate(self.opciones):
                if texto=='Cerrar Capri':return math.pi-i*2*math.pi/len(self.opciones)
        return 0.

    def indice(self,x,y,radio=None):
        # El submenú reserva el sector inferior para cerrar, también al pulsarlo.
        a=-self.giro();dx=x-self.centro;dy=y-self.centro
        x=self.centro+dx*math.cos(a)-dy*math.sin(a)
        y=self.centro+dx*math.sin(a)+dy*math.cos(a)
        return sector(x,y,self.centro,self.radio if radio is None else radio,len(self.opciones))

    def mover(self,e):
        nuevo=self.indice(e.x,e.y)
        if nuevo!=self.seleccion:self.seleccion=nuevo;self.dibujar()

    def click(self,e):self.ejecutar(self.indice(e.x,e.y))

    def ejecutar(self,indice):
        if self.cerrado:return
        if indice is None:self.cerrar();return
        if indice==-1:
            if self.pila:self.opciones=self.pila.pop();self.seleccion=-1;self.dibujar()
            else:self.cerrar()
            return
        if not 0<=indice<len(self.opciones):return
        _,accion=self.opciones[indice]
        if isinstance(accion,list):self.pila.append(self.opciones);self.opciones=accion;self.seleccion=-1;self.dibujar()
        else:self.cerrar();accion()

    def dibujar(self):
        from tkinter import font as tkfont
        from idiomas import ui,idioma_actual
        c=self.canvas;c.delete('all');self.fuentes=[];m=self.centro;r=self.radio;n=len(self.opciones);paso=2*math.pi/n
        c.create_oval(m-r-4,m-r-4,m+r+4,m+r+4,outline='#9d2949',width=1)
        for i,(texto,_) in enumerate(self.opciones):
            angulo=-math.pi/2+i*paso+self.giro();inicio=angulo-paso/2+.025;fin=angulo+paso/2-.025
            puntos=[]
            for k in range(13):
                a=inicio+(fin-inicio)*k/12;puntos.extend((m+math.cos(a)*r,m+math.sin(a)*r))
            for k in range(12,-1,-1):
                a=inicio+(fin-inicio)*k/12;puntos.extend((m+math.cos(a)*r*.39,m+math.sin(a)*r*.39))
            activo=i==self.seleccion
            c.create_polygon(*puntos,fill='#4b1528' if activo else '#1c0b13',outline='#ff6486' if activo else '#8b2744',width=3,tags=f'sector_{i}')
            x=m+math.cos(angulo)*r*.72;y=m+math.sin(angulo)*r*.72
            factor=self.tamano/430
            if not self.pila:
                anteriores=set(c.find_all())
                icono(c,x,y-22*factor,9 if texto=='Color' else (8 if texto=='Escribir' else i),'#ffb5c6' if activo else '#d79cac')
                for creado in set(c.find_all())-anteriores:c.addtag_withtag(f'icono_{i}',creado)
                y=c.bbox(f'icono_{i}')[3]+max(7,round(8*factor))
            familia='Yu Gothic UI' if idioma_actual()=='ja' else FAMILIA
            tamano=max(7,round(10*factor));ancho=r*.50;traducido=ui(texto)
            def envolver(fuente):
                lineas=['']
                for palabra in traducido.split():
                    candidato=(lineas[-1]+' '+palabra).strip()
                    if lineas[-1] and fuente.measure(candidato)>ancho:lineas.append(palabra)
                    else:lineas[-1]=candidato
                return '\n'.join(lineas)
            fuente=tkfont.Font(root=c,font=(familia,tamano,'bold'))
            self.fuentes.append(fuente)
            item=c.create_text(x,y,text=envolver(fuente),anchor='n' if not self.pila else 'center',justify='center',fill='#ffb5c6' if activo else '#e1d9ee',font=fuente,tags=f'etiqueta_{i}')
            while tamano>7:
                bbox=c.bbox(item)
                if bbox and all(self.indice(px,py,r-6)==i for px,py in ((bbox[0]-3,bbox[1]-2),(bbox[2]+3,bbox[1]-2),(bbox[0]-3,bbox[3]+2),(bbox[2]+3,bbox[3]+2))):break
                tamano-=1;fuente.configure(size=tamano);c.itemconfigure(item,text=envolver(fuente))
        a=r*.34;c.create_oval(m-a,m-a,m+a,m+a,fill='#32101d',outline='#e985a0',width=2)
        c.create_text(m,m-19,text='‹' if self.pila else '×',fill='#ffb4c5',font=(FAMILIA,23))
        c.create_text(m,m+8,text='CAPRI',fill='#f3eaff',font=(FAMILIA,15,'bold'))
        c.create_text(m,m+32,text='Volver' if self.pila else 'Cerrar',fill='#be8d9d',font=(FAMILIA,9))

    def cerrar(self):
        if self.cerrado:return
        self.cerrado=True
        if self.ventana.winfo_exists():self.ventana.grab_release();self.ventana.destroy()
        if self.terminar:self.terminar();self.terminar=None
