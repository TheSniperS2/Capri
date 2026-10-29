"""Entrada permanente debajo del avatar, con señal de audio integrada."""
import math
import tkinter as tk
from fuentes import FAMILIA

TRANS='#010203'

class Entrada(tk.Canvas):
    def __init__(self,padre,enviar,menu):
        super().__init__(padre,width=360,height=46,bg=TRANS,highlightthickness=0)
        self.enviar=enviar;self.menu=menu;self.placeholder=True;self.activa=False;self.hablando=False;self.nivel=0
        self.texto_placeholder='Di «Capri» o escribe…';self.foco_cambio=None;self.antes_foco=None;self.activacion=True
        self.entrada=tk.Entry(self,bg='#170c12',fg='#768b96',insertbackground='#ff9eaf',relief='flat',
                              highlightthickness=0,font=(FAMILIA,12))
        self.entrada.insert(0,self.texto_placeholder)
        self.ventana=self.create_window(35,23,window=self.entrada,anchor='w')
        self.entrada.bind('<FocusIn>',self.foco);self.entrada.bind('<FocusOut>',self.desfoco)
        self.entrada.bind('<Return>',lambda e:self.enviar_actual())
        self.entrada.bind('<Button-3>',menu)
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',self.clic);self.bind('<Button-3>',menu)

    def foco(self,e=None):
        if self.placeholder:self.entrada.delete(0,'end');self.entrada.configure(fg='#edf5f4');self.placeholder=False
        if self.foco_cambio:self.foco_cambio(True)

    def desfoco(self,e=None):
        if not self.entrada.get():
            self.placeholder=True;self.entrada.configure(fg='#768b96');self.entrada.insert(0,self.texto_placeholder)
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
        if e.x>self.winfo_width()-36:self.enviar_actual()
        else:self.dar_foco()

    def señal(self,nivel,escuchando,hablando):
        self.nivel=nivel;self.activa=escuchando;self.hablando=hablando
        nuevo='Te escucho…' if escuchando else ('Di «Capri» o escribe…' if self.activacion else 'Escribe a Capri…')
        if nuevo!=self.texto_placeholder:
            self.texto_placeholder=nuevo
            if self.placeholder:self.entrada.delete(0,'end');self.entrada.insert(0,nuevo)
        self.dibujar()

    def dibujar(self):
        w=max(200,self.winfo_width(),int(self.cget('width')));self.delete('marco')
        color='#ff9eaf' if self.activa else ('#edce67' if self.hablando else '#9d3b52')
        self.create_polygon(15,4,w-9,4,w-4,10,w-4,34,w-15,42,5,42,5,14,fill='#170c12',outline=color,tags='marco')
        self.tag_lower('marco');self.itemconfigure(self.ventana,width=max(110,w-78))
        self.coords(self.ventana,35,23)
        if self.activa or self.hablando:
            for i in range(5):
                h=2+(self.nivel*11 if self.activa else 6)*abs(math.sin(i+1))
                self.create_line(15+i*3,23-h,15+i*3,23+h,fill=color,width=2,tags='marco')
        else:self.create_line(16,20,23,23,16,26,fill='#ec3c62',width=2,tags='marco')
        self.create_line(w-28,28,w-18,18,fill=color,width=1.5,tags='marco')
        self.create_line(w-26,18,w-18,18,w-18,26,fill=color,width=1.5,tags='marco')
