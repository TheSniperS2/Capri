"""Conversación compacta junto a Capri, con escritura y glitch transitorio."""
import random
import time
import tkinter as tk
import os
from fuentes import FAMILIA

TRANS='#010203'

class Dialogo:
    def __init__(self,raiz,habilitado,enviar=None,historial=None,detener=None,glitch=None):
        self.raiz=raiz;self.habilitado=habilitado;self.enviar=enviar;self.historial=historial;self.detener=detener
        self.glitch=glitch or (lambda:True);self.ventana=None;self.pendiente=None
        self.objetivo='';self.visible='';self.usuario='';self.vence=0;self.fase=0;self.editando=False
        self.estado='ENLACE ABIERTO';self.entrada=None;self.control_entrada=None;self.manual=False;self.alto_canvas=108;self.sincronizada=False
        self.menu=None

    def crear(self):
        if self.ventana is not None and self.ventana.winfo_exists():return
        p=self.ventana=tk.Toplevel(self.raiz);p.title('Capri · Enlace');p.overrideredirect(True);p.attributes('-topmost',True)
        p.configure(bg=TRANS)
        if os.name=='nt':p.wm_attributes('-transparentcolor',TRANS)
        self.canvas=tk.Canvas(p,width=364,height=self.alto_canvas,bg=TRANS,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Button-3>',lambda e:self.menu(e) if self.menu else None)
        p.bind('<Escape>',lambda e:self.detener() if self.detener else self.ocultar())

    def abrir(self):
        self.manual=True
        if self.objetivo or self.usuario:
            self.crear();self.vence=time.monotonic()+60;self.ventana.deiconify();self.posicionar()
            if self.pendiente is None:self.tick()
        if self.control_entrada:self.control_entrada.dar_foco()

    def revisar(self,texto):
        self.estado='REVISA EL DICTADO'
        if self.control_entrada:self.control_entrada.poner(texto)

    def recibir_usuario(self,texto):
        if not self.habilitado() and not self.manual:return
        self.usuario=texto;self.objetivo='';self.visible='';self.estado='PROCESANDO';self.sincronizada=False
        self.crear();self.vence=time.monotonic()+60;self.ventana.deiconify();self.posicionar()
        if self.pendiente is None:self.tick()

    def enviar_entrada(self):
        if self.control_entrada:self.control_entrada.enviar_actual()

    def mostrar(self,texto,sincronizada=False):
        if (not self.habilitado() and not self.manual) or not texto:return
        self.crear();texto=texto[:1400]
        if sincronizada or not texto.startswith(self.objetivo):self.visible=''
        self.sincronizada=sincronizada
        self.objetivo=texto;self.estado='TRANSMISIÓN';self.vence=time.monotonic()+25
        self.ventana.deiconify();self.posicionar()
        if self.pendiente is None:self.tick()

    def preparar_voz(self,texto,estado='PREPARANDO VOZ'):
        self.mostrar(texto,sincronizada=True);self.estado=estado

    def revelar(self,texto,caracteres):
        if not self.habilitado() and not self.manual:return
        self.objetivo=texto[:1400];self.visible=self.objetivo[:max(0,caracteres)]
        self.sincronizada=True;self.estado='HABLANDO';self.vence=time.monotonic()+25
        if self.ventana and self.ventana.winfo_exists():self.dibujar()

    def terminar_voz(self):
        self.visible=self.objetivo;self.sincronizada=False;self.estado='ENLACE ABIERTO'

    def posicionar(self):
        if not self.ventana or not self.ventana.winfo_exists():return
        sw=self.raiz.winfo_screenwidth();sh=self.raiz.winfo_screenheight()
        ancho=max(280,self.raiz.winfo_width());alto=self.alto_canvas
        self.canvas.configure(width=ancho)
        x=self.raiz.winfo_x()+(self.raiz.winfo_width()-ancho)//2
        y=self.raiz.winfo_y()-alto-8
        if y<8:
            x=self.raiz.winfo_x()-ancho-10
            if x<8:x=self.raiz.winfo_x()+self.raiz.winfo_width()+8
            y=self.raiz.winfo_y()+30
        x=max(8,min(x,sw-ancho-8));y=max(8,min(y,sh-alto-12))
        self.ventana.geometry(f'{ancho}x{alto}+{x}+{y}')

    def dibujar(self):
        c=self.canvas;c.delete('all');ancho=max(280,c.winfo_width());alto=self.alto_canvas
        c.create_polygon(13,9,ancho-22,9,ancho-10,21,ancho-10,alto-24,ancho-22,alto-12,22,alto-12,10,alto-24,10,22,
                         fill='#0d111b',outline='#6f9ba3',width=1)
        c.create_line(22,alto-11,ancho-23,alto-11,fill='#ec3c62',width=3)
        c.create_rectangle(26,44,80,61,fill='#f2d959',outline='')
        c.create_text(31,53,text='CAPRI',anchor='w',fill='#151822',font=(FAMILIA,10,'bold'))
        c.create_text(92,53,text=self.estado,anchor='w',fill='#80939c',font=(FAMILIA,8))
        pregunta=self.usuario.replace('\n',' ')
        c.create_text(29,25,text=('TÚ > '+pregunta[:52]+('…' if len(pregunta)>52 else '')) if pregunta else 'ENLACE PERSONAL',anchor='w',width=ancho-58,fill='#8d98a4',font=(FAMILIA,9))
        contenido=self.visible[-230:].replace('\n',' ')
        # El glitch afecta solo a la punta de escritura; el texto confirmado
        # permanece intacto, accesible en el historial sin símbolos añadidos.
        escribiendo=len(self.visible)<len(self.objetivo)
        punta=random.choice('_/-') if escribiendo and self.glitch() else ('_' if escribiendo else '')
        cuerpo=c.create_text(29,76,text=('…' if len(self.visible)>230 else '')+contenido+punta,anchor='nw',width=ancho-62,
                      fill='#edf0fa',font=(FAMILIA,12))
        caja=c.bbox(cuerpo)
        requerido=max(108,min(300,(caja[3] if caja else 86)+24))
        if requerido!=self.alto_canvas:
            self.alto_canvas=requerido;c.configure(height=requerido)
        if escribiendo and self.glitch() and self.fase%9==0:
            y=81+(self.fase*7)%60;c.create_line(ancho-75,y,ancho-29,y,fill='#ff4267')

    def tick(self):
        self.pendiente=None
        if (not self.habilitado() and not self.manual) or (time.monotonic()>self.vence and not self.editando):self.ocultar();return
        if not self.sincronizada:self.visible=self.objetivo[:min(len(self.objetivo),len(self.visible)+2)]
        self.fase+=1;self.dibujar();self.posicionar()
        self.pendiente=self.raiz.after(25 if len(self.visible)<len(self.objetivo) else 180,self.tick)

    def ocultar(self):
        if self.pendiente:self.raiz.after_cancel(self.pendiente);self.pendiente=None
        self.editando=False;self.manual=False
        if self.ventana and self.ventana.winfo_exists():self.ventana.withdraw()
