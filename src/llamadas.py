"""Aviso telefónico y enlace conectado de Capri, sin activar el micrófono."""
import time
import math
from tema_ui import tk
from tema_ui import LienzoUI as Lienzo
from fuentes import FAMILIA


def telefono(c,x,y,s=1,color='#f3d5df',angulo=0):
    """Auricular diagonal de teléfono, con almohadillas y codo reconocibles."""
    puntos=[(-19,-25),(-9,-25),(-3,-10),(-10,-5),(-6,4),(3,11),(9,5),
            (24,12),(24,22),(19,27),(11,27),(-1,21),(-12,12),(-21,-1),(-25,-13),(-25,-20)]
    a=math.radians(angulo)
    c.create_polygon(*[v for px,py in puntos for v in (x+(px*math.cos(a)-py*math.sin(a))*s,y+(px*math.sin(a)+py*math.cos(a))*s)],fill=color,outline='',tags='telefono')


class LlamadaCapri:
    def __init__(self,root,contestar,terminar,restaurar=None,senal=None,ocupada=None,nombre='CAPRI'):
        self.root=root;self.contestar=contestar;self.terminar=terminar;self.restaurar=restaurar
        self.cerrada=False;self.conectada=False;self.pendiente=None;self.inicio=time.monotonic()
        self.ultimo_audio=self.inicio
        self.fin_lectura=None
        self.transcripcion='';self.texto_visible=''
        self.nombre=nombre.upper();self.completa=False
        self.senal=senal or (lambda:());self.ocupada=ocupada or (lambda:False)
        self.v=tk.Toplevel(root);self.v.withdraw();self.v.overrideredirect(True);self.v.configure(bg='#010203');self.v.attributes('-topmost',True)
        try:self.v.attributes('-transparentcolor','#010203')
        except tk.TclError:pass
        self.w=min(430,root.winfo_screenwidth()-48);self.h=226 if restaurar else 190
        from ventanas import area_trabajo
        l,t,_,_=area_trabajo();self.x=l+28;self.y=t+28
        self.v.geometry(f'{self.w}x{self.h}+{self.x}+{self.y}')
        self.c=Lienzo(self.v,width=self.w,height=self.h,bg='#010203',highlightthickness=0);self.c.pack()
        self.v.bind('<Escape>',lambda e:self.rechazar());self.v.protocol('WM_DELETE_WINDOW',self.rechazar)
        self.dibujar()
        from ventanas import mostrar_no_activar
        mostrar_no_activar(self.v)

    def dibujar(self):
        if self.cerrada:return
        if self.pendiente:self.root.after_cancel(self.pendiente);self.pendiente=None
        t=time.monotonic()-self.inicio
        if self.conectada and self.ocupada():self.ultimo_audio=time.monotonic()
        if (not self.conectada and t>=20) or (self.fin_lectura is not None and time.monotonic()>=self.fin_lectura) or t>=120:
            if self.conectada and self.fin_lectura is not None and time.monotonic()>=self.fin_lectura:self.completa=True
            self.rechazar(activar=False);return
        c=self.c;c.delete('all');w=self.w;h=self.h
        color='#ff4569' if self.conectada or int(t*2)%2 else '#bd294a'
        # Tres esquinas cortadas; la inferior izquierda queda recta.
        c.create_polygon(2,21,21,2,w-21,2,w-2,21,w-2,h-21,w-21,h-2,2,h-2,
                         fill='#170e15',outline=color,width=1,tags='marco_llamada')
        c.create_line(23,8,w-25,8,fill='#5d333b')
        if self.conectada:
            c.create_polygon(16,31,28,19,90,19,102,31,102,105,16,105,fill='#57252c',outline='#a95852')
            for y in range(23,104,4):c.create_line(max(19,50-y),y,min(99,68+y),y,fill='#683039')
            c.create_line(23,33,31,25,44,25,fill='#dca89a');c.create_line(96,83,96,98,80,98,fill='#dca89a')
            c.create_text(59,48,text='CALL',fill='#fff4d9',font=(FAMILIA,17,'bold'))
            telefono(c,59,83,.48,color='#ebc7af')
            c.create_text(120,33,text=self.nombre,anchor='w',fill='#eaf1ed',font=(FAMILIA,19,'bold'))
            c.create_text(w-22,33,text=f'00:{int(t):02}',anchor='e',fill='#90a7a3',font=(FAMILIA,9))
            c.create_oval(120,54,125,59,fill='#8bd3b4',outline='')
            c.create_text(133,57,text='ENLACE ACTIVO',anchor='w',fill='#8bd3b4',font=(FAMILIA,9,'bold'))
            niveles=list(self.senal())[-28:];niveles=[0.]*(28-len(niveles))+niveles
            for i,nivel in enumerate(niveles):
                x=122+i*6;alto=1+min(1,max(0,nivel))*18
                c.create_line(x,79-alto/2,x,79+alto/2,fill='#91c3b7' if nivel>.02 else '#405554',width=2,tags='onda_voz')
            c.create_text(120,102,text='Cerrar aviso',anchor='w',fill='#aeb9b6',font=(FAMILIA,9),tags='rechazar')
            if self.transcripcion:
                c.create_line(20,120,w-20,120,fill='#532336')
                c.create_text(22,136,text=self.texto_visible or '…',anchor='nw',fill='#e8e7ed',font=(FAMILIA,11),width=w-44,tags='subtitulo_llamada')
        else:
            c.create_polygon(18,31,26,23,78,23,88,33,88,91,18,91,fill='#3b1525',outline='#9e3a58')
            vibracion=math.sin(t*48) if t%1.8<.55 else 0.
            cx=53.4+vibracion*2;cy=56
            telefono(c,cx,cy,.82,angulo=vibracion*8)
            # Ondas desde el hueco del auricular, orientadas hacia su lado abierto.
            for radio in (8,14,20):
                c.create_arc(cx-radio,cy-radio,cx+radio,cy+radio,start=5-vibracion*8,extent=80,
                             style='arc',outline='#ee7494' if vibracion else '#93435e',width=2,tags='ondas_telefono')
            c.create_text(105,37,text=self.nombre,anchor='w',fill='#eef1e9',font=(FAMILIA,22,'bold'))
            c.create_oval(106,67,111,72,fill='#ff91b0',outline='')
            c.create_text(120,70,text='LLAMADA ENTRANTE',anchor='w',fill='#ff91b0',font=(FAMILIA,10))
            c.create_line(20,104,w-20,104,fill='#532336')
            c.create_text(22,123,text='Capri está tramando algo…' if self.nombre=='CAPRI' else 'Transmisión entrante desde Night City…',anchor='w',fill='#e8cbd5',font=(FAMILIA,11),width=w-44)
            def boton(x1,x2,y,texto,tag,fondo):
                c.create_polygon(x1+5,y,x2-5,y,x2,y+5,x2,y+25,x2-5,y+30,x1,y+30,x1,y+5,
                                 fill=fondo,outline='#ae3a55',tags=tag)
                c.create_text((x1+x2)/2,y+15,text=texto,fill='#fff0f5' if tag=='contestar' else '#c6a5b3',font=(FAMILIA,10,'bold'),tags=tag)
            boton(20,w/2-7,146,'Contestar','contestar','#86213f');boton(w/2+7,w-20,146,'Ahora no','rechazar','#28121e')
            if self.restaurar:boton(20,w-20,182,'Restaurar ventana','restaurar','#431526')
        for tag,accion in (('contestar',self.aceptar),('rechazar',self.rechazar),('restaurar',self.devolver)):
            c.tag_bind(tag,'<Button-1>',lambda e,a=accion:a())
        self.pendiente=self.root.after(40 if self.conectada else 60,self.dibujar)

    def preparar_voz(self,texto):
        self.transcripcion=texto;self.texto_visible=''
        self.ajustar_altura_texto();self.dibujar()

    def ajustar_altura_texto(self):
        # Solo el texto ya pronunciado ocupa espacio; el resto del guion no anticipa líneas.
        medida=self.c.create_text(22,136,text=self.texto_visible or '…',anchor='nw',font=(FAMILIA,11),width=self.w-44)
        caja=self.c.bbox(medida);self.c.delete(medida)
        alto=160+(caja[3]-caja[1] if caja else 20)
        if alto!=self.h:
            self.h=alto
            self.v.geometry(f'{self.w}x{self.h}+{self.x}+{self.y}');self.c.configure(height=self.h)

    def revelar(self,texto,caracteres):
        if not self.cerrada and texto==self.transcripcion:
            self.texto_visible=texto[:caracteres]
            self.ajustar_altura_texto();self.dibujar()

    def terminar_voz(self,completa=False):
        if self.conectada and not self.cerrada:self.completa=completa;self.rechazar(activar=False)

    def cerrar(self):
        if self.cerrada:return
        self.cerrada=True
        if self.pendiente:self.root.after_cancel(self.pendiente);self.pendiente=None
        if self.v.winfo_exists():self.v.destroy()

    def aceptar(self):
        if self.cerrada or self.conectada:return
        self.conectada=True;self.inicio=time.monotonic();self.ultimo_audio=self.inicio;self.w=min(self.w,350);self.h=124
        self.v.geometry(f'{self.w}x{self.h}+{self.x}+{self.y}');self.c.configure(width=self.w,height=self.h)
        self.dibujar();self.contestar()

    def rechazar(self,activar=True):
        if self.cerrada:return
        self.cerrar();self.terminar(activar)

    def devolver(self):
        if self.restaurar:self.restaurar(True)
