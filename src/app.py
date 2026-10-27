"""Capri: compañera de escritorio para Windows y asistente de voz."""
from pathlib import Path
import json
import math
import os
import queue
import random
import subprocess
import sys
import threading
import time
import urllib.error
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageOps
from core import IA, interpretar, ejecutar, HIDDEN
from voz import Microfono, Voz, Atajo, listar_microfonos,normalizar_velocidad,normalizar_volumen

BASE = Path(__file__).resolve().parent
BG = '#0b0c13'
CARD = '#151720'
FG = '#f6eff1'
MUTED = '#9d98ab'
RED = '#ff4267'
GREEN = '#b5ff7c'
TRANS = '#010203'

class Capri:
    def __init__(self, hotkeys=True):
        self.root = tk.Tk()
        self.root.title('Capri')
        try:self.root.iconbitmap(default=str(BASE/'capri.ico'))
        except tk.TclError:pass
        self.root.configure(bg=TRANS)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        if os.name == 'nt': self.root.wm_attributes('-transparentcolor', TRANS)
        self.root.geometry(f'282x334+{max(0,self.root.winfo_screenwidth()-305)}+{max(0,self.root.winfo_screenheight()-410)}')
        self.eventos = queue.Queue()
        self.cerrado = False
        self.estado = 'Lista para ti'
        self.nivel = 0
        self.hablando = False
        self.escuchando = False
        self.ocupada = False
        self.peticion = 0
        self.respuesta_stop = threading.Event()
        self.stream_ticket = None
        self.voz_ticket = None
        self.voz_cursor = 0
        self.descartar_micro = False
        self.micro_stop = threading.Event()
        self.activacion_stop=threading.Event()
        self.activacion_fin=threading.Event()
        self.capturando_activacion=False
        self.activacion_ticket=0
        self.activacion_hilo=None
        self.activacion_reintento=0
        self.activacion_permitida=hotkeys
        self.micro = Microfono(BASE/'modelos')
        self.ia = IA()
        self.cfg = {'voz': True, 'voz_natural': True, 'modelo': '', 'ia': False, 'microfono': None,
                    'reconocimiento':'mixto','voz_perfil':'capri','velocidad_voz':1.0,'volumen_voz':100,'activacion_voz':True}
        try:
            self.cfg.update(json.loads((BASE/'ajustes.json').read_text(encoding='utf8')))
        except (OSError, ValueError): pass
        self.voz = Voz(lambda v: self.eventos.put(('voz', (self.voz.generacion,v))))
        self.fase = 0
        self.drag = None
        self.fotos = []
        self.imagen_ref = None
        self.panel = None
        self.ajustes = None
        self.micro_lista_ticket = 0
        self._cargar_arte()
        self.canvas = tk.Canvas(self.root, bg=TRANS, width=282, height=290, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<ButtonPress-1>', self._inicio_arrastre)
        self.canvas.bind('<B1-Motion>', self._arrastrar)
        self.canvas.bind('<ButtonRelease-1>', self._fin_arrastre)
        self.canvas.bind('<Double-Button-1>', lambda e: self.abrir_chat())
        self.canvas.bind('<Button-3>', self.menu)
        controles = tk.Frame(self.root, bg=BG)
        controles.pack(fill='x', padx=16, pady=(0,12))
        self.b_mic = self.boton(controles, '● Hablar · F8', self.hablar, RED)
        self.b_mic.pack(side='left', fill='x', expand=True)
        self.boton(controles, 'Chat', self.abrir_chat).pack(side='left', padx=(5,0))
        self.boton(controles, '⚙', self.configurar).pack(side='left', padx=(5,0))
        self.atajo = Atajo(lambda: self.eventos.put(('micro', None)), lambda t: self.eventos.put(('aviso', t))) if hotkeys else None
        self.root.bind('<Escape>', lambda e: self.parar())
        self.root.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.root.after(60, self.poll)
        self.root.after(30, self.animar)
        self.root.after(900, lambda: self.mensaje_burbuja('Di «Capri» o pulsa F8 para hablar.' if self.cfg.get('activacion_voz') else 'Estoy aquí. Pulsa F8 para hablar.'))
        if self.cfg.get('ia') and self.cfg.get('modelo'):
            threading.Thread(target=self.preparar_ia,daemon=True).start()

    def preparar_ia(self):
        try:self.ia.preparar(self.cfg.get('modelo'))
        except Exception:pass

    def boton(self, padre, texto, accion, color=None):
        return tk.Button(padre, text=texto, command=accion, bg=color or '#242632', fg='#110c14' if color else FG,
                         activebackground=GREEN if color else '#353746', activeforeground='#110c14' if color else FG,
                         relief='flat', bd=0, padx=11, pady=9, cursor='hand2', font=('Segoe UI', 10, 'bold'))

    def _cargar_arte(self):
        self.fotos = []
        for nombre in ('capri-1.png','capri-2.png','capri-3.png'):
            try:
                with Image.open(BASE/'assets'/nombre) as im:
                    copia = im.convert('RGBA')
                    copia.thumbnail((224, 215), Image.Resampling.LANCZOS)
                    self.fotos.append(copia.copy())
            except (OSError, ValueError): pass

    def _inicio_arrastre(self, e):
        self.drag = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(), time.monotonic())

    def _arrastrar(self, e):
        if not self.drag: return
        x,y,wx,wy,_ = self.drag
        nx = min(max(0, wx + e.x_root - x), max(0,self.root.winfo_screenwidth()-282))
        ny = min(max(0, wy + e.y_root - y), max(0,self.root.winfo_screenheight()-334))
        self.root.geometry(f'+{nx}+{ny}')

    def _fin_arrastre(self, e):
        if self.drag and abs(e.x_root-self.drag[0])+abs(e.y_root-self.drag[1])<6:
            self.abrir_chat()
        self.drag = None

    def menu(self, evento):
        menu = tk.Menu(self.root, tearoff=False, bg=CARD, fg=FG)
        menu.add_command(label='Hablar · F8', command=self.hablar)
        menu.add_command(label='Abrir chat', command=self.abrir_chat)
        menu.add_command(label='Ajustes', command=self.configurar)
        menu.add_separator()
        menu.add_command(label='Cerrar Capri', command=self.cerrar)
        menu.tk_popup(evento.x_root, evento.y_root)

    def animar(self):
        if self.cerrado: return
        self.fase += .065
        c = self.canvas
        c.delete('all')
        color = GREEN if self.escuchando else RED
        dy = math.sin(self.fase)*3
        x = 141
        c.create_polygon(22,19, 249,19, 265,35, 265,256, 249,272, 17,272,17,35, fill=BG, outline=color, width=1)
        c.create_text(32,35, text='CAPRI', anchor='w', fill=FG, font=('Segoe UI', 10, 'bold'))
        c.create_text(250,35, text='●', anchor='e', fill=color, font=('Segoe UI',11))
        if self.fotos:
            # Son ilustraciones originales completas: no se redibuja ni deforma su cara.
            indice = int(time.monotonic()/4)%len(self.fotos) if self.hablando else 0
            self.imagen_ref = ImageTk.PhotoImage(self.fotos[indice])
            c.create_image(x,147+dy, image=self.imagen_ref)
        else:
            c.create_text(141,135, text='Falta descargar la imagen de Capri.\nAbre de nuevo «Abrir Capri».', width=210, justify='center', fill=MUTED, font=('Segoe UI',11))
        if self.escuchando or self.hablando:
            for i in range(22):
                amplitud = (.2+self.nivel)*16 if self.escuchando else (3+9*abs(math.sin(self.fase*3+i*.5)))
                h = max(2, amplitud*abs(math.sin(self.fase*2+i*.7)))
                c.create_line(48+i*8.4,239-h,48+i*8.4,239+h,fill=color,width=3)
        for i in range(5):
            px = 30+((i*47+self.fase*4)%220)
            py = 65+((i*31-self.fase*9)%150)
            if px<50 or px>235: c.create_rectangle(px,py,px+2,py+3,fill=color,outline='')
        if self.ocupada and int(self.fase*5)%16 == 0:
            c.create_line(25,170,258,170,fill=RED,width=2)
        c.create_text(141,258,text=self.estado[:37],fill=color,font=('Segoe UI',9))
        self.root.after(66, self.animar)

    def abrir_chat(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.deiconify(); self.panel.lift(); self.entrada.focus_set(); return
        p = self.panel = tk.Toplevel(self.root)
        p.title('Capri · Conversación')
        p.configure(bg=BG); p.geometry('470x620')
        p.minsize(420,490)
        x = max(0,self.root.winfo_x()-485); y = max(0,min(self.root.winfo_y()-140,self.root.winfo_screenheight()-690))
        p.geometry(f'+{x}+{y}')
        cabeza = tk.Frame(p,bg=BG); cabeza.pack(fill='x',padx=20,pady=(18,8))
        tk.Label(cabeza,text='CAPRI',bg=BG,fg=FG,font=('Segoe UI',20,'bold')).pack(side='left')
        self.boton(cabeza,'Ajustes',self.configurar).pack(side='right')
        tk.Label(p,text='Tu voz, tus instrucciones.',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=21,pady=(0,12))
        self.chat = tk.Text(p,bg=CARD,fg=FG,relief='flat',borderwidth=0,wrap='word',font=('Segoe UI',11),padx=17,pady=15,state='disabled')
        self.chat.pack(fill='both',expand=True,padx=18)
        self.chat.tag_configure('yo',foreground=GREEN,font=('Segoe UI',10,'bold'))
        self.chat.tag_configure('capri',foreground=RED,font=('Segoe UI',10,'bold'))
        self.chat.tag_configure('aviso',foreground=MUTED)
        self.poner_chat('Capri','Hola. Dime «abre Opera y busca…» o pulsa Hablar.\nPara conversar de cualquier tema, activa la IA local en Ajustes.')
        self.subtitulo = tk.StringVar(value='F8 para hablar · Esc para detener')
        tk.Label(p,textvariable=self.subtitulo,bg=BG,fg=MUTED,wraplength=430,font=('Segoe UI',9)).pack(fill='x',padx=20,pady=9)
        caja = tk.Frame(p,bg=BG); caja.pack(fill='x',padx=18,pady=(0,10))
        self.entrada = tk.Entry(caja,bg=CARD,fg=FG,insertbackground=GREEN,relief='flat',font=('Segoe UI',11))
        self.entrada.pack(side='left',fill='both',expand=True,ipady=10)
        self.entrada.bind('<Return>',lambda e:self.enviar_entrada())
        self.boton(caja,'Enviar',self.enviar_entrada,RED).pack(side='left',padx=(7,0))
        pie = tk.Frame(p,bg=BG); pie.pack(fill='x',padx=18,pady=(0,16))
        self.boton(pie,'● Hablar · F8',self.hablar,RED).pack(side='left')
        self.boton(pie,'Detener',self.parar).pack(side='left',padx=7)
        self.boton(pie,'Salir',self.cerrar).pack(side='right')
        p.bind('<Escape>',lambda e:self.parar())
        p.protocol('WM_DELETE_WINDOW',p.withdraw)
        self.entrada.focus_set()

    def poner_chat(self, autor, texto):
        if not self.panel or not self.panel.winfo_exists(): return
        self.chat.configure(state='normal')
        self.chat.insert('end',autor.upper()+'\n','yo' if autor=='Tú' else 'capri')
        self.chat.insert('end',texto+'\n\n')
        self.chat.configure(state='disabled'); self.chat.see('end')

    def mostrar_respuesta_parcial(self,ticket,texto):
        self.chat.configure(state='normal')
        if self.stream_ticket != ticket:
            self.chat.insert('end','CAPRI\n','capri')
            self.chat.mark_set('inicio_respuesta','end-1c')
            self.chat.mark_gravity('inicio_respuesta','left')
            self.stream_ticket=ticket
        self.chat.delete('inicio_respuesta','end-1c')
        self.chat.insert('end',texto)
        self.chat.configure(state='disabled');self.chat.see('end')

    def mensaje_burbuja(self,texto):
        self.estado = texto[:37]

    def enviar_entrada(self):
        texto = self.entrada.get().strip()
        if not texto: return
        self.entrada.delete(0,'end')
        self.enviar(texto)

    def enviar(self, texto):
        if self.ocupada:
            self.estado='Un momento, estoy respondiendo…'; return
        self.detener_activacion()
        self.voz.parar();self.voz_ticket=None;self.voz_cursor=0
        self.abrir_chat()
        self.poner_chat('Tú',texto)
        orden = interpretar(texto)
        if orden and orden.tipo=='silencio':
            self.parar(); return
        if orden and orden.tipo=='velocidad_voz':
            actual=normalizar_velocidad(self.cfg.get('velocidad_voz',1.0))
            nuevo=1.0 if orden.valor=='normal' else normalizar_velocidad(actual+(.15 if orden.valor=='subir' else -.15))
            self.guardar('velocidad_voz',round(nuevo,2))
            respuesta=f'Listo. Velocidad de voz: {nuevo:.2f} veces.'
            self.poner_chat('Capri',respuesta)
            if self.cfg.get('voz'):self.voz.hablar(respuesta,self.cfg.get('voz_natural',True),perfil=self.cfg.get('voz_perfil','capri'),velocidad=nuevo,volumen=self.cfg.get('volumen_voz',100))
            return
        self.ocupada=True; self.estado='Pensando…'
        self.peticion += 1
        ticket = self.peticion
        self.respuesta_stop=threading.Event()
        cancelar=self.respuesta_stop
        if self.panel: self.subtitulo.set('Procesando tu instrucción…')
        def trabajar():
            try:
                if orden:
                    respuesta = ejecutar(orden)
                else:
                    try:
                        respuesta = self.ia.conversar(texto,self.cfg.get('modelo') or None,
                                    al_texto=lambda t:self.eventos.put(('respuesta_parcial',(ticket,t))),cancelar=cancelar)
                    except InterruptedError:return
                    except (TimeoutError,urllib.error.URLError):
                        self.eventos.put(('error',(ticket,'No pude obtener la respuesta del modelo local. Comprueba que Ollama esté abierto y vuelve a intentarlo.')));return
                    except Exception as e:
                        self.eventos.put(('error',(ticket,'La IA local no pudo responder. '+str(e)[:180])));return
                self.eventos.put(('respuesta',(ticket,respuesta)))
            except Exception as e:
                self.eventos.put(('error',(ticket,'No pude completar la orden. '+str(e)[:230])))
        threading.Thread(target=trabajar,daemon=True).start()
        self.root.after(95000,lambda:self._limite_respuesta(ticket))

    def _limite_respuesta(self,ticket):
        if self.ocupada and self.peticion == ticket:
            self.estado='La IA está tardando. Puedes detenerla.'
            if self.panel: self.subtitulo.set('El modelo local está tardando más de lo previsto.')

    def hablar(self):
        if self.escuchando:
            if self.capturando_activacion:self.activacion_fin.set()
            self.micro_stop.set(); self.estado='Terminando de escuchar…'; return
        self.detener_activacion()
        # El micrófono tiene prioridad, incluso mientras se genera una respuesta.
        self.parar()
        self.descartar_micro=False
        self.escuchando=True; self.micro_stop=threading.Event()
        self.estado='Te escucho…'; self.b_mic.configure(text='■ Terminar')
        if self.panel and self.panel.winfo_exists(): self.subtitulo.set('Te escucho. Habla y haz una pausa al terminar.')
        dispositivo = self.cfg.get('microfono')
        def trabajar():
            try:
                texto=self.micro.escuchar(self.micro_stop,lambda t:self.eventos.put(('parcial',t)),lambda n:self.eventos.put(('nivel',n)),
                                         dispositivo=dispositivo,motor=self.cfg.get('reconocimiento','mixto'),
                                         estado=lambda t:self.eventos.put(('micro_estado',t)))
                self.eventos.put(('transcripcion',texto))
            except Exception as e:
                try:
                    (BASE/'diagnostico-microfono.json').write_text(json.dumps(self.micro.diagnostico,ensure_ascii=False,indent=2),encoding='utf8')
                except (OSError,AttributeError):pass
                self.eventos.put(('micro_error','No pude usar el micrófono. '+str(e)[:250]))
        threading.Thread(target=trabajar,daemon=True).start()

    def detener_activacion(self):
        self.activacion_stop.set()
        self.activacion_ticket+=1
        if self.capturando_activacion:
            self.capturando_activacion=False;self.escuchando=False
            self.b_mic.configure(text='● Hablar · F8')

    def mantener_activacion(self):
        if not self.activacion_permitida or not self.cfg.get('activacion_voz') or self.cerrado:return
        # Evitar que su propia voz active otra conversación. F8 siempre interrumpe.
        if self.escuchando or self.hablando or (self.ajustes and self.ajustes.winfo_exists()):return
        if self.activacion_hilo and self.activacion_hilo.is_alive():return
        if time.monotonic()<self.activacion_reintento:return
        self.activacion_stop=threading.Event()
        self.activacion_fin=threading.Event()
        detener=self.activacion_stop
        terminar=self.activacion_fin
        self.activacion_ticket+=1;ticket=self.activacion_ticket
        def esperar():
            try:
                texto=self.micro.esperar_activacion(detener,lambda:self.eventos.put(('nombre_detectado',ticket)),
                         dispositivo=self.cfg.get('microfono'),motor=self.cfg.get('reconocimiento','mixto'),terminar=terminar)
                self.eventos.put(('activacion_resultado',(ticket,texto,None)))
            except Exception as e:self.eventos.put(('activacion_resultado',(ticket,None,str(e))))
        self.activacion_hilo=threading.Thread(target=esperar,name='CapriActivacion',daemon=True)
        self.activacion_hilo.start()

    def parar(self,preservar_activacion=False):
        if not preservar_activacion:self.detener_activacion()
        self.descartar_micro=True
        self.respuesta_stop.set()
        self.micro_stop.set(); self.voz.parar(); self.hablando=False
        self.peticion += 1; self.ocupada=False
        self.estado='Detenida'
        self.voz_ticket=None;self.voz_cursor=0
        if self.stream_ticket is not None and self.panel and self.panel.winfo_exists():
            self.chat.configure(state='normal');self.chat.insert('end','\n\n');self.chat.configure(state='disabled')
            self.stream_ticket=None
        # Una petición ya enviada al modelo termina en su hilo; su texto se conserva.

    def poll(self):
        if self.cerrado:return
        for _ in range(150):
            try:tipo,valor=self.eventos.get_nowait()
            except queue.Empty:break
            if tipo=='nombre_detectado':
                if valor!=self.activacion_ticket:continue
                self.parar(preservar_activacion=True)
                self.escuchando=True;self.capturando_activacion=True;self.descartar_micro=False
                self.estado='Te escucho…';self.b_mic.configure(text='■ Terminar')
                if self.panel and self.panel.winfo_exists():self.subtitulo.set('Te escucho…')
            elif tipo=='activacion_resultado':
                ticket,texto,error=valor
                if ticket!=self.activacion_ticket:continue
                self.escuchando=False;self.capturando_activacion=False;self.b_mic.configure(text='● Hablar · F8')
                if error:
                    self.activacion_reintento=time.monotonic()+30
                    self.estado='Activación por voz no disponible'
                    if self.panel and self.panel.winfo_exists():self.poner_chat('Capri','No pude mantener la escucha de «Capri». Puedes usar Hablar. '+error[:150])
                elif texto:
                    self.recibir_dictado(texto)
                elif texto is not None:
                    self.estado='No escuché una orden. Di «Capri» otra vez.'
            elif tipo=='micro':self.hablar()
            elif tipo=='voz':
                if isinstance(valor,tuple):
                    generacion,valor=valor
                    if generacion!=self.voz.generacion:continue
                if self.escuchando:continue
                if isinstance(valor,bool):self.hablando=valor;self.estado='Hablando…' if valor else ('Respondiendo…' if self.ocupada else 'Lista para ti')
                else:self.estado=valor[:37];self.abrir_chat();self.poner_chat('Capri',valor)
                if self.hablando:self.detener_activacion()
            elif tipo=='nivel':self.nivel=valor
            elif tipo=='micro_estado':
                self.estado=valor[:37]
                if self.panel and self.panel.winfo_exists():self.subtitulo.set(valor)
            elif tipo=='parcial':
                self.estado='Oyendo: '+valor[-27:]
                if self.panel and self.panel.winfo_exists():self.subtitulo.set(valor[-140:])
            elif tipo in ('transcripcion','micro_error'):
                self.escuchando=False;self.nivel=0;self.b_mic.configure(text='● Hablar · F8')
                if self.descartar_micro: self.estado='Lista para ti'
                elif tipo=='transcripcion' and valor:
                    if getattr(self.micro,'confianza_baja',False):
                        self.abrir_chat();self.entrada.delete(0,'end');self.entrada.insert(0,valor)
                        self.estado='Revisa lo que entendí'
                        self.subtitulo.set('No lo entendí con seguridad. Revisa la frase y pulsa Enviar.')
                    else:self.enviar(valor)
                else:
                    self.estado='No te escuché. Pulsa F8 para repetir.' if not valor else 'Micrófono no disponible'
                    self.abrir_chat();self.poner_chat('Capri',valor or 'No entendí la frase. Acércate al micrófono y vuelve a pulsar F8.')
            elif tipo=='respuesta_parcial':
                ticket,texto=valor
                if ticket!=self.peticion:continue
                self.estado='Respondiendo…';self.subtitulo.set('Capri está respondiendo…')
                self.mostrar_respuesta_parcial(ticket,texto)
            elif tipo in ('respuesta','error'):
                ticket,valor=valor
                if ticket != self.peticion:continue
                self.ocupada=False;self.estado='Lista para ti' if tipo=='respuesta' else 'No pude completar la orden'
                if tipo=='error':self.voz.parar();self.voz_ticket=None;self.voz_cursor=0
                if not self.panel or not self.panel.winfo_exists():self.abrir_chat()
                if self.stream_ticket==ticket:
                    self.mostrar_respuesta_parcial(ticket,valor)
                    self.chat.configure(state='normal');self.chat.insert('end','\n\n');self.chat.configure(state='disabled');self.stream_ticket=None
                else:self.poner_chat('Capri',valor)
                self.subtitulo.set('F8 para hablar · Esc para detener')
                if tipo=='respuesta' and self.cfg.get('voz'):
                    self.narrar_respuesta(ticket,valor,final=True)
            elif tipo=='aviso':self.estado=valor[:37]
            elif tipo=='microfonos':
                ticket,lista,error=valor
                if ticket==self.micro_lista_ticket and self.ajustes and self.ajustes.winfo_exists():
                    self.mostrar_microfonos(lista,error)
        self.mantener_activacion()
        self.root.after(60,self.poll)

    def recibir_dictado(self,texto):
        if self.micro.confianza_baja:
            self.abrir_chat();self.entrada.delete(0,'end');self.entrada.insert(0,texto)
            self.estado='Revisa lo que entendí'
            self.subtitulo.set('No estoy segura de la frase. Revísala y pulsa Enviar.')
        else:self.enviar(texto)

    def narrar_respuesta(self,ticket,texto,final=False):
        if not final or not self.cfg.get('voz') or self.escuchando or ticket!=self.peticion:return
        self.voz.hablar(texto,self.cfg.get('voz_natural',True),perfil=self.cfg.get('voz_perfil','capri'),velocidad=self.cfg.get('velocidad_voz',1.0),volumen=self.cfg.get('volumen_voz',100))

    def configurar(self):
        self.detener_activacion()
        if self.ajustes and self.ajustes.winfo_exists():self.ajustes.lift();return
        p=self.ajustes=tk.Toplevel(self.root);p.title('Capri · Ajustes');p.configure(bg=BG)
        p.geometry('540x'+str(min(700,max(480,self.root.winfo_screenheight()-100))))
        contenido=tk.Canvas(p,bg=BG,highlightthickness=0)
        barra=ttk.Scrollbar(p,orient='vertical',command=contenido.yview)
        contenido.configure(yscrollcommand=barra.set)
        barra.pack(side='right',fill='y');contenido.pack(side='left',fill='both',expand=True)
        f=tk.Frame(contenido,bg=BG,padx=24,pady=22)
        ventana=contenido.create_window(0,0,window=f,anchor='nw')
        f.bind('<Configure>',lambda e:contenido.configure(scrollregion=contenido.bbox('all')))
        contenido.bind('<Configure>',lambda e:contenido.itemconfigure(ventana,width=e.width))
        p.bind('<MouseWheel>',lambda e:contenido.yview_scroll(-int(e.delta/120),'units'))
        tk.Label(f,text='A tu manera',font=('Segoe UI',19,'bold'),fg=FG,bg=BG).pack(anchor='w',pady=(0,15))
        tk.Label(f,text='Micrófono',bg=BG,fg=GREEN,font=('Segoe UI',12,'bold')).pack(anchor='w')
        fila=tk.Frame(f,bg=BG);fila.pack(fill='x',pady=(7,5))
        self.micro_combo=ttk.Combobox(fila,state='disabled',font=('Segoe UI',10))
        self.micro_combo.pack(side='left',fill='x',expand=True)
        self.micro_combo.bind('<<ComboboxSelected>>',self.elegir_microfono)
        self.micro_refrescar=self.boton(fila,'Actualizar',self.cargar_microfonos)
        self.micro_refrescar.pack(side='left',padx=(7,0))
        self.micro_estado=tk.StringVar(value='Buscando micrófonos…')
        tk.Label(f,textvariable=self.micro_estado,wraplength=460,justify='left',bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',pady=(0,14))
        tk.Label(f,text='Reconocimiento de voz',bg=BG,fg=GREEN,font=('Segoe UI',12,'bold')).pack(anchor='w')
        motor=ttk.Combobox(f,state='readonly',values=['Mixto · español e inglés','Rápido · Vosk español'],font=('Segoe UI',10))
        motor.current(0 if self.cfg.get('reconocimiento','mixto') in ('preciso','mixto') else 1)
        motor.bind('<<ComboboxSelected>>',lambda e:self.guardar('reconocimiento','mixto' if motor.current()==0 else 'rapido'))
        motor.pack(fill='x',pady=(7,12))
        from reconocimiento import disponible
        if not disponible(BASE/'modelos'):
            tk.Label(f,text='Preciso necesita descargar un modelo local de 148 MB.',wraplength=460,justify='left',bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w')
            self.boton(f,'Preparar reconocimiento preciso',self.preparar_reconocimiento).pack(anchor='w',pady=(5,12))
        for key,texto in [('activacion_voz','Activar al decir «Capri» (escucha local)'),('voz','Responder en voz alta'),('voz_natural','Voz española natural por internet')]:
            var=tk.BooleanVar(value=bool(self.cfg.get(key)))
            tk.Checkbutton(f,text=texto,variable=var,command=lambda k=key,v=var:self.guardar(k,v.get()),bg=BG,fg=FG,selectcolor=CARD,activebackground=BG,activeforeground=FG,font=('Segoe UI',11)).pack(anchor='w',pady=5)
        volumen=normalizar_volumen(self.cfg.get('volumen_voz',100))
        texto_volumen=tk.StringVar(value=f'Volumen de Capri: {volumen}%')
        tk.Label(f,textvariable=texto_volumen,bg=BG,fg=FG,font=('Segoe UI',10)).pack(anchor='w',pady=(10,0))
        self.escala_volumen=tk.Scale(f,from_=0,to=100,resolution=5,orient='horizontal',showvalue=False,
                        bg=BG,fg=FG,troughcolor=CARD,highlightthickness=0,activebackground=RED)
        self.escala_volumen.set(volumen)
        def cambiar_volumen(valor):
            valor=normalizar_volumen(valor)
            texto_volumen.set(f'Volumen de Capri: {valor}%')
            self.guardar('volumen_voz',valor)
        self.escala_volumen.configure(command=cambiar_volumen)
        self.escala_volumen.pack(fill='x',pady=(0,4))
        tk.Label(f,text='Se aplica a la siguiente respuesta. 0% silencia a Capri.',bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w')
        velocidad=normalizar_velocidad(self.cfg.get('velocidad_voz',1.0))
        texto_velocidad=tk.StringVar(value=f'Velocidad de voz: {velocidad:.2f}×')
        tk.Label(f,textvariable=texto_velocidad,bg=BG,fg=FG,font=('Segoe UI',10)).pack(anchor='w',pady=(10,0))
        escala=tk.Scale(f,from_=.8,to=1.8,resolution=.05,orient='horizontal',showvalue=False,
                        bg=BG,fg=FG,troughcolor=CARD,highlightthickness=0,activebackground=RED)
        escala.set(velocidad)
        escala.configure(command=lambda v:texto_velocidad.set(f'Velocidad de voz: {float(v):.2f}×'))
        escala.bind('<ButtonRelease-1>',lambda e:self.guardar('velocidad_voz',escala.get()))
        escala.bind('<KeyRelease>',lambda e:self.guardar('velocidad_voz',escala.get()))
        escala.pack(fill='x',pady=(0,10))
        tk.Label(f,text='El micrófono se reconoce en tu PC. La voz natural es una interpretación sintética, no la actriz de la serie; envía solo las respuestas a Microsoft. Si la desactivas se usa Windows.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',pady=(5,20))
        tk.Label(f,text='Conversación libre',bg=BG,fg=GREEN,font=('Segoe UI',12,'bold')).pack(anchor='w')
        tk.Label(f,text='Ollama ejecuta la IA en tu equipo, sin clave ni pago por uso. La activación descarga un modelo de aproximadamente 2 GB.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',pady=(7,10))
        self.boton(f,'Activar IA local',self.activar_ia,RED).pack(anchor='w')
        self.boton(f,'Vincular playlist de Spotify',self.vincular_playlist).pack(anchor='w',pady=(12,0))
        tk.Label(f,text='No se guarda el audio ni el historial del chat.\nArrastra la imagen para mover a Capri. Clic para chatear.\nF8: micrófono · Esc: detener voz.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',pady=20)
        self.boton(f,'Listo',p.destroy).pack(anchor='e')
        self.cargar_microfonos()

    def cargar_microfonos(self):
        self.micro_lista_ticket+=1
        ticket=self.micro_lista_ticket
        self.micro_combo.configure(state='disabled')
        self.micro_refrescar.configure(state='disabled')
        self.micro_estado.set('Buscando micrófonos…')
        def consultar():
            try:self.eventos.put(('microfonos',(ticket,listar_microfonos(),None)))
            except Exception:self.eventos.put(('microfonos',(ticket,[],'No pude obtener la lista. Conecta el micrófono y pulsa Actualizar.')))
        threading.Thread(target=consultar,daemon=True).start()

    def mostrar_microfonos(self,lista,error=None):
        self.micro_opciones=[None]+lista
        nombres=[m['nombre'] for m in lista]
        etiquetas=['Predeterminado de Windows']+[m['nombre']+(' ('+str(m['indice'])+')' if nombres.count(m['nombre'])>1 else '') for m in lista]
        elegido=self.cfg.get('microfono')
        indice=0
        if elegido:
            coincidencias=[i for i,m in enumerate(self.micro_opciones) if m and m['nombre']==elegido.get('nombre') and m['api']==elegido.get('api')]
            # Una elección anterior por MME sigue siendo válida. Mostramos el mismo
            # micrófono una sola vez, sin cambiar su configuración hasta que lo elija.
            if not coincidencias:
                mismo_nombre=[i for i,m in enumerate(self.micro_opciones) if m and m['nombre']==elegido.get('nombre')]
                if len(mismo_nombre)==1:coincidencias=mismo_nombre
            if coincidencias:
                indice=next((i for i in coincidencias if self.micro_opciones[i]['indice']==elegido.get('indice')),coincidencias[0])
            else:
                self.micro_opciones.append(elegido)
                etiquetas.append('No disponible: '+str(elegido.get('nombre','Micrófono elegido')))
                indice=len(etiquetas)-1
        self.micro_combo.configure(values=etiquetas,state='readonly')
        self.micro_combo.current(indice)
        self.micro_refrescar.configure(state='normal')
        if error:self.micro_estado.set(error)
        elif elegido and not coincidencias:self.micro_estado.set('El micrófono guardado no está conectado. Selecciona otro o actualiza la lista.')
        elif not lista:self.micro_estado.set('No aparecen entradas de audio. Conecta un micrófono y pulsa Actualizar.')
        else:self.micro_estado.set('Elige el tuyo. La elección se guarda y se usa al pulsar F8.')

    def elegir_microfono(self,event=None):
        indice=self.micro_combo.current()
        if indice<0 or indice>=len(self.micro_opciones):return
        elegido=self.micro_opciones[indice]
        try:self.guardar('microfono',elegido)
        except OSError:
            self.micro_estado.set('No pude guardar la elección. Revisa los permisos de la carpeta de Capri.');return
        if self.escuchando:self.parar()
        nombre=elegido['nombre'] if elegido else 'Predeterminado de Windows'
        self.micro_estado.set('Guardado: '+nombre+'. Pulsa F8 para usarlo.')

    def activar_ia(self):
        pythonw=Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw if pythonw.exists() else sys.executable),str(BASE/'activar_ia.py')],creationflags=HIDDEN)

    def preparar_reconocimiento(self):
        lanzador=BASE/'Preparar Capri.pyw'
        if not lanzador.exists():
            messagebox.showinfo('Capri','Abre el archivo «Abrir Capri.pyw» actualizado para preparar Whisper.');return
        pythonw=Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw if pythonw.exists() else sys.executable),str(lanzador)],creationflags=HIDDEN)
        self.cerrar()

    def guardar(self,k,v):
        self.cfg[k]=v
        (BASE/'ajustes.json').write_text(json.dumps(self.cfg,ensure_ascii=False,indent=2),encoding='utf8')
        if k=='voz' and not v:self.voz.parar()
        if k in ('activacion_voz','microfono','reconocimiento'):
            self.detener_activacion();self.activacion_reintento=0

    def vincular_playlist(self):
        nombre=simpledialog.askstring('Playlist de Spotify','¿Con qué nombre quieres pedir esta playlist?',parent=self.ajustes)
        if not nombre:return
        enlace=simpledialog.askstring('Playlist de Spotify','Pega su enlace de Spotify. Puede seguir siendo privada:',parent=self.ajustes)
        if not enlace:return
        from playlists import vincular
        try:vincular(nombre,enlace,BASE)
        except (OSError,ValueError) as e:messagebox.showerror('Playlist de Spotify',str(e),parent=self.ajustes);return
        messagebox.showinfo('Playlist de Spotify','Vinculada. Puedes decir «Capri, pon mi playlist '+nombre+'».',parent=self.ajustes)

    def cerrar(self):
        self.detener_activacion()
        self.cerrado=True;self.respuesta_stop.set();self.micro_stop.set();self.voz.parar()
        if self.atajo:self.atajo.cerrar()
        for pendiente in self.root.tk.splitlist(self.root.tk.call('after','info')):
            try:self.root.after_cancel(pendiente)
            except tk.TclError:pass
        self.root.destroy()

def main():
    mutex=None
    if os.name=='nt':
        import ctypes
        try:ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Capri.Desktop')
        except OSError:pass
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
        k.CreateMutexW.restype=ctypes.c_void_p
        mutex=k.CreateMutexW(None,False,'Local\\CapriDesktopCompanion1')
        if mutex and ctypes.get_last_error()==183:
            root=tk.Tk();root.withdraw();messagebox.showinfo('Capri','Capri ya está abierta. Busca su imagen flotante o pulsa F8.');root.destroy();return
    try:
        app=Capri();app.root.mainloop()
    finally:
        if mutex:
            k.CloseHandle.argtypes=[ctypes.c_void_p];k.CloseHandle(mutex)

if __name__=='__main__':main()
