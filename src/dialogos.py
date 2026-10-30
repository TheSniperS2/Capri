"""Conversación compacta junto a Capri, con escritura y glitch transitorio."""
import random
import time
import tkinter as tk
from idiomas import Lienzo as CanvasUI
import os
from tkinter import font as tkfont
from fuentes import FAMILIA

TRANS='#010203'

class Dialogo:
    def __init__(self,raiz,habilitado,enviar=None,historial=None,detener=None,glitch=None):
        self.raiz=raiz;self.habilitado=habilitado;self.enviar=enviar;self.historial=historial;self.detener=detener
        self.glitch=glitch or (lambda:True);self.ventana=None;self.pendiente=None
        self.objetivo='';self.visible='';self.usuario='';self.vence=0;self.fase=0;self.editando=False
        self.estado='ENLACE ABIERTO';self.entrada=None;self.control_entrada=None;self.manual=False;self.alto_canvas=108;self.sincronizada=False
        self.menu=None;self.fin_escritura=False;self.retener=lambda:False
        self.personaje=lambda:False;self.ruta_retrato=None;self.retrato=None;self.punta=80;self.estilo_personaje=None
        self.idioma=lambda:'es'
        self.origen=None
        self.componiendo=False
        # El seguimiento no depende del ritmo de escritura del texto (25/180ms).
        self.raiz.bind('<Configure>',self._seguir_raiz,add='+')

    def _seguir_raiz(self,e):
        if e.widget==self.raiz:self.posicionar((e.x,e.y,e.width,e.height))

    def crear(self):
        if self.ventana is not None and self.ventana.winfo_exists():return
        p=self.ventana=tk.Toplevel(self.raiz);p.title('Capri · Enlace');p.overrideredirect(True);p.attributes('-topmost',True)
        p.configure(bg=TRANS)
        if os.name=='nt':p.wm_attributes('-transparentcolor',TRANS)
        self.canvas=CanvasUI(p,width=364,height=self.alto_canvas,bg=TRANS,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.fuente_pregunta=tkfont.Font(root=p,family=FAMILIA,size=9)
        self.fuente_cuerpo=tkfont.Font(root=p,family=FAMILIA,size=12)
        if self.ruta_retrato:
            try:
                from PIL import Image,ImageTk
                with Image.open(self.ruta_retrato) as im:self.retrato=ImageTk.PhotoImage(im.convert('RGBA').resize((58,58),Image.Resampling.LANCZOS))
            except OSError:pass
        self.canvas.bind('<Button-3>',lambda e:self.menu(e) if self.menu else None)
        p.bind('<Escape>',lambda e:self.detener() if self.detener else self.ocultar())

    def abrir(self):
        self.ocultar();self.manual=True;self.componiendo=True
        if self.control_entrada:self.control_entrada.dar_foco()

    def revisar(self,texto):
        self.estado='REVISA EL DICTADO'
        if self.control_entrada:self.control_entrada.poner(texto)

    def recibir_usuario(self,texto):
        self.componiendo=False
        if not self.habilitado() and not self.manual:return
        self.usuario=texto;self.objetivo='';self.visible='';self.estado='PROCESANDO';self.sincronizada=False
        self.fin_escritura=False
        self.crear();self.vence=time.monotonic()+60;self.ventana.deiconify();self.posicionar()
        if self.pendiente is None:self.tick()

    def enviar_entrada(self):
        if self.control_entrada:self.control_entrada.enviar_actual()

    def mostrar(self,texto,sincronizada=False):
        self.componiendo=False
        if (not self.habilitado() and not self.manual) or not texto:return
        self.crear()
        if sincronizada or not texto.startswith(self.objetivo):self.visible=''
        self.sincronizada=sincronizada
        self.fin_escritura=False
        self.objetivo=texto;self.estado='TRANSMISIÓN';self.vence=time.monotonic()+25
        self.ventana.deiconify();self.posicionar()
        if self.pendiente is None:self.tick()

    def preparar_voz(self,texto,estado='PREPARANDO VOZ'):
        self.mostrar(texto,sincronizada=True);self.estado=estado

    def revelar(self,texto,caracteres):
        if not self.habilitado() and not self.manual:return
        self.objetivo=texto;self.visible=self.objetivo[:max(0,caracteres)]
        self.sincronizada=True;self.estado='HABLANDO';self.vence=time.monotonic()+60
        if self.ventana and self.ventana.winfo_exists():self.dibujar();self.posicionar()

    def terminar_voz(self):
        self.visible=self.objetivo;self.sincronizada=False;self.estado='ENLACE ABIERTO'
        self.fin_escritura=True;self.vence=time.monotonic()+3

    def posicionar(self,origen=None):
        if origen is not None:self.origen=origen
        if not self.ventana or not self.ventana.winfo_exists():return
        if self.ventana.state()=='withdrawn':return
        rx,ry,rw,rh=self.origen or (self.raiz.winfo_x(),self.raiz.winfo_y(),self.raiz.winfo_width(),self.raiz.winfo_height())
        sw=self.raiz.winfo_screenwidth();sh=self.raiz.winfo_screenheight()
        ancho=min(440,sw-16) if self.personaje() else max(280,rw);alto=self.alto_canvas
        if int(float(self.canvas.cget('width')))!=ancho:
            self.canvas.configure(width=ancho);self.dibujar();alto=self.alto_canvas
        x=rx+(rw-ancho)//2
        y=ry-alto-8
        if y<8:
            x=rx-ancho-10
            if x<8:x=rx+rw+8
            y=ry+30
        x=max(8,min(x,sw-ancho-8));y=max(8,min(y,sh-alto-12))
        punta=max(30,min(ancho-35,rx+rw/2-x))
        if punta!=self.punta:
            self.punta=punta
            # Solo cambia la geometría de la punta, sin volver a maquetar texto.
            for tag,desfase in (('globo_personaje',0),('sombra_globo',4)):
                for item in self.canvas.find_withtag(tag):
                    puntos=self.canvas.coords(item)
                    for indice,valor in ((8,punta+17),(10,punta),(12,punta-12)):puntos[indice]=valor+desfase
                    self.canvas.coords(item,*puntos)
        geometria=f'{ancho}x{alto}+{round(x)}+{round(y)}'
        if geometria!=getattr(self,'geometria',None):
            self.ventana.geometry(geometria);self.geometria=geometria

    def dibujar(self):
        c=self.canvas;c.delete('all');ancho=max(280,int(float(c.cget('width'))));modo=self.personaje()
        from idiomas import fuente,texto
        self.fuente_cuerpo.configure(family=fuente(self.idioma()))
        self.fuente_pregunta.configure(family=fuente(self.idioma()))
        if modo!=self.estilo_personaje:self.fuente_cuerpo.configure(weight='bold' if modo else 'normal');self.estilo_personaje=modo
        izquierda=104 if modo else 29;arriba=54 if modo else 76;limite=ancho-izquierda-(25 if modo else 33)
        pregunta=' '.join(self.usuario.split())
        pregunta=(texto('tu',self.idioma())+' > '+pregunta) if pregunta else 'ENLACE PERSONAL'
        if self.fuente_pregunta.measure(pregunta)>limite:
            while pregunta and self.fuente_pregunta.measure(pregunta+'…')>limite:pregunta=pregunta[:-1]
            pregunta+='…'
        escribiendo=len(self.visible)<len(self.objetivo)
        punta=(random.choice('_/-') if self.glitch() else '_') if escribiendo and self.visible else ''
        # Envolver por ancho real, incluyendo palabras largas. Solo la vista
        # compacta muestra las últimas seis líneas; el historial queda completo.
        lineas=['']
        for palabra in (' '.join(self.visible.split())+punta).split(' '):
            candidato=(lineas[-1]+' '+palabra).strip()
            if lineas[-1] and self.fuente_cuerpo.measure(candidato)>limite:lineas.append('')
            for caracter in ((' ' if lineas[-1] else '')+palabra):
                if self.fuente_cuerpo.measure(lineas[-1]+caracter)>limite:lineas.append('')
                lineas[-1]+=caracter
        if len(lineas)>6:
            lineas=lineas[-6:];lineas[0]='…'+lineas[0]
            while self.fuente_cuerpo.measure(lineas[0])>limite:lineas[0]='…'+lineas[0][2:]
        cuerpo=c.create_text(izquierda,arriba,text='\n'.join(lineas),anchor='nw',fill='#edf0fa',font=self.fuente_cuerpo,tags='cuerpo')
        caja=c.bbox(cuerpo)
        # El borde inferior del globo está 24px por encima de la punta.
        # Reservar además 20px reales entre el texto y ese borde.
        alto=max(144 if modo else 120,(caja[3] if caja else 86)+(46 if modo else 32))
        self.alto_canvas=alto;c.configure(height=alto)
        if modo:
            punta=max(30,min(ancho-35,self.punta))
            puntos=[14,8,ancho-24,8,ancho-10,22,ancho-10,alto-24,punta+17,alto-24,punta,alto-5,punta-12,alto-24,10,alto-24,10,21]
            sombra=c.create_polygon(*[v+4 for v in puntos],fill='#bd2147',outline='',tags='sombra_globo')
            fondo=c.create_polygon(*puntos,fill='#120f1d',outline='#dd4262',width=2,tags='globo_personaje')
            c.tag_lower(fondo);c.tag_lower(sombra)
            if self.retrato:
                c.create_rectangle(24,26,86,88,fill='#38121e',outline='#ef446b',width=2)
                c.create_image(26,28,image=self.retrato,anchor='nw',tags='retrato')
            c.create_text(104,29,text='CAPRI',anchor='w',fill='#e8def9',font=(FAMILIA,11,'bold'))
            c.create_rectangle(ancho-125,17,ancho-23,37,fill='#89243f',outline='')
            etiqueta={'GENERANDO RESPUESTA':'PENSANDO','PREPARANDO VOZ':'PREPARANDO','ENLACE ABIERTO':'EN LÍNEA','REVISA EL DICTADO':'REVISAR'}.get(self.estado,self.estado)
            from idiomas import ui
            etiqueta=ui(etiqueta)
            while self.fuente_pregunta.measure(etiqueta)>94:etiqueta=etiqueta[:-2]+'…'
            c.create_text(ancho-74,27,text=etiqueta,fill='#efe5fa',font=(FAMILIA,8,'bold'),tags='estado_globo')
            if not self.visible:
                for i in range(3):
                    x=izquierda+i*12;y=arriba+10
                    c.create_oval(x,y,x+5,y+5,fill='#ffa0b6' if self.fase%3==i else '#702439',outline='',tags='pensando')
            return
        fondo=c.create_polygon(22,9,ancho-22,9,ancho-10,21,ancho-10,alto-24,ancho-22,alto-12,10,alto-12,10,21,
                         fill='#0d111b',outline='#a54459',width=1)
        c.tag_lower(fondo)
        # Inferior izquierda recta; el acento sigue la base y el bisel derecho.
        c.create_line(10,alto-12,ancho-22,alto-12,ancho-10,alto-24,
                      fill='#d64b64',width=1,tags='borde_inferior')
        c.create_rectangle(26,44,80,61,fill='#f2d959',outline='')
        c.create_text(31,53,text='CAPRI',anchor='w',fill='#151822',font=(FAMILIA,10,'bold'))
        c.create_text(92,53,text=self.estado,anchor='w',fill='#80939c',font=(FAMILIA,8))
        c.create_text(29,25,text=pregunta,anchor='w',fill='#8d98a4',font=self.fuente_pregunta,tags='pregunta')
        if escribiendo and self.glitch() and self.fase%9==0:
            y=81+(self.fase*7)%max(1,alto-110);c.create_line(ancho-75,y,ancho-29,y,fill='#ff4267')
        if not self.visible:
            for i in range(3):
                x=izquierda+i*12;y=arriba+10
                c.create_oval(x,y,x+5,y+5,fill='#ffa0b6' if self.fase%3==i else '#702439',outline='',tags='pensando')

    def tick(self):
        self.pendiente=None
        if (not self.habilitado() and not self.manual) or (time.monotonic()>self.vence and not self.sincronizada and not self.retener()):self.ocultar();return
        if not self.sincronizada:self.visible=self.objetivo[:min(len(self.objetivo),len(self.visible)+2)]
        if self.objetivo and self.visible==self.objetivo and not self.sincronizada and not self.fin_escritura:
            self.fin_escritura=True;self.vence=time.monotonic()+3
        self.fase+=1;self.dibujar();self.posicionar()
        self.pendiente=self.raiz.after(25 if len(self.visible)<len(self.objetivo) else 180,self.tick)

    def ocultar(self):
        if self.pendiente:self.raiz.after_cancel(self.pendiente);self.pendiente=None
        self.editando=False;self.manual=False;self.componiendo=False
        if self.ventana and self.ventana.winfo_exists():self.ventana.withdraw()
