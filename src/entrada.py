"""Entrada permanente debajo del avatar, con señal de audio integrada."""
import math
from tema_ui import tk
from tema_ui import LienzoUI as CanvasUI
from idiomas import ui,idioma_actual
from fuentes import FAMILIA

TRANS='#010203'

class Entrada(CanvasUI):
    def __init__(self,padre,enviar,menu,aspecto='original'):
        super().__init__(padre,width=360,height=46,bg=TRANS,highlightthickness=0)
        self.enviar=enviar;self.menu=menu;self.placeholder=True;self.activa=False;self.hablando=False;self.nivel=0
        self.texto_placeholder='Di «Capri» o escribe…';self.foco_cambio=None;self.antes_foco=None;self.activacion=True
        self.entrada=tk.Entry(self,bg='#170c12',fg='#768b96',insertbackground='#ff9eaf',relief='flat',
                              highlightthickness=0,font=(FAMILIA,12))
        self.entrada.insert(0,ui(self.texto_placeholder))
        self.ventana=self.create_window(35,23,window=self.entrada,anchor='w')
        self.entrada.bind('<FocusIn>',self.foco);self.entrada.bind('<FocusOut>',self.desfoco)
        self.entrada.bind('<Return>',lambda e:self.enviar_actual())
        self.entrada.bind('<Button-3>',menu)
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',self.clic);self.bind('<Button-3>',menu)
        self.aplicar_aspecto(aspecto)

    def aplicar_aspecto(self,aspecto):
        from disenos_pantalla import normalizar
        self.diseno=normalizar(aspecto)
        self.fondo='#170c12';self.acento='#ff9eaf';self.borde='#9d3b52'
        self.color_voz='#edce67';self.flecha='#ec3c62';self.suave='#768b96'
        self.entrada.configure(bg=self.fondo,insertbackground=self.acento,
                               fg=self.suave if self.placeholder else '#edf5f4')
        self.dibujar()

    def foco(self,e=None):
        if self.placeholder:self.entrada.delete(0,'end');self.entrada.configure(fg='#edf5f4');self.placeholder=False
        if self.foco_cambio:self.foco_cambio(True)

    def desfoco(self,e=None):
        if not self.entrada.get():
            self.placeholder=True;self.entrada.configure(fg=self.suave);self.entrada.insert(0,ui(self.texto_placeholder))
        if self.foco_cambio:self.foco_cambio(False)

    def poner(self,texto):
        if self.antes_foco:
            otra=self.antes_foco()
            if otra is not None and otra is not self:return otra.poner(texto)
        self.placeholder=False;self.entrada.configure(fg='#edf5f4')
        self.entrada.delete(0,'end');self.entrada.insert(0,texto);self.entrada.focus_set()

    def dar_foco(self):
        if self.antes_foco:
            otra=self.antes_foco()
            if otra is not None and otra is not self:return otra.dar_foco()
        self.entrada.focus_set();self.foco()

    def enviar_actual(self):
        if self.placeholder:return
        texto=self.entrada.get().strip()
        if texto:
            if self.enviar(texto) is not False:self.entrada.delete(0,'end')

    def clic(self,e):
        margen=44 if self.diseno=='compacto' else (42 if self.diseno=='minimal' else 36)
        if e.x>self.winfo_width()-margen:self.enviar_actual()
        else:self.dar_foco()

    def señal(self,nivel,escuchando,hablando):
        self.nivel=nivel;self.activa=escuchando;self.hablando=hablando
        nuevo='Te escucho…' if escuchando else ('Di «Capri» o escribe…' if self.activacion else 'Escribe a Capri…')
        if nuevo!=self.texto_placeholder:
            self.texto_placeholder=nuevo
            if self.placeholder:self.entrada.delete(0,'end');self.entrada.insert(0,ui(nuevo))
        self.dibujar()

    def dibujar(self):
        if self.placeholder and self.entrada.get()!=ui(self.texto_placeholder):
            self.entrada.delete(0,'end');self.entrada.insert(0,ui(self.texto_placeholder))
        actual=idioma_actual()
        if getattr(self,'_idioma_fuente',None)!=(actual,self.diseno):
            familia='Yu Gothic UI' if actual=='ja' else ('Consolas' if self.diseno=='terminal' else FAMILIA)
            self.entrada.configure(font=(familia,11 if self.diseno=='terminal' else 12));self._idioma_fuente=(actual,self.diseno)
        w=max(200,self.winfo_width(),int(self.cget('width')));self.delete('marco')
        color=self.acento if self.activa else (self.color_voz if self.hablando else self.borde)
        from disenos_pantalla import superficie,ancho_entrada
        superficie(self,self.diseno,w,46,chat=True)
        if self.activa or self.hablando:
            for item in self.find_withtag('borde_entrada'):self.itemconfigure(item,outline=color)
        self.tag_lower('marco');self.itemconfigure(self.ventana,width=ancho_entrada(self.diseno,w))
        self.coords(self.ventana,35,23)
        if self.activa or self.hablando:
            for i in range(5):
                h=2+(self.nivel*11 if self.activa else 6)*abs(math.sin(i+1))
                self.create_line(15+i*3,23-h,15+i*3,23+h,fill=color,width=2,tags='marco')
        else:self.create_line(16,20,23,23,16,26,fill=self.flecha,width=2,tags='marco')
        self.create_line(w-28,28,w-18,18,fill=color,width=1.5,tags='marco')
        self.create_line(w-26,18,w-18,18,w-18,26,fill=color,width=1.5,tags='marco')
