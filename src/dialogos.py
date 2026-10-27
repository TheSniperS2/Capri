"""Conversación compacta junto a Capri, con escritura y glitch transitorio."""
import random
import time
import tkinter as tk

class Dialogo:
    def __init__(self,raiz,habilitado,enviar=None,historial=None,detener=None,glitch=None):
        self.raiz=raiz;self.habilitado=habilitado;self.enviar=enviar;self.historial=historial;self.detener=detener
        self.glitch=glitch or (lambda:True);self.ventana=None;self.pendiente=None
        self.objetivo='';self.visible='';self.usuario='';self.vence=0;self.fase=0;self.editando=False
        self.estado='ENLACE ABIERTO';self.entrada=None;self.manual=False;self.alto_canvas=156;self.sincronizada=False

    def crear(self):
        if self.ventana is not None and self.ventana.winfo_exists():return
        p=self.ventana=tk.Toplevel(self.raiz);p.title('Capri · Enlace');p.overrideredirect(True);p.attributes('-topmost',True)
        p.configure(bg='#080c17')
        self.canvas=tk.Canvas(p,width=364,height=self.alto_canvas,bg='#080c17',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        barra=tk.Frame(p,bg='#11192b',padx=9,pady=4);barra.pack(fill='x',padx=11,pady=(0,10))
        self.entrada=tk.Entry(barra,bg='#11192b',fg='#f6eff1',insertbackground='#b5ff7c',relief='flat',font=('Segoe UI',10))
        self.entrada.pack(side='left',fill='x',expand=True)
        self.entrada.bind('<Return>',lambda e:self.enviar_entrada())
        self.entrada.bind('<FocusIn>',lambda e:setattr(self,'editando',True))
        self.entrada.bind('<FocusOut>',lambda e:setattr(self,'editando',False))
        tk.Button(barra,text='↗',command=self.enviar_entrada,bg='#11192b',fg='#b5ff7c',relief='flat',bd=0).pack(side='right')
        self.canvas.bind('<Button-1>',self.clic)
        p.bind('<Escape>',lambda e:self.detener() if self.detener else self.ocultar())

    def abrir(self):
        self.manual=True
        self.crear();self.vence=time.monotonic()+60;self.ventana.deiconify();self.posicionar()
        self.entrada.focus_set()
        if self.pendiente is None:self.tick()

    def revisar(self,texto):
        self.abrir();self.estado='REVISA EL DICTADO'
        self.entrada.delete(0,'end');self.entrada.insert(0,texto)

    def recibir_usuario(self,texto):
        if not self.habilitado() and not self.manual:return
        self.usuario=texto;self.objetivo='';self.visible='';self.estado='PROCESANDO';self.sincronizada=False
        self.crear();self.vence=time.monotonic()+60;self.ventana.deiconify();self.posicionar()
        if self.pendiente is None:self.tick()

    def enviar_entrada(self):
        texto=self.entrada.get().strip()
        if texto and self.enviar:
            self.entrada.delete(0,'end');self.enviar(texto)

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
        alto=self.alto_canvas+54
        x=self.raiz.winfo_x()+(self.raiz.winfo_width()-364)//2
        y=self.raiz.winfo_y()-alto-8
        if y<8:
            x=self.raiz.winfo_x()-374
            if x<8:x=self.raiz.winfo_x()+self.raiz.winfo_width()+8
            y=self.raiz.winfo_y()+30
        x=max(8,min(x,sw-374));y=max(8,min(y,sh-alto-12))
        self.ventana.geometry(f'364x{alto}+{x}+{y}')

    def dibujar(self):
        c=self.canvas;c.delete('all');ancho=max(364,c.winfo_width());alto=self.alto_canvas
        c.create_polygon(13,9,ancho-22,9,ancho-10,21,ancho-10,alto-24,ancho-22,alto-12,22,alto-12,10,alto-24,10,22,
                         fill='#0d111b',outline='#6f9ba3',width=1)
        c.create_line(22,alto-11,ancho-23,alto-11,fill='#ec3c62',width=3)
        c.create_rectangle(26,44,80,61,fill='#f2d959',outline='')
        c.create_text(31,53,text='CAPRI',anchor='w',fill='#151822',font=('Consolas',9,'bold'))
        c.create_text(92,53,text=self.estado,anchor='w',fill='#80939c',font=('Consolas',8))
        c.create_text(ancho-28,27,text='×',fill='#a4acc1',font=('Segoe UI',13))
        pregunta=self.usuario.replace('\n',' ')
        c.create_text(29,25,text=('TÚ > '+pregunta[:52]+('…' if len(pregunta)>52 else '')) if pregunta else 'ENLACE PERSONAL',anchor='w',width=ancho-74,fill='#8d98a4',font=('Segoe UI',9))
        contenido=self.visible[-230:].replace('\n',' ')
        # El glitch afecta solo a la punta de escritura; el texto confirmado
        # permanece intacto, accesible en el historial sin símbolos añadidos.
        escribiendo=len(self.visible)<len(self.objetivo)
        punta=random.choice('▱▰_/░') if escribiendo and self.glitch() else ('▏' if escribiendo else '')
        cuerpo=c.create_text(29,76,text=('…' if len(self.visible)>230 else '')+contenido+punta,anchor='nw',width=ancho-62,
                      fill='#edf0fa',font=('Segoe UI',11))
        caja=c.bbox(cuerpo)
        requerido=max(156,min(260,(caja[3] if caja else 90)+44))
        if requerido!=self.alto_canvas:
            self.alto_canvas=requerido;c.configure(height=requerido)
        if escribiendo and self.glitch() and self.fase%9==0:
            y=81+(self.fase*7)%60;c.create_line(ancho-75,y,ancho-29,y,fill='#ff4267')
        c.create_text(29,alto-26,text='HISTORIAL',anchor='w',fill='#8d98b4',font=('Consolas',8))
        c.create_text(ancho-30,alto-26,text='■ DETENER',anchor='e',fill='#b5ff7c',font=('Consolas',8))

    def tick(self):
        self.pendiente=None
        if (not self.habilitado() and not self.manual) or (time.monotonic()>self.vence and not self.editando):self.ocultar();return
        if not self.sincronizada:self.visible=self.objetivo[:min(len(self.objetivo),len(self.visible)+2)]
        self.fase+=1;self.dibujar();self.posicionar()
        self.pendiente=self.raiz.after(25 if len(self.visible)<len(self.objetivo) else 180,self.tick)

    def clic(self,e):
        if e.y<40 and e.x>self.canvas.winfo_width()-50:self.ocultar()
        elif e.y>self.canvas.winfo_height()-42:
            if e.x<140 and self.historial:self.historial()
            elif self.detener:self.detener()

    def ocultar(self):
        if self.pendiente:self.raiz.after_cancel(self.pendiente);self.pendiente=None
        self.editando=False;self.manual=False
        if self.ventana and self.ventana.winfo_exists():self.ventana.withdraw()
