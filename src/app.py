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
from idiomas import Lienzo as CanvasUI
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageOps
from core import IA, interpretar, ejecutar, HIDDEN
from intenciones import Interprete,requiere_contexto
from voz import Microfono, Voz, Atajo, listar_microfonos,normalizar_velocidad,normalizar_volumen
from idiomas import codigo as codigo_idioma,texto as texto_idioma,conocida as traduccion_conocida
from idiomas import activar as activar_idioma,localizar_widgets,ui

BASE = Path(__file__).resolve().parent
BG = '#10090d'
CARD = '#211018'
FG = '#f6eff1'
MUTED = '#bb929f'
RED = '#ff4267'
GREEN = '#ffb0c3'
TRANS = '#010203'

def limitar_escala(valor):
    try:valor=float(valor)
    except (TypeError,ValueError):return 1.0
    return min(1.6,max(.75,valor)) if math.isfinite(valor) else 1.0

class Capri:
    def __init__(self, hotkeys=True):
        from fuentes import cargar
        cargar(BASE)
        self.root = tk.Tk()
        self.root.title('Capri')
        icono=BASE/'capri.ico'
        if not icono.is_file():icono=BASE.parent/'assets/capri.ico'
        try:self.root.iconbitmap(default=str(icono))
        except tk.TclError:pass
        self.root.configure(bg=TRANS)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        if os.name == 'nt': self.root.wm_attributes('-transparentcolor', TRANS)
        self.root.geometry(f'360x338+{max(0,self.root.winfo_screenwidth()-384)}+{max(0,self.root.winfo_screenheight()-408)}')
        self.eventos = queue.Queue()
        self.cerrado = False
        self.saliendo=False;self.animacion_cierre=bool(hotkeys)
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
        self.narracion_activa=False
        self.boca_activa=False
        self.descartar_micro = False
        self.micro_stop = threading.Event()
        self.activacion_stop=threading.Event()
        self.activacion_fin=threading.Event()
        self.capturando_activacion=False
        self.activacion_ticket=0
        self.activacion_hilo=None
        self.activacion_reintento=0
        self.activacion_lista=False;self.precalentamiento_lanzado=False
        self.activacion_permitida=hotkeys
        self.micro = Microfono(BASE/'modelos')
        self.ia = IA()
        self.interprete = Interprete()
        if hotkeys:
            from puente_opera import iniciar
            iniciar()
        self.cfg = {'voz': True, 'voz_natural': True, 'modelo': '', 'ia': False, 'microfono': None,
                    'reconocimiento':'mixto','modelo_whisper':'base','voz_perfil':'capri','velocidad_voz':1.0,'volumen_voz':100,'activacion_voz':True,'dialogos_escritorio':True,'animaciones':True,'efecto_glitch':True,'escala_avatar':1.0,'intro_inicio':True}
        try:
            self.cfg.update(json.loads((BASE/'ajustes.json').read_text(encoding='utf-8-sig')))
        except (OSError, ValueError): pass
        self.cfg.setdefault('modo_visual','pantalla');self.cfg.setdefault('pasear_personaje',True);self.cfg.setdefault('control_ampliado',False)
        from control_pc import ControlPC
        self.control_pc=ControlPC(lambda:bool(self.cfg.get('control_ampliado')))
        self.entrada_personaje=False;self.ventana_entrada=None;self.entrada_lateral=None;self.transito=None
        self.cfg.setdefault('travesuras',False);self.cfg.setdefault('travesuras_apps',False)
        from travesuras import Travesuras
        self.juego=Travesuras();self.asomo=None
        self.escala_avatar=limitar_escala(self.cfg.get('escala_avatar',1))
        self.intro_activa=bool(hotkeys and self.cfg.get('intro_inicio',True));self.inicio_intro=time.monotonic()
        self.micro.modelo_whisper=self.cfg.get('modelo_whisper','base')
        self.micro.umbral_microfono_db=self.cfg.get('umbral_microfono_db')
        from dialogos import Dialogo
        self.dialogo=Dialogo(self.root,lambda:self.cfg.get('dialogos_escritorio',True),enviar=self.enviar,
                             historial=self.abrir_chat,detener=self.interrumpir,glitch=lambda:self.cfg.get('efecto_glitch',True))
        self.dialogo.retener=lambda:bool(self.control_pc.pendiente and time.monotonic()<self.control_pc.pendiente.vence)
        self.dialogo.personaje=self.es_personaje;self.dialogo.ruta_retrato=icono
        self.dialogo.idioma=lambda:codigo_idioma(self.cfg.get('idioma'))
        self.historial=[];self.respuesta_borrador=''
        self.subtitulo=tk.StringVar(value=self.cfg.get('tecla_hablar','F8')+' para hablar · Esc para detener')
        self.estado='Preparando activación…' if hotkeys and self.cfg.get('activacion_voz') else self.cfg.get('tecla_hablar','F8')+' para hablar'
        self.voz = Voz(lambda v: self.eventos.put(('voz', (self.voz.generacion,v))))
        self.cfg.setdefault('idioma','es')
        activar_idioma(self.cfg['idioma'])
        self.ia.idioma=self.voz.idioma=codigo_idioma(self.cfg['idioma'])
        self.fase = 0
        self.drag = None
        self.fotos = []
        self.imagen_ref = None
        self.panel = None
        self.ajustes = None
        self.micro_lista_ticket = 0
        self._cargar_arte()
        self.fotos_tk=[ImageTk.PhotoImage(im) for im in self.fotos]
        from avatar import Avatar
        ruta_base=BASE/'assets/capri-base-v2.png'
        if not ruta_base.exists() and BASE.name=='src':ruta_base=BASE.parent/'assets/capri-base-v2.png'
        self.avatar=Avatar(ruta_base)
        from companera import Companera
        self.companera=Companera(ruta_base.with_name('capri-personaje-v1.png'))
        self.canvas = CanvasUI(self.root, bg=TRANS, width=360, height=292, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<ButtonPress-1>', self._inicio_arrastre)
        self.canvas.bind('<B1-Motion>', self._arrastrar)
        self.canvas.bind('<ButtonRelease-1>', self._fin_arrastre)
        self.canvas.bind('<Double-Button-1>', lambda e: self.dialogo.abrir())
        self.canvas.bind('<Button-3>', self.menu)
        self.canvas.bind('<Control-MouseWheel>',self.rueda_tamano)
        from entrada import Entrada
        self.entrada_compacta=Entrada(self.root,self.enviar,self.menu)
        self.entrada_compacta.antes_foco=self.mostrar_entrada_personaje
        self.entrada_compacta.pack(fill='x')
        self.entrada_compacta.foco_cambio=lambda foco:setattr(self.dialogo,'editando',foco)
        self.dialogo.entrada=self.entrada_compacta.entrada;self.dialogo.control_entrada=self.entrada_compacta;self.dialogo.menu=self.menu
        self.aplicar_escala(inicial=True)
        if self.intro_activa:self.iniciar_intro()
        self.atajo = Atajo(lambda: self.eventos.put(('micro', None)), lambda t: self.eventos.put(('aviso', t)),self.cfg.get('tecla_hablar','F8')) if hotkeys else None
        self.root.bind('<Escape>', lambda e:self.interrumpir())
        self.root.protocol('WM_DELETE_WINDOW',self.cerrar)
        self.root.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.root.after(60, self.poll)
        self.root.after(30, self.animar)
        if not hotkeys or not self.cfg.get('activacion_voz'):self.precalentar_ia()

    def precalentar_ia(self):
        if not self.precalentamiento_lanzado and self.cfg.get('ia') and self.cfg.get('modelo'):
            self.precalentamiento_lanzado=True
            threading.Thread(target=self.preparar_ia,daemon=True).start()

    def preparar_ia(self):
        try:self.ia.preparar(self.cfg.get('modelo'))
        except Exception:pass

    def boton(self, padre, texto, accion, color=None):
        from ajustes_ui import BotonCyber
        return BotonCyber(padre,text=texto,command=accion,bg=color or '#471528',fg='#160b11' if color else FG,
                          padx=13,pady=9,font=('Chakra Petch',10,'bold'))

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
        if self.es_personaje() and not self.intro_activa:
            self.companera.salto=None;self.companera.soporte=None;self.companera.ancla=None
        self.drag = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(), time.monotonic())

    def _arrastrar(self, e):
        if not self.drag: return
        x,y,wx,wy,_ = self.drag
        nx = min(max(0, wx + e.x_root - x), max(0,self.root.winfo_screenwidth()-self.root.winfo_width()))
        ny = min(max(0, wy + e.y_root - y), max(0,self.root.winfo_screenheight()-self.root.winfo_height()))
        self.root.geometry(f'+{nx}+{ny}')
        if self.es_personaje():self.companera.x=nx;self.companera.y=ny

    def _fin_arrastre(self, e):
        if self.drag and abs(e.x_root-self.drag[0])+abs(e.y_root-self.drag[1])<6:
            if self.es_personaje() and self.juego.atrapame:
                self.drag=None;self.tocar_juego();return
            if not self.es_personaje() and e.y<42*self.escala_avatar and e.x>self.canvas.winfo_width()-36*self.escala_avatar:self.menu(e)
            else:self.entrada_compacta.dar_foco()
        elif self.drag and self.es_personaje():
            self.companera.posar(self.root.winfo_x(),self.root.winfo_y())
        self.drag = None

    def menu(self, evento):
        return self.abrir_menu_radial(evento)

    def cerrar_radial(self):
        radial=getattr(self,'radial',None)
        if radial:radial.cerrar()

    def abrir_menu_radial(self,e):
        from menu_radial import MenuRadial
        self.cerrar_radial()
        estilos=[(nombre,lambda valor=valor:self.guardar('halo_personaje',valor)) for nombre,valor in
                 [('Violeta','violeta'),('Neón','neon'),('Hielo','hielo'),('Rojo','rojo'),('Sin sombra','ninguno')]]
        tamanos=[(f'{n}%',lambda n=n:self.guardar('escala_avatar',n/100)) for n in (75,100,125,150)]
        juegos=[('Atrápame',self.comenzar_juego),('Asomarse',lambda:self.hacer_travesura('asomar')),('Travesura',self.hacer_travesura)]
        voz=[('Hablar',self.hablar),('Activar voz' if not self.cfg.get('voz') else 'Silenciar voz',lambda:self.guardar('voz',not self.cfg.get('voz')))]
        mas=[('Escribir',self.dialogo.abrir),('Repetir intro',self.iniciar_intro),('YouTube',self.conectar_opera),
             ('Reanudar viajes' if not self.cfg.get('pasear_personaje',True) else 'Pausar viajes',lambda:self.guardar('pasear_personaje',not self.cfg.get('pasear_personaje',True))),('Cerrar Capri',self.cerrar)]
        opciones=[('Ajustes',self.configurar),('Chat',self.abrir_chat),('Juegos' if self.es_personaje() else 'Escribir',juegos if self.es_personaje() else self.dialogo.abrir),('Aspecto',self.abrir_aspectos),
                  ('Modo pantalla' if self.es_personaje() else 'Modo personaje',lambda:self.guardar('modo_visual','pantalla' if self.es_personaje() else 'personaje')),('Tamaño',tamanos),('Voz',voz),('Más',mas)]
        self.radial=MenuRadial(self.root,e.x_root,e.y_root,opciones,terminar=lambda:setattr(self,'radial',None),
                               personaje=(self.root.winfo_x(),self.root.winfo_y(),self.companera.ancho if self.es_personaje() else self.root.winfo_width(),self.companera.alto if self.es_personaje() else self.root.winfo_height()))

    def abrir_aspectos(self):
        from ajustes_ui import GaleriaAspectos
        galeria=getattr(self,'galeria_aspectos',None)
        if galeria and galeria.ventana.winfo_exists():galeria.ventana.lift();return
        if not getattr(self.companera,'lienzos',None):self.companera.redimensionar(self.escala_avatar)
        self.galeria_aspectos=GaleriaAspectos(self.root,self.companera.lienzos[0],self.cfg.get('halo_personaje','violeta'),
                                            lambda valor:self.guardar('halo_personaje',valor))

    def rueda_tamano(self,e):
        self.guardar('escala_avatar',round(self.escala_avatar+(.1 if e.delta>0 else -.1),2))
        return 'break'

    def aplicar_escala(self,inicial=False):
        self.escala_avatar=limitar_escala(self.cfg.get('escala_avatar',1))
        if self.avatar.escala!=self.escala_avatar:self.avatar.redimensionar(self.escala_avatar)
        if self.es_personaje():
            self.companera.redimensionar(self.escala_avatar)
            if inicial:self.companera.iniciar()
            self.geometria_personaje=None
            self.dibujar_personaje(mover=False)
            return
        ancho=round(360*self.escala_avatar);alto=round(292*self.escala_avatar)+46
        self.canvas.configure(width=ancho,height=alto-46)
        self.entrada_compacta.configure(width=ancho)
        self.dialogo.control_entrada=self.entrada_compacta;self.dialogo.entrada=self.entrada_compacta.entrada
        x=self.root.winfo_screenwidth()-ancho-24 if inicial else self.root.winfo_x()
        y=self.root.winfo_screenheight()-alto-70 if inicial else self.root.winfo_y()
        x=max(0,min(x,self.root.winfo_screenwidth()-ancho));y=max(0,min(y,self.root.winfo_screenheight()-alto))
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')

    def es_personaje(self):return self.cfg.get('modo_visual')=='personaje'

    def mostrar_entrada_personaje(self):
        if self.es_personaje() and not self.intro_activa:
            if self.ventana_entrada is None or not self.ventana_entrada.winfo_exists():
                from entrada import Entrada
                v=self.ventana_entrada=tk.Toplevel(self.root);v.overrideredirect(True);v.attributes('-topmost',True);v.configure(bg=TRANS)
                if os.name=='nt':v.wm_attributes('-transparentcolor',TRANS)
                self.entrada_lateral=Entrada(v,self.enviar,self.menu);self.entrada_lateral.configure(width=310);self.entrada_lateral.pack()
                self.entrada_lateral.foco_cambio=self.foco_entrada_lateral
                self.entrada_lateral.antes_foco=self.mostrar_entrada_personaje
                v.bind('<Escape>',lambda e:self.interrumpir())
            self.entrada_personaje=True
            x=self.root.winfo_x()-320;y=self.root.winfo_y()+20
            if x<8:x=self.root.winfo_x()+self.companera.ancho+8
            x=max(8,min(x,self.root.winfo_screenwidth()-318));y=max(8,min(y,self.root.winfo_screenheight()-54))
            self.ventana_entrada.geometry(f'310x46+{x}+{y}');self.ventana_entrada.deiconify()
            self.entrada_compacta.pack_forget()
            self.dialogo.control_entrada=self.entrada_lateral;self.dialogo.entrada=self.entrada_lateral.entrada
            return self.entrada_lateral

    def ocultar_entrada_personaje(self):
        self.entrada_personaje=False;self.dialogo.editando=False
        if self.ventana_entrada and self.ventana_entrada.winfo_exists():self.ventana_entrada.withdraw()

    def foco_entrada_lateral(self,foco):
        self.foco_lateral=foco;self.dialogo.editando=foco
        if not foco:self.root.after(150,lambda:self.ocultar_entrada_personaje() if not getattr(self,'foco_lateral',False) else None)

    def dibujar_personaje(self,mover=True):
        p=self.companera
        if self.asomo and time.monotonic()>=self.asomo['hasta'] and not self.transito and not self.escuchando and not self.ocupada:
            destino=self.asomo['volver'];self.asomo=None;self.salto_juego(destino);return
        if mover:p.tick(pausa=bool(getattr(self,'radial',None) or self.asomo or self.drag or self.escuchando or self.hablando or self.ocupada or self.dialogo.editando or self.control_pc.pendiente),
                        pasear=self.cfg.get('pasear_personaje',True))
        if mover and p.salto:
            salto=p.salto;p.salto=None;self.iniciar_transito('salto',salto=salto);self.dibujar_transito();return
        ancho=p.ancho;extra=0
        self.entrada_compacta.pack_forget()
        self.canvas.configure(width=ancho,height=p.alto);self.entrada_compacta.configure(width=ancho)
        geometria=f'{ancho}x{p.alto+extra}+{max(0,round(p.x))}+{max(0,round(p.y))}'
        if geometria!=getattr(self,'geometria_personaje',None):
            self.root.geometry(geometria);self.geometria_personaje=geometria
        p.dibujar(self.canvas,self.hablando,self.boca_activa,glitch=self.cfg.get('efecto_glitch',True) and self.cfg.get('animaciones',True),halo=self.cfg.get('halo_personaje','violeta'))

    def interrumpir(self):
        if self.saliendo:self.cerrar_inmediato();return
        if self.transito:self.finalizar_transito()
        self.control_pc.cancelar();self.parar()
        self.juego.atrapame=False;self.juego.proxima=time.monotonic()+100
        if self.asomo:
            self.asomo=None;self.companera.iniciar()
        if self.es_personaje():
            self.ocultar_entrada_personaje();self.entrada_compacta.pack_forget()

    def juego_ocupada(self):
        return bool(getattr(self,'radial',None) or self.transito or self.intro_activa or self.asomo or self.ocupada or self.escuchando or self.hablando or self.voz_ticket is not None or self.drag or self.dialogo.editando or self.control_pc.pendiente or (self.ajustes and self.ajustes.winfo_exists()))

    def decir_juego(self,texto):
        self.dialogo.usuario='';self.poner_chat('Capri',texto,mostrar=not self.puede_narrar())
        if self.puede_narrar():self.narrar_respuesta(self.peticion,texto,final=True)

    def salto_juego(self,destino=None):
        from ventanas import area_trabajo
        p=self.companera;l,t,r,b=area_trabajo()
        if destino is None:destino=(l+10 if p.x>(l+r)/2 else r-p.ancho-10,b-p.alto)
        salto={'inicio':time.monotonic(),'x':p.x,'y':p.y,'destino':destino,'id':0,'izquierda':destino[0],'lado':None}
        p.soporte=None;self.iniciar_transito('salto',salto=salto)

    def comenzar_juego(self):
        if not self.es_personaje() or self.juego_ocupada():return
        self.juego.comenzar();self.decir_juego('Atrápame tres veces, choom. Haz clic sobre mí cuando aterrice.')

    def tocar_juego(self):
        if self.ocupada or self.escuchando or self.control_pc.pendiente:return
        resultado=self.juego.tocar()
        if resultado=='ganaste':self.decir_juego('Me pillaste, choom. Esta ronda es tuya.')
        elif resultado=='escapar':self.salto_juego()

    def hacer_travesura(self,tipo=None):
        if not self.es_personaje() or self.juego_ocupada():return
        tipo=tipo or self.juego.elegir(self.cfg.get('travesuras_apps',False))
        if tipo in ('pestana','carpeta'):
            if not self.cfg.get('travesuras_apps'):return
            def abrir():
                try:
                    if not self.cfg.get('travesuras_apps'):return
                    from core import Orden
                    respuesta=ejecutar(Orden('pestana') if tipo=='pestana' else Orden('carpeta','Documents'))
                    self.eventos.put(('travesura_resultado',respuesta+' Un pequeño atajo, choom.'))
                except Exception:self.eventos.put(('travesura_resultado','Hoy esa puerta no quiso abrirse. Me quedo aquí contigo.'))
            threading.Thread(target=abrir,daemon=True).start();return
        if tipo=='asomar':
            from ventanas import area_trabajo
            p=self.companera;l,t,r,b=area_trabajo();volver=(l+8 if random.choice((True,False)) else r-p.ancho-8,b-p.alto)
            self.asomo={'hasta':time.monotonic()+4.8,'volver':volver}
            self.salto_juego((volver[0],b-p.alto*.48))
        else:self.salto_juego()

    def iniciar_transito(self,tipo,anterior=None,salto=None):
        self.cerrar_radial()
        if self.transito:self.finalizar_transito()
        self.finalizar_intro();self.ocultar_entrada_personaje();self.dialogo.ocultar()
        s=limitar_escala(self.cfg.get('escala_avatar',1));p=self.companera
        p.ancla=None;p.velocidad_caida=0.
        if p.escala!=s or not p.fotos:p.redimensionar(s)
        origen_personaje=(anterior=='personaje') or tipo=='salto'
        if origen_personaje:
            inicio=((salto['x'] if salto else p.x)+p.ancho/2,(salto['y'] if salto else p.y)+p.alto/2)
            vista=Image.new('RGBA',(320,210));copia=p.originales[0].copy();copia.thumbnail((145,210),Image.Resampling.LANCZOS)
            vista.alpha_composite(copia,((320-copia.width)//2,(210-copia.height)//2))
        else:
            inicio=(self.root.winfo_x()+180*s,self.root.winfo_y()+146*s);vista=self.avatar.vistas[0]
        sw=self.root.winfo_screenwidth();sh=self.root.winfo_screenheight()
        presentacion=tipo!='salto' and self.es_personaje()
        if tipo=='salto':
            fin=(salto['destino'][0]+p.ancho/2,salto['destino'][1]+p.alto/2)
            izquierda=salto.get('lado')=='izquierda' or (not salto.get('lado') and salto['destino'][0]<salto['x'])
            destino_fotos=p.espejos if izquierda else p.fotos
            imagen=destino_fotos[3 if salto.get('id') else 0]
        elif self.es_personaje():
            from ventanas import area_trabajo
            l,t,r,b=area_trabajo();fin=(r-p.ancho/2-25,b-p.alto/2);imagen=(p.espejos if p.direccion<0 else p.fotos)[0]
        else:
            fin=(sw-180*s-24,sh-146*s-116);imagen=self.avatar.fotos[0]
        x=max(0,math.floor(min(inicio[0],fin[0])-310*s));y=max(0,math.floor(min(inicio[1],fin[1])-170*s))
        w=min(sw-x,math.ceil(max(inicio[0],fin[0])+300*s-x));h=min(sh-y,math.ceil(max(inicio[1],fin[1])+170*s-y))
        x=y=0;w=sw;h=sh
        from intro import Fragmentos
        self.transito={'inicio':time.monotonic(),'duracion':.85 if tipo=='salto' else 1.1,'tipo':tipo,'salto':salto,'escala':s,
                      'ruta':(((inicio[0]-x)/s,(inicio[1]-y)/s),((fin[0]-x)/s,(fin[1]-y)/s)),
                      'fragmentos':None,'imagen':imagen,'fin':fin}
        if tipo=='salto':
            from intro import TrasladoTeselas
            from PIL import ImageTk
            origen=ImageTk.getimage(getattr(p,'imagen',None) or p.fotos[0])
            destino=ImageTk.getimage(imagen)
            from companera import con_sombra
            origen=con_sombra(origen,self.cfg.get('halo_personaje','violeta'))
            destino=con_sombra(destino,self.cfg.get('halo_personaje','violeta'))
            self.transito['teselas']=TrasladoTeselas(origen,destino,inicio,fin)
        if tipo!='salto':
            from intro import Transformacion
            from PIL import ImageOps
            saludo=self.preparar_saludo(sw,sh)
            cuerpo=p.lienzos[0]
            if p.direccion<0:cuerpo=ImageOps.mirror(cuerpo)
            from companera import con_sombra
            cuerpo=con_sombra(cuerpo,self.cfg.get('halo_personaje','violeta'))
            clave_cache=(sw,sh,s,p.direccion<0,not presentacion,self.cfg.get('halo_personaje','violeta'))
            if not hasattr(self,'caches_morfosis'):self.caches_morfosis={}
            fotos_cache=self.caches_morfosis.get(clave_cache)
            cantidad=85 if presentacion else 31
            if fotos_cache is not None and (len(fotos_cache)!=cantidad or not all(fotos_cache)):fotos_cache=None
            morfosis=Transformacion(getattr(self.avatar,'vista_maestra',self.avatar.vistas[0]),saludo.original if saludo.original is not None else self.avatar.vistas[0],cuerpo,
                                   inicio if presentacion else fin,fin if presentacion else inicio,sw,sh,s,inversa=not presentacion,fotos=fotos_cache,directa=not presentacion)
            self.cache_morfosis=(clave_cache,morfosis.fotos)
            self.caches_morfosis[clave_cache]=morfosis.fotos
            while len(self.caches_morfosis)>2:self.caches_morfosis.pop(next(iter(self.caches_morfosis)))
            self.transito.update(duracion=2.7 if presentacion else .7,morfosis=morfosis)
        self.ocultar_reubicacion_intro();self.entrada_compacta.pack_forget()
        self.canvas.configure(width=w,height=h);self.root.geometry(f'{w}x{h}+{x}+{y}');self.root.update_idletasks();self.pasar_clics_intro(True)
        self.transito['inicio']=time.monotonic()

    def finalizar_transito(self):
        t=self.transito
        if not t:return
        if t.get('morfosis'):t['morfosis'].detener()
        self.transito=None;self.ocultar_reubicacion_intro();self.pasar_clics_intro(False)
        if t['tipo']=='salto':
            salto=t['salto'];p=self.companera;p.x,p.y=salto['destino'];p.soporte=salto['id'] or None
            p.soporte_dx=p.x-salto.get('izquierda',p.x);p.soporte_lado=salto.get('lado')
            p.direccion=-1 if p.soporte_lado=='izquierda' or (not p.soporte_lado and p.x<salto['x']) else 1;p.quieta_hasta=time.monotonic()+random.uniform(5,9)
            p.estado='sentada' if p.soporte else 'quieta';p.ultimo=time.monotonic()
            p.gracia_fisica=0.;p.proxima_accion=p.ultimo+random.uniform(6,11)
            self.aplicar_escala(inicial=False)
        else:
            self.entrada_compacta.pack(fill='x');self.aplicar_escala(inicial=True)
        if self.dialogo.objetivo and (self.control_pc.pendiente or self.dialogo.sincronizada or self.dialogo.vence>time.monotonic()) and self.dialogo.ventana:
            self.dialogo.ventana.deiconify();self.dialogo.posicionar()
            if self.dialogo.pendiente is None:self.dialogo.tick()

    def restaurar_reubicacion(self):
        if hasattr(self,'intro_alpha'):
            self.root.update_idletasks();self.root.attributes('-alpha',self.intro_alpha);del self.intro_alpha

    def dibujar_transito(self):
        t=self.transito
        if not t:return False
        progreso=(time.monotonic()-t['inicio'])/t['duracion']
        if progreso>=1:self.finalizar_transito();return False
        from intro import dibujar_viaje,VIAJE
        c=self.canvas
        if t.get('morfosis'):
            t['morfosis'].dibujar(c,progreso);self.restaurar_reubicacion();return True
        c.delete('all')
        if t.get('teselas'):
            t['teselas'].dibujar(c,progreso);self.restaurar_reubicacion();return True
        dibujar_viaje(c,VIAJE+(1-VIAJE)*progreso,*t['ruta'],imagen=t['imagen'],fragmentos=t['fragmentos'])
        c.scale('all',0,0,t['escala'],t['escala']);self.restaurar_reubicacion();return True

    def preparar_saludo(self,ancho,alto):
        from intro import Saludo
        ruta=BASE/'assets/capri-saludo-v1.png'
        if not ruta.exists():ruta=BASE.parent/'assets/capri-saludo-v1.png'
        clave=(ancho,alto)
        if getattr(self,'saludo_clave',None)!=clave:
            self.saludo=Saludo(ruta,ancho,alto,solo_fuente=True);self.saludo_clave=clave
        return self.saludo

    def iniciar_intro(self):
        if self.transito:self.finalizar_transito()
        self.pasar_clics_intro(False)
        self.ocultar_reubicacion_intro()
        self.intro_activa=True;self.inicio_intro=time.monotonic();self.dialogo.ocultar()
        self.entrada_compacta.pack_forget();self.intro_en_viaje=False
        self.escala_avatar=min(self.root.winfo_screenwidth()*.82/360,self.root.winfo_screenheight()*.82/292)
        self.avatar.redimensionar(self.escala_avatar)
        self.preparar_fragmentos_intro()
        w=round(360*self.escala_avatar);h=round(292*self.escala_avatar)
        self.intro_centro=((self.root.winfo_screenwidth()-w)//2,(self.root.winfo_screenheight()-h)//2)
        self.canvas.configure(width=w,height=h)
        self.root.geometry(f'{w}x{h}+{self.intro_centro[0]}+{self.intro_centro[1]}')
        self.root.update_idletasks();self.pasar_clics_intro(True);self.inicio_intro=time.monotonic()

    def finalizar_intro(self):
        if not self.intro_activa:return
        self.ocultar_reubicacion_intro()
        self.intro_activa=False
        self.pasar_clics_intro(False)
        self.entrada_compacta.pack(fill='x');self.aplicar_escala(inicial=True)
        self.fragmentos_intro=None

    def ocultar_reubicacion_intro(self):
        # Evitar que Windows traslade durante un instante el último panel pintado.
        if not hasattr(self,'intro_alpha'):self.intro_alpha=float(self.root.attributes('-alpha'))
        self.root.attributes('-alpha',0)
        self.canvas.delete('all');self.root.update_idletasks()

    def preparar_fragmentos_intro(self):
        from intro import Fragmentos
        self.fragmentos_intro=Fragmentos(self.avatar.vistas[0],self.escala_avatar) if self.avatar.vistas else None

    def pasar_clics_intro(self,activar):
        # La estela usa una superficie más amplia, pero deja pasar el ratón.
        if os.name!='nt':return
        import ctypes
        from ctypes import wintypes
        try:
            u=ctypes.windll.user32
            u.GetParent.argtypes=[wintypes.HWND];u.GetParent.restype=wintypes.HWND
            obtener=u.GetWindowLongPtrW;poner=u.SetWindowLongPtrW
            obtener.argtypes=[wintypes.HWND,ctypes.c_int];obtener.restype=ctypes.c_ssize_t
            poner.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_ssize_t];poner.restype=ctypes.c_ssize_t
            hwnd=u.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            if activar:
                if not hasattr(self,'intro_estilo'):self.intro_estilo=obtener(hwnd,-20)
                poner(hwnd,-20,obtener(hwnd,-20)|0x20)
            elif hasattr(self,'intro_estilo'):
                poner(hwnd,-20,self.intro_estilo);del self.intro_estilo
        except (AttributeError,OSError):pass

    def mover_intro(self,progreso):
        from intro import VIAJE
        if progreso<VIAJE:return
        if not self.intro_en_viaje:
            self.ocultar_reubicacion_intro()
            self.intro_en_viaje=True
            inicio=(self.intro_centro[0]+180*self.escala_avatar,self.intro_centro[1]+153*self.escala_avatar)
            self.escala_avatar=limitar_escala(self.cfg.get('escala_avatar',1));self.avatar.redimensionar(self.escala_avatar)
            self.preparar_fragmentos_intro()
            s=self.escala_avatar;sw=self.root.winfo_screenwidth();sh=self.root.winfo_screenheight()
            fin=(sw-180*s-24,sh-132*s-116)
            if self.es_personaje():
                from ventanas import area_trabajo
                l,top,r,b=area_trabajo();fin=(r-self.companera.ancho/2-25,b-self.companera.alto/2)
            x=max(0,math.floor(min(inicio[0],fin[0])-310*s));y=max(0,math.floor(min(inicio[1],fin[1])-170*s))
            w=min(sw-x,math.ceil(max(inicio[0],fin[0])+300*s-x))
            h=min(sh-y,math.ceil(max(inicio[1],fin[1])+170*s-y))
            self.intro_ruta=(((inicio[0]-x)/s,(inicio[1]-y)/s),((fin[0]-x)/s,(fin[1]-y)/s))
            self.canvas.configure(width=w,height=h);self.root.geometry(f'{w}x{h}+{x}+{y}')
            self.pasar_clics_intro(True)

    def actualizar_indicador_voz(self):
        visible=(self.es_personaje() and self.escuchando and not self.intro_activa
                 and not self.transito and not self.saliendo and not self.cerrado)
        ventana=getattr(self,'indicador_voz',None)
        if not visible:
            if ventana is not None:ventana.withdraw()
            return
        if ventana is None:
            ventana=self.indicador_voz=tk.Toplevel(self.root,bg=TRANS)
            ventana.overrideredirect(True);ventana.attributes('-topmost',True)
            if os.name=='nt':ventana.attributes('-transparentcolor',TRANS)
            self.indicador_canvas=CanvasUI(ventana,width=172,height=30,bg=TRANS,highlightthickness=0)
            self.indicador_canvas.pack()
        x=max(0,min(self.root.winfo_screenwidth()-172,self.root.winfo_x()+(self.root.winfo_width()-172)//2))
        y=max(0,self.root.winfo_y()-34)
        ventana.geometry(f'172x30+{x}+{y}');ventana.deiconify()
        c=self.indicador_canvas;c.delete('all')
        c.create_polygon(7,1,165,1,171,7,171,23,165,29,7,29,1,23,1,7,
                         fill='#120d20',outline='#66e3df')
        c.create_text(12,15,anchor='w',text='TE ESCUCHO',fill='#b9fff1',font=('Chakra Petch',9,'bold'))
        nivel=max(0,min(1,self.nivel))
        for i,factor in enumerate((.5,.8,1,.8,.5)):
            h=3+round(17*nivel*factor)
            c.create_rectangle(122+i*8,15-h/2,126+i*8,15+h/2,fill='#72ffd1',outline='',tags='nivel_escucha')

    def animar(self):
        if self.cerrado or self.saliendo: return
        self.entrada_compacta.activacion=bool(self.cfg.get('activacion_voz'))
        inicio_frame=time.perf_counter();self.actualizar_indicador_voz()
        if self.transito and self.dibujar_transito():
            self.root.after(max(1,round(16.667-(time.perf_counter()-inicio_frame)*1000)),self.animar);return
        from intro import DURACION,VIAJE
        progreso=(time.monotonic()-self.inicio_intro)/DURACION
        if self.intro_activa:
            if progreso>=1:self.finalizar_intro()
            else:self.mover_intro(progreso)
        self.fase += .065
        c = self.canvas
        c.delete('all')
        if self.es_personaje() and not self.intro_activa:
            globo_visible=bool(self.dialogo.ventana and self.dialogo.ventana.winfo_exists() and self.dialogo.ventana.state()!='withdrawn')
            evento=self.juego.tick(self.cfg.get('travesuras',False),self.juego_ocupada() or globo_visible,self.cfg.get('travesuras_apps',False))
            if evento:self.hacer_travesura(evento)
            if self.transito:
                self.dibujar_transito();self.root.after(16,self.animar);return
            self.dibujar_personaje()
            self.entrada_compacta.señal(self.nivel,self.escuchando,self.hablando and self.boca_activa)
            if hasattr(self,'intro_alpha'):
                self.root.update_idletasks();self.root.attributes('-alpha',self.intro_alpha);del self.intro_alpha
            self.root.after(16,self.animar);return
        animaciones=self.cfg.get('animaciones',True)
        color=GREEN if self.escuchando else ('#ffc2b5' if self.hablando or self.ocupada or self.voz_ticket is not None or (self.activacion_permitida and self.cfg.get('activacion_voz') and not self.activacion_lista) else '#ed6684')
        from avatar import dibujar_marco
        fase='ESCUCHA' if self.escuchando else ('VOZ' if self.hablando else ('SINTONIZANDO' if self.voz_ticket is not None else ('RECIBIENDO' if self.ocupada else ('CONECTANDO' if self.activacion_permitida and self.cfg.get('activacion_voz') and not self.activacion_lista else ('DI CAPRI' if self.cfg.get('activacion_voz') else self.cfg.get('tecla_hablar','F8'))))))
        dibujar_marco(c,self.fase if animaciones else 0,color,fase,self.nivel,self.avatar.glitch_activo if animaciones else False,self.escala_avatar)
        if self.avatar.fotos:
            self.imagen_ref=self.avatar.imagen(self.hablando and self.boca_activa,glitch=self.cfg.get('efecto_glitch',True)) if animaciones else self.avatar.fotos[0]
            c.create_image(180,160,image=self.imagen_ref)
        elif self.fotos_tk:
            self.imagen_ref=self.fotos_tk[0]
            c.create_image(180,160,image=self.imagen_ref)
        else:
            c.create_text(180,160,text='Preparando imagen de Capri',fill=MUTED,font=('Chakra Petch',11))
        self.entrada_compacta.señal(self.nivel,self.escuchando,self.hablando and self.boca_activa)
        if self.intro_activa:
            from intro import dibujar
            imagen_intro=self.imagen_ref
            if self.avatar.glitches and .36<progreso<.76:imagen_intro=self.avatar.glitches[0][int(progreso*24)%2]
            if self.es_personaje() and progreso>=VIAJE and self.companera.fotos:
                imagen_intro=(self.companera.espejos if self.companera.direccion<0 else self.companera.fotos)[0]
            dibujar(c,progreso,imagen_intro,self.escala_avatar,getattr(self,'intro_ruta',None),self.fragmentos_intro)
        if self.escala_avatar!=1:c.scale('all',0,0,self.escala_avatar,self.escala_avatar)
        if hasattr(self,'intro_alpha'):
            self.root.update_idletasks()
            self.root.attributes('-alpha',self.intro_alpha);del self.intro_alpha
        self.root.after(25 if self.intro_activa else 66, self.animar)

    def abrir_chat(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.deiconify(); self.panel.lift(); self.entrada.focus_set(); return
        p = self.panel = tk.Toplevel(self.root)
        p.title('Capri · Conversación')
        p.configure(bg=BG); p.geometry('470x620')
        p.minsize(420,490)
        x = max(0,self.root.winfo_x()-485); y = max(0,min(self.root.winfo_y()-140,self.root.winfo_screenheight()-690))
        p.geometry(f'+{x}+{y}')
        from ajustes_ui import VentanaCyber,MarcoTransmision,BarraCyber
        self.marco_chat=VentanaCyber(p,'CONVERSACIÓN');contenido=self.marco_chat.cuerpo
        cabeza = tk.Frame(contenido,bg=BG); cabeza.pack(fill='x',padx=20,pady=(18,8))
        tk.Label(cabeza,text='CAPRI',bg=BG,fg=FG,font=('Chakra Petch',20,'bold')).pack(side='left')
        self.boton(cabeza,'Ajustes',self.configurar).pack(side='right')
        tk.Label(contenido,text='Di «Capri» para hablar o escribe una transmisión.',bg=BG,fg=MUTED,font=('Chakra Petch',10)).pack(anchor='w',padx=21,pady=(0,12))
        from idiomas import fuente
        self.marco_historial=MarcoTransmision(contenido,'REGISTRO // TRANSMISIONES',height=240)
        self.marco_historial.pack(fill='both',expand=True,padx=12)
        self.chat = tk.Text(self.marco_historial.cuerpo,height=8,bg='#180d13',fg=FG,relief='flat',borderwidth=0,highlightthickness=0,wrap='word',font=(fuente(self.cfg.get('idioma')),11),padx=5,pady=8,spacing1=0,spacing3=0,selectbackground='#6a2038',selectforeground=FG,state='disabled')
        barra_chat=BarraCyber(self.marco_historial.cuerpo,self.chat.yview)
        self.chat.configure(yscrollcommand=barra_chat.set);barra_chat.pack(side='right',fill='y',padx=(6,0))
        self.chat.pack(side='left',fill='both',expand=True)
        self.chat.tag_configure('yo',foreground=GREEN,font=('Chakra Petch',10,'bold'))
        self.chat.tag_configure('capri',foreground=RED,font=('Chakra Petch',10,'bold'))
        for rol in ('yo','capri'):self.chat.tag_configure(rol,spacing1=8,spacing3=4)
        self.chat.tag_configure('mensaje',spacing3=14)
        self.chat.tag_configure('aviso',foreground=MUTED)
        self.chat.bind('<Configure>',lambda e:self.chat.yview_moveto(1))
        self.pintar_historial()
        tk.Label(contenido,textvariable=self.subtitulo,bg=BG,fg=MUTED,wraplength=430,font=('Chakra Petch',9)).pack(fill='x',padx=20,pady=9)
        self.marco_entrada=MarcoTransmision(contenido,'NUEVA TRANSMISIÓN // ESCRIBE AQUÍ',height=94)
        self.marco_entrada.pack(fill='x',padx=12,pady=(0,8))
        caja=self.marco_entrada.cuerpo
        self.entrada = tk.Entry(caja,bg='#180d13',fg=FG,insertbackground=GREEN,relief='flat',borderwidth=0,highlightthickness=0,font=(fuente(self.cfg.get('idioma')),11),selectbackground='#6a2038',selectforeground=FG)
        self.entrada.pack(side='left',fill='x',expand=True,padx=(2,10),pady=8)
        self.entrada.configure(highlightthickness=1,highlightbackground='#59303e',highlightcolor=RED)
        self.placeholder_entrada=tk.Label(caja,text='Escribe un mensaje…',bg='#180d13',fg=MUTED,anchor='w',font=(fuente(self.cfg.get('idioma')),11))
        def entrar(e=None):
            self.placeholder_entrada.place_forget()
        def salir(e=None):
            if not self.entrada.get():self.placeholder_entrada.place(in_=self.entrada,x=6,rely=.5,anchor='w',width=max(1,self.entrada.winfo_width()-12))
        self.entrada.bind('<Configure>',lambda e:self.placeholder_entrada.place_configure(width=max(1,e.width-12)) if self.placeholder_entrada.winfo_manager()=='place' else None)
        self.placeholder_entrada.bind('<Button-1>',lambda e:self.entrada.focus_set())
        self.entrada.bind('<FocusIn>',entrar);self.entrada.bind('<FocusOut>',salir)
        salir()
        self.entrada.bind('<Return>',lambda e:self.enviar_entrada())
        self.boton(caja,'Enviar',self.enviar_entrada,RED).pack(side='left',padx=(7,0))
        pie = tk.Frame(contenido,bg=BG); pie.pack(fill='x',padx=18,pady=(0,16))
        tk.Label(pie,text='DI «CAPRI»  //  '+self.cfg.get('tecla_hablar','F8')+' PARA HABLAR',bg=BG,fg=GREEN,font=('Chakra Petch',9,'bold')).pack(side='left')
        localizar_widgets(self.root,True)

    def poner_chat(self, autor, texto,mostrar=True):
        if autor=='Capri':texto=ui(texto,self.cfg.get('idioma'))
        if autor=='Capri' and mostrar:self.dialogo.mostrar(texto)
        self.historial.append((autor,texto))
        self.pintar_historial()

    def pintar_historial(self):
        if not self.panel or not self.panel.winfo_exists():return
        self.chat.configure(state='normal')
        self.chat.delete('1.0','end')
        for i,(autor,texto) in enumerate(self.historial):
            if autor=='Capri' and i==len(self.historial)-1 and self.voz_ticket==self.peticion:
                texto=self.dialogo.visible
            if not texto.strip():texto=texto_idioma('preparando',self.cfg.get('idioma'))
            self.chat.insert('end',(texto_idioma('tu',self.cfg.get('idioma')) if autor=='Tú' else autor.upper())+' //\n','yo' if autor=='Tú' else 'capri')
            self.chat.insert('end',texto+'\n','mensaje')
        if self.stream_ticket is not None:
            self.chat.insert('end','CAPRI\n','capri')
            self.chat.insert('end',texto_idioma('preparando',self.cfg.get('idioma')) if self.puede_narrar() or not self.respuesta_borrador else self.respuesta_borrador)
        self.chat.configure(state='disabled'); self.chat.yview_moveto(1)

    def mostrar_respuesta_parcial(self,ticket,texto):
        if self.puede_narrar():self.dialogo.preparar_voz(texto,estado='GENERANDO RESPUESTA')
        else:self.dialogo.mostrar(texto)
        self.stream_ticket=ticket;self.respuesta_borrador=texto
        self.pintar_historial()

    def mensaje_burbuja(self,texto):
        self.estado = texto[:37]

    def enviar_entrada(self):
        texto = self.entrada.get().strip()
        if not texto: return
        self.entrada.delete(0,'end')
        self.enviar(texto)

    def enviar(self, texto,origen='texto'):
        if self.ocupada:
            self.estado='Un momento, estoy respondiendo…'; return False
        self.juego.atrapame=False
        self.finalizar_intro()
        if self.es_personaje():
            self.ocultar_entrada_personaje();self.entrada_compacta.pack_forget()
        self.detener_activacion()
        self.narracion_activa=False;self.voz.parar();self.voz_ticket=None;self.voz_cursor=0
        self.dialogo.recibir_usuario(texto)
        self.poner_chat('Tú',texto)
        orden = interpretar(texto)
        orden = self.interprete.ajustar_orden(texto,orden,bool(self.cfg.get('control_ampliado')))
        from core import normalizar
        juego=normalizar(texto).strip(' .!¡¿?')
        if self.es_personaje():
            if juego in ('juguemos','juega conmigo','vamos a jugar','juguemos a atrapame'):
                self.control_pc.cancelar();self.root.after(80,self.comenzar_juego);return
            if juego in ('asomate','asomate por una esquina','haz una travesura'):
                self.control_pc.cancelar();self.root.after(80,lambda:self.hacer_travesura('asomar' if juego.startswith('asomate') else None));return
            if juego in ('para de jugar','deja de jugar','basta de travesuras'):
                self.guardar('travesuras',False);self.interrumpir();self.decir_juego('Listo, choom. Me porto bien. Por ahora.');return
        if self.cfg.get('control_ampliado'):
            from core import normalizar,Orden
            if normalizar(texto).strip(' .!¡¿?') in ('cancela el apagado','cancelar el apagado','cancela apagado'):
                orden=Orden('equipo_cancelar_apagado')
        if orden and orden.tipo=='silencio':
            self.interrumpir(); return
        if orden and orden.tipo=='velocidad_voz':
            actual=normalizar_velocidad(self.cfg.get('velocidad_voz',1.0))
            nuevo=1.0 if orden.valor=='normal' else normalizar_velocidad(actual+(.15 if orden.valor=='subir' else -.15))
            self.guardar('velocidad_voz',round(nuevo,2))
            respuesta=f'Listo. Velocidad de voz: {nuevo:.2f} veces.'
            idioma=codigo_idioma(self.cfg.get('idioma'))
            if idioma!='es':respuesta={'en':f'Voice speed: {nuevo:.2f} times.','pt':f'Velocidade da voz: {nuevo:.2f} vezes.','ja':f'話す速さを{nuevo:.2f}倍にしたよ。'}[idioma]
            self.poner_chat('Capri',respuesta,mostrar=not self.puede_narrar())
            if self.puede_narrar():self.narrar_respuesta(self.peticion,respuesta,final=True)
            return
        self.ocupada=True; self.estado='Pensando…'
        self.peticion += 1
        ticket = self.peticion
        self.respuesta_stop=threading.Event()
        cancelar=self.respuesta_stop
        idioma=codigo_idioma(self.cfg.get('idioma'))
        if self.panel: self.subtitulo.set('Procesando tu instrucción…')
        def trabajar():
            try:
                resuelta=orden
                pregunta=''
                pendiente_previo=self.control_pc.pendiente
                confirmada=self.control_pc.confirmar(texto)
                if confirmada is not None:
                    if not cancelar.is_set():
                        from core import Orden
                        previo=Orden(pendiente_previo.accion,str(pendiente_previo.ruta or '')) if pendiente_previo else None
                        self.eventos.put(('contexto',(ticket,texto,previo,confirmada,False)))
                        self.eventos.put(('respuesta',(ticket,self.localizar_respuesta(confirmada,idioma,cancelar))))
                    return
                if self.cfg.get('ia') and requiere_contexto(resuelta):
                    if self.cfg.get('control_ampliado'):
                        decision=self.interprete.resolver(texto,self.cfg.get('modelo'),cancelar,control_ampliado=True)
                    else:decision=self.interprete.resolver(texto,self.cfg.get('modelo'),cancelar)
                    resuelta=decision.orden
                    pregunta=decision.pregunta
                if cancelar.is_set():return
                if pregunta:
                    respuesta=pregunta
                    resuelta=None
                elif resuelta:
                    from control_pc import ACCIONES as PC
                    if resuelta.tipo in PC:
                        respuesta=self.control_pc.ejecutar(resuelta.tipo,resuelta.valor)
                        if cancelar.is_set():self.control_pc.cancelar();return
                    else:respuesta = ejecutar(resuelta)
                else:
                    try:
                        self.ia.contexto_acciones=self.interprete.contexto()['turnos']
                        self.ia.control_ampliado=bool(self.cfg.get('control_ampliado'))
                        self.ia.idioma=idioma
                        respuesta = self.ia.conversar(texto,self.cfg.get('modelo') or None,
                                    al_texto=lambda t:self.eventos.put(('respuesta_parcial',(ticket,t))),cancelar=cancelar,
                                    origen=origen)
                    except InterruptedError:return
                    except (TimeoutError,urllib.error.URLError):
                        self.eventos.put(('error',(ticket,texto_idioma('ia_error',idioma))));return
                    except Exception as e:
                        self.eventos.put(('error',(ticket,texto_idioma('ia_error',idioma)+' '+str(e)[:180])));return
                self.eventos.put(('contexto',(ticket,texto,resuelta,respuesta,bool(pregunta))))
                if resuelta or pregunta:respuesta=self.localizar_respuesta(respuesta,idioma,cancelar)
                if cancelar.is_set():return
                self.eventos.put(('respuesta',(ticket,respuesta)))
            except InterruptedError:return
            except Exception as e:
                self.eventos.put(('error',(ticket,texto_idioma('accion_error',idioma)+' '+str(e)[:230])))
        threading.Thread(target=trabajar,daemon=True).start()
        self.root.after(95000,lambda:self._limite_respuesta(ticket))

    def localizar_respuesta(self,respuesta,idioma,cancelar=None):
        conocida=traduccion_conocida(respuesta,idioma)
        if conocida is not None:return conocida
        localizada=ui(respuesta,idioma)
        if localizada!=respuesta:return localizada
        try:
            if not self.cfg.get('ia'):raise RuntimeError('IA local desactivada')
            return self.ia.traducir(respuesta,idioma,self.cfg.get('modelo') or None,cancelar)
        except InterruptedError:raise
        except Exception:
            # Conservar el resultado verdadero si el modelo no puede traducirlo.
            return texto_idioma('sin_traduccion',idioma)+'\n'+texto_idioma('original',idioma)+'\n'+respuesta

    def _limite_respuesta(self,ticket):
        if self.ocupada and self.peticion == ticket:
            self.estado='La IA está tardando. Puedes detenerla.'
            if self.panel: self.subtitulo.set('El modelo local está tardando más de lo previsto.')

    def hablar(self):
        if hasattr(self,'panel_prueba') and not self.panel_prueba.cerrado:self.panel_prueba.stop.set()
        if self.escuchando:
            if self.capturando_activacion:self.activacion_fin.set()
            self.micro_stop.set(); self.estado='Terminando de escuchar…'; return
        self.detener_activacion()
        # El micrófono tiene prioridad, incluso mientras se genera una respuesta.
        self.parar()
        self.descartar_micro=False
        self.escuchando=True; self.micro_stop=threading.Event()
        self.estado='Te escucho…'
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
        self.activacion_lista=False
        self.activacion_ticket+=1
        if self.capturando_activacion:
            self.capturando_activacion=False;self.escuchando=False

    def mantener_activacion(self):
        if self.saliendo:return
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
                         dispositivo=self.cfg.get('microfono'),motor=self.cfg.get('reconocimiento','mixto'),terminar=terminar,
                         nivel=lambda n:self.eventos.put(('activacion_nivel',(ticket,n))),
                         estado=lambda s:self.eventos.put(('activacion_estado',(ticket,s))),
                         lista=lambda:self.eventos.put(('activacion_lista',ticket)))
                self.eventos.put(('activacion_resultado',(ticket,texto,None)))
            except Exception as e:self.eventos.put(('activacion_resultado',(ticket,None,str(e))))
        self.activacion_hilo=threading.Thread(target=esperar,name='CapriActivacion',daemon=True)
        self.activacion_hilo.start()

    def parar(self,preservar_activacion=False):
        self.cerrar_radial()
        if self.transito:self.finalizar_transito()
        self.finalizar_intro()
        self.dialogo.ocultar()
        self.narracion_activa=False;self.boca_activa=False
        if not preservar_activacion:self.detener_activacion()
        self.descartar_micro=True
        self.respuesta_stop.set()
        self.micro_stop.set(); self.voz.parar(); self.hablando=False
        self.peticion += 1; self.ocupada=False
        self.estado='Detenida'
        self.voz_ticket=None;self.voz_cursor=0
        if self.stream_ticket is not None:
            if self.respuesta_borrador:self.historial.append(('Capri',self.respuesta_borrador))
            self.stream_ticket=None;self.respuesta_borrador='';self.pintar_historial()
        self.pintar_historial()
        # Una petición ya enviada al modelo termina en su hilo; su texto se conserva.

    def poll(self):
        if self.cerrado:return
        for _ in range(150):
            try:tipo,valor=self.eventos.get_nowait()
            except queue.Empty:break
            if self.saliendo:
                if tipo=='micro':self.cerrar_inmediato();return
                continue
            if tipo=='activacion_lista':
                if valor!=self.activacion_ticket:continue
                self.activacion_lista=True
                if not self.ocupada and not self.hablando and self.voz_ticket is None:self.estado='Di «Capri» o pulsa '+self.cfg.get('tecla_hablar','F8')
                self.precalentar_ia()
            elif tipo=='nombre_detectado':
                if valor!=self.activacion_ticket:continue
                self.parar(preservar_activacion=True)
                self.escuchando=True;self.capturando_activacion=True;self.descartar_micro=False
                self.estado='Te escucho…'
                if self.panel and self.panel.winfo_exists():self.subtitulo.set('Te escucho…')
            elif tipo=='activacion_resultado':
                ticket,texto,error=valor
                if ticket!=self.activacion_ticket:continue
                self.escuchando=False;self.capturando_activacion=False;self.nivel=0
                self.activacion_lista=False
                if error:
                    self.activacion_reintento=time.monotonic()+30
                    self.estado='Activación por voz no disponible'
                    self.poner_chat('Capri','No pude mantener la escucha de «Capri». Puedes usar Hablar. '+error[:150])
                elif texto:
                    self.recibir_dictado(texto)
                elif texto is not None:
                    self.estado='No escuché una orden. Di «Capri» otra vez.'
                else:
                    self.estado='Di «Capri» o pulsa '+self.cfg.get('tecla_hablar','F8')
            elif tipo=='activacion_nivel':
                ticket,nivel=valor
                if ticket==self.activacion_ticket and self.capturando_activacion:self.nivel=nivel
            elif tipo=='activacion_estado':
                ticket,estado=valor
                if ticket!=self.activacion_ticket:continue
                self.escuchando=False;self.capturando_activacion=False;self.nivel=0
                self.activacion_lista=False
                self.estado=estado
                if self.panel and self.panel.winfo_exists():self.subtitulo.set(estado)
            elif tipo=='micro':self.hablar()
            elif tipo=='travesura_resultado':
                if not self.ocupada and not self.escuchando and not self.hablando:self.decir_juego(valor)
            elif tipo=='voz':
                if isinstance(valor,tuple):
                    generacion,valor=valor
                    if generacion!=self.voz.generacion:continue
                if self.escuchando:continue
                if isinstance(valor,tuple) and valor[0]=='avance_voz':
                    if self.voz_ticket==self.peticion:
                        datos=valor[1];self.dialogo.revelar(*datos[:2])
                        if len(datos)>2:self.boca_activa=datos[2]
                        self.pintar_historial()
                    continue
                if isinstance(valor,bool):
                    anterior=self.hablando;self.hablando=valor;self.boca_activa=valor
                    self.estado='Hablando…' if valor else ('Respondiendo…' if self.ocupada else 'Lista para ti')
                    if valor and self.voz_ticket==self.peticion:self.narracion_activa=True
                    elif not valor and self.narracion_activa:
                        self.dialogo.terminar_voz();self.narracion_activa=False;self.voz_ticket=None
                        self.pintar_historial()
                    if anterior and not valor:self.avatar.sonreir()
                else:self.voz_ticket=None;self.estado=valor[:37];self.poner_chat('Capri',valor)
                if self.hablando:self.detener_activacion()
            elif tipo=='nivel':self.nivel=valor
            elif tipo=='micro_estado':
                self.estado=valor[:37]
                if self.panel and self.panel.winfo_exists():self.subtitulo.set(valor)
            elif tipo=='parcial':
                self.estado='Oyendo: '+valor[-27:]
                if self.panel and self.panel.winfo_exists():self.subtitulo.set(valor[-140:])
            elif tipo in ('transcripcion','micro_error'):
                self.escuchando=False;self.nivel=0
                if self.descartar_micro: self.estado='Lista para ti'
                elif tipo=='transcripcion' and valor:
                    self.recibir_dictado(valor)
                else:
                    self.estado='No te escuché. Pulsa '+self.cfg.get('tecla_hablar','F8')+' para repetir.' if not valor else 'Micrófono no disponible'
                    self.poner_chat('Capri',valor or 'No entendí la frase. Acércate al micrófono y pulsa '+self.cfg.get('tecla_hablar','F8')+'.')
            elif tipo=='respuesta_parcial':
                ticket,texto=valor
                if ticket!=self.peticion:continue
                self.estado='Respondiendo…';self.subtitulo.set('Capri está respondiendo…')
                self.mostrar_respuesta_parcial(ticket,texto)
            elif tipo=='contexto':
                ticket,texto,orden,resultado,aclaracion=valor
                if ticket==self.peticion:self.interprete.registrar(texto,orden,resultado,aclaracion)
            elif tipo in ('respuesta','error'):
                ticket,valor=valor
                if ticket != self.peticion:continue
                self.ocupada=False;self.estado='Lista para ti' if tipo=='respuesta' else 'No pude completar la orden'
                if tipo=='error':self.voz.parar();self.voz_ticket=None;self.voz_cursor=0
                if self.stream_ticket==ticket:
                    self.stream_ticket=None;self.respuesta_borrador=''
                con_voz=tipo=='respuesta' and self.puede_narrar()
                self.poner_chat('Capri',valor,mostrar=not con_voz)
                self.subtitulo.set(self.cfg.get('tecla_hablar','F8')+' para hablar · Esc para detener')
                if con_voz:
                    self.narrar_respuesta(ticket,valor,final=True)
            elif tipo=='aviso':self.estado=valor[:37]
            elif tipo=='microfonos':
                ticket,lista,error=valor
                if ticket==self.micro_lista_ticket and self.ajustes and self.ajustes.winfo_exists():
                    self.mostrar_microfonos(lista,error)
            elif tipo=='modelos_ia':
                ventana,modelos,error=valor
                if self.ajustes is ventana and ventana.winfo_exists():
                    actual=self.cfg.get('modelo','')
                    self.modelo_combo.configure(values=modelos,state='readonly' if modelos else 'disabled')
                    if actual:self.modelo_combo.set(actual)
                    self.modelo_estado.set(error or 'Elige un modelo instalado. Se usa para conversar y entender peticiones.')
        self.mantener_activacion()
        localizar_widgets(self.root)
        self.root.after(60,self.poll)

    def recibir_dictado(self,texto):
        from activacion import quitar_nombre
        sin_nombre=quitar_nombre(texto)
        if sin_nombre is not None:texto=sin_nombre
        if not texto.strip():
            self.estado='Di qué quieres hacer';return
        if self.micro.confianza_baja:
            self.dialogo.revisar(texto)
            self.estado='Revisa lo que entendí'
            self.subtitulo.set('No estoy segura de la frase. Revísala y pulsa Enviar.')
        else:self.enviar(texto,origen='voz')

    def narrar_respuesta(self,ticket,texto,final=False):
        if not final or not self.puede_narrar() or self.escuchando or ticket!=self.peticion:return
        from voz import texto_para_voz
        if not texto_para_voz(texto):
            self.dialogo.mostrar(texto);return
        self.voz_ticket=ticket;self.narracion_activa=False;self.dialogo.preparar_voz(texto)
        self.estado='Preparando voz…'
        self.voz.hablar(texto,self.cfg.get('voz_natural',True),perfil=self.cfg.get('voz_perfil','capri'),velocidad=self.cfg.get('velocidad_voz',1.0),volumen=self.cfg.get('volumen_voz',100))
        self.pintar_historial()

    def puede_narrar(self):return bool(self.cfg.get('voz')) and normalizar_volumen(self.cfg.get('volumen_voz',100))>0

    def configurar(self):
        self.finalizar_intro()
        self.detener_activacion()
        if self.ajustes and self.ajustes.winfo_exists():self.ajustes.lift();return
        p=self.ajustes=tk.Toplevel(self.root);p.title('Capri · Ajustes');p.configure(bg=BG)
        p.bind('<Escape>',lambda e:self.interrumpir())
        p.geometry('800x'+str(min(760,max(560,self.root.winfo_screenheight()-100))));p.minsize(720,560)
        from ajustes_ui import PanelAjustes,SelectorCyber,InterruptorCyber,EscalaCyber,CapturadorTecla
        from ajustes_ui import VentanaCyber
        self.marco_ajustes=VentanaCyber(p,'AJUSTES')
        self.panel_ajustes=ui=PanelAjustes(self.marco_ajustes.cuerpo)
        escritorio=ui.seccion('Escritorio','Forma, tamaño, movimiento y efectos de Capri.')
        micro=ui.seccion('Micrófono','Elige tu entrada, comprueba el nivel y ajusta el reconocimiento local.')
        voz=ui.seccion('Voz','Escucha y compara perfiles sin cambiar tu voz actual hasta elegir uno.')
        ia=ui.seccion('IA y servicios','Modelo local, navegador y música.')
        permisos=ui.seccion('Permisos','Decide qué puede hacer Capri en tu computador.')
        from idiomas import IDIOMAS
        tk.Label(voz,text='Idioma de Capri',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w')
        self.idioma_combo=SelectorCyber(voz,values=[v[0] for v in IDIOMAS.values()])
        self.idioma_combo.current(list(IDIOMAS).index(codigo_idioma(self.cfg.get('idioma'))))
        self.idioma_combo.pack(fill='x',pady=(6,6))
        self.idioma_combo.bind('<<ComboboxSelected>>',lambda e:self.guardar('idioma',list(IDIOMAS)[self.idioma_combo.current()]))
        for ayuda in ('Cambia menús, ajustes, avisos, respuestas y voz. Se conserva tu perfil de voz en español.',
                      'Las conversaciones y traducciones de resultados detallados usan IA local. El reconocimiento de voz mantiene su configuración.'):
            tk.Label(voz,text=ayuda,bg=BG,fg=MUTED,font=('Chakra Petch',9),wraplength=460,justify='left').pack(anchor='w',pady=(0,7))
        f=escritorio
        tk.Label(f,text='Forma de Capri',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w')
        forma=SelectorCyber(f,state='readonly',values=['Pantalla personal','Personaje en el escritorio'],font=('Chakra Petch',10))
        forma.current(1 if self.es_personaje() else 0);forma.pack(fill='x',pady=(6,8))
        forma.bind('<<ComboboxSelected>>',lambda e:self.guardar('modo_visual','personaje' if forma.current() else 'pantalla'))
        paseo=tk.BooleanVar(value=self.cfg.get('pasear_personaje',True))
        InterruptorCyber(f,text='Teletransportarse, explorar ventanas y sujetarse',variable=paseo,command=lambda:self.guardar('pasear_personaje',paseo.get()),
                       bg=BG,fg=FG,selectcolor=CARD,activebackground=BG,font=('Chakra Petch',10)).pack(anchor='w')
        for clave,etiqueta in (('travesuras','Travesuras suaves y apariciones ocasionales'),('travesuras_apps','Permitir que el juego abra una pestaña o Documentos')):
            var=tk.BooleanVar(value=self.cfg.get(clave,False))
            InterruptorCyber(f,text=etiqueta,variable=var,command=lambda k=clave,v=var:self.guardar(k,v.get()),bg=BG,fg=FG,selectcolor=CARD,activebackground=BG,font=('Chakra Petch',10)).pack(anchor='w',pady=2)
        self.boton(f,'Ver aspectos de Capri',self.abrir_aspectos).pack(anchor='w',pady=(8,12))
        f=permisos
        control=tk.BooleanVar(value=self.cfg.get('control_ampliado',False))
        InterruptorCyber(f,text='Activar control ampliado del computador',variable=control,command=lambda:self.guardar('control_ampliado',control.get()),
                       bg=BG,fg=FG,selectcolor=CARD,activebackground=BG,font=('Chakra Petch',10)).pack(anchor='w',pady=(8,3))
        from ajustes_ui import TarjetaInfo
        for titulo,detalle in (
            ('SIEMPRE DISPONIBLE','Conversación, voz, música y sitios web.'),
            ('CON CONTROL AMPLIADO','Gestión de archivos y ventanas con tus permisos de Windows.'),
            ('TÚ CONFIRMAS','Las acciones sensibles piden confirmación. Los borrados van a la Papelera.')):
            TarjetaInfo(f,titulo,detalle).pack(fill='x',pady=6)
        f=escritorio
        tk.Label(f,text='A tu manera',font=('Chakra Petch',19,'bold'),fg=FG,bg=BG).pack(anchor='w',pady=(0,15))
        texto_tamaño=tk.StringVar(value=f'Tamaño de Capri: {round(self.escala_avatar*100)}%')
        tk.Label(f,textvariable=texto_tamaño,bg=BG,fg=GREEN,font=('Chakra Petch',11,'bold')).pack(anchor='w')
        escala_tamaño=EscalaCyber(f,from_=75,to=160,resolution=5,orient='horizontal',bg=BG,fg=FG,troughcolor=CARD,highlightthickness=0)
        escala_tamaño.set(round(self.escala_avatar*100))
        escala_tamaño.configure(command=lambda v:texto_tamaño.set(f'Tamaño de Capri: {round(float(v))}%'))
        escala_tamaño.bind('<ButtonRelease-1>',lambda e:self.guardar('escala_avatar',escala_tamaño.get()/100))
        escala_tamaño.bind('<KeyRelease>',lambda e:self.guardar('escala_avatar',escala_tamaño.get()/100))
        escala_tamaño.pack(fill='x',pady=(0,12))
        f=micro
        tk.Label(voz,text='Tecla para hablar',bg=BG,fg=FG,font=('Chakra Petch',11,'bold')).pack(anchor='w',pady=(0,6))
        self.captura_tecla=CapturadorTecla(voz,self.cfg.get('tecla_hablar','F8'),self.suspender_atajo,self.terminar_captura_tecla)
        self.captura_tecla.pack(fill='x',pady=(0,6))
        tk.Label(voz,text='Haz clic y pulsa una tecla o combinación. Esc cancela.',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w',pady=(0,12))
        tk.Label(f,text='01 // Entrada de audio',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w')
        fila=tk.Frame(f,bg=BG);fila.pack(fill='x',pady=(7,5))
        self.micro_combo=SelectorCyber(fila,state='disabled',font=('Chakra Petch',10))
        self.micro_combo.pack(side='left',fill='x',expand=True)
        self.micro_combo.bind('<<ComboboxSelected>>',self.elegir_microfono)
        self.micro_refrescar=self.boton(fila,'Actualizar',self.cargar_microfonos)
        self.micro_refrescar.pack(side='left',padx=(7,0))
        self.micro_estado=tk.StringVar(value='Buscando micrófonos…')
        tk.Label(f,textvariable=self.micro_estado,wraplength=460,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w',pady=(0,14))
        from prueba_microfono import PanelPrueba
        self.panel_prueba=PanelPrueba(f,self.micro,self.cfg,self.guardar,antes_grabar=self.parar)
        self.panel_prueba.pack(fill='x',pady=(0,18))
        tk.Label(f,text='Reconocimiento de voz',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w')
        motor=SelectorCyber(f,state='readonly',values=['Whisper · español y nombres en inglés','Rápido · Vosk español'],font=('Chakra Petch',10))
        motor.current(0 if self.cfg.get('reconocimiento','mixto') in ('preciso','mixto') else 1)
        motor.bind('<<ComboboxSelected>>',lambda e:self.guardar('reconocimiento','mixto' if motor.current()==0 else 'rapido'))
        motor.pack(fill='x',pady=(7,12))
        from reconocimiento import disponible,modelos_disponibles,elegir_modelo
        self.whisper_opciones=modelos_disponibles(BASE/'modelos') or ['base']
        self.whisper_combo=SelectorCyber(f,state='readonly',values=['Whisper '+m for m in self.whisper_opciones],font=('Chakra Petch',10))
        elegido=elegir_modelo(BASE/'modelos',self.cfg.get('modelo_whisper','base'))
        self.whisper_combo.current(self.whisper_opciones.index(elegido) if elegido in self.whisper_opciones else 0)
        def elegir_whisper(event=None):
            self.guardar('modelo_whisper',self.whisper_opciones[self.whisper_combo.current()])
            self.guardar('reconocimiento','mixto');motor.current(0)
        self.whisper_combo.bind('<<ComboboxSelected>>',elegir_whisper)
        self.whisper_combo.pack(fill='x',pady=(0,4))
        tk.Label(f,text='Para responder antes: Whisper Base. Small prioriza precisión.',wraplength=460,bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w',pady=(2,6))
        tk.Label(f,text='Small usa más memoria y puede tardar más. Base sigue disponible como respaldo.',wraplength=460,bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w',pady=(0,10))
        if not disponible(BASE/'modelos',elegido):
            tk.Label(f,text='Preciso necesita descargar un modelo local de 148 MB.',wraplength=460,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w')
            self.boton(f,'Preparar reconocimiento preciso',self.preparar_reconocimiento).pack(anchor='w',pady=(5,12))
        for key,texto in [('activacion_voz','Activar al decir «Capri» (escucha local)'),('voz','Responder en voz alta'),('voz_natural','Voz natural por internet'),('dialogos_escritorio','Mostrar diálogos progresivos junto a Capri'),('animaciones','Estados de boca y expresiones del avatar'),('efecto_glitch','Interferencias breves de imagen y texto'),('intro_inicio','Intro visual al abrir Capri')]:
            var=tk.BooleanVar(value=bool(self.cfg.get(key)))
            destino=micro if key=='activacion_voz' else (voz if key in ('voz','voz_natural') else escritorio)
            InterruptorCyber(destino,text=texto,variable=var,command=lambda k=key,v=var:self.guardar(k,v.get()),bg=BG,fg=FG,selectcolor=CARD,activebackground=BG,activeforeground=FG,font=('Chakra Petch',11)).pack(anchor='w',pady=5)
        f=voz
        volumen=normalizar_volumen(self.cfg.get('volumen_voz',100))
        texto_volumen=tk.StringVar(value=f'Volumen de Capri: {volumen}%')
        tk.Label(f,textvariable=texto_volumen,bg=BG,fg=FG,font=('Chakra Petch',10)).pack(anchor='w',pady=(10,0))
        self.escala_volumen=EscalaCyber(f,from_=0,to=100,resolution=5,orient='horizontal',showvalue=False,
                        bg=BG,fg=FG,troughcolor=CARD,highlightthickness=0,activebackground=RED)
        self.escala_volumen.set(volumen)
        def cambiar_volumen(valor):
            valor=normalizar_volumen(valor)
            texto_volumen.set(f'Volumen de Capri: {valor}%')
            self.guardar('volumen_voz',valor)
        self.escala_volumen.configure(command=cambiar_volumen)
        self.escala_volumen.pack(fill='x',pady=(0,4))
        tk.Label(f,text='Se aplica a la siguiente respuesta. 0% silencia a Capri.',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w')
        from voz import PERFILES_VOZ
        tk.Label(f,text='Voz de Capri',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w',pady=(12,0))
        perfiles=list(PERFILES_VOZ)
        self.perfil_voz_combo=SelectorCyber(f,state='readonly',values=[PERFILES_VOZ[k][0] for k in perfiles],font=('Chakra Petch',10))
        self.perfil_voz_combo.current(perfiles.index(self.cfg.get('voz_perfil')) if self.cfg.get('voz_perfil') in perfiles else 0)
        self.perfil_voz_combo.bind('<<ComboboxSelected>>',lambda e:self.guardar('voz_perfil',perfiles[self.perfil_voz_combo.current()]))
        self.perfil_voz_combo.pack(fill='x',pady=(6,5))
        self.boton(f,'Escuchar prueba',lambda:self.voz.hablar(texto_idioma('prueba',self.cfg.get('idioma')),True,
                    perfil=self.cfg.get('voz_perfil','capri'),velocidad=self.cfg.get('velocidad_voz',1),volumen=self.cfg.get('volumen_voz',100))).pack(anchor='w')
        velocidad=normalizar_velocidad(self.cfg.get('velocidad_voz',1.0))
        texto_velocidad=tk.StringVar(value=f'Velocidad de voz: {velocidad:.2f}×')
        tk.Label(f,textvariable=texto_velocidad,bg=BG,fg=FG,font=('Chakra Petch',10)).pack(anchor='w',pady=(10,0))
        escala=EscalaCyber(f,from_=.8,to=1.8,resolution=.05,orient='horizontal',showvalue=False,
                        bg=BG,fg=FG,troughcolor=CARD,highlightthickness=0,activebackground=RED)
        escala.set(velocidad)
        escala.configure(command=lambda v:texto_velocidad.set(f'Velocidad de voz: {float(v):.2f}×'))
        escala.bind('<ButtonRelease-1>',lambda e:self.guardar('velocidad_voz',escala.get()))
        escala.bind('<KeyRelease>',lambda e:self.guardar('velocidad_voz',escala.get()))
        escala.pack(fill='x',pady=(0,10))
        tk.Label(f,text='El micrófono se reconoce en tu PC. La voz natural es una interpretación sintética, no la actriz de la serie; envía solo las respuestas a Microsoft. Si la desactivas se usa Windows.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w',pady=(5,20))
        f=ia
        tk.Label(f,text='Conversación libre',bg=BG,fg=GREEN,font=('Chakra Petch',12,'bold')).pack(anchor='w')
        self.modelo_combo=SelectorCyber(f,state='disabled',font=('Chakra Petch',10))
        self.modelo_combo.set(self.cfg.get('modelo',''))
        self.modelo_combo.bind('<<ComboboxSelected>>',lambda e:self.elegir_modelo_ia(self.modelo_combo.get()))
        self.modelo_combo.pack(fill='x',pady=(7,4))
        self.modelo_estado=tk.StringVar(value='Buscando modelos instalados en Ollama…')
        tk.Label(f,textvariable=self.modelo_estado,wraplength=460,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',9)).pack(anchor='w')
        def consultar_modelos():
            try:self.eventos.put(('modelos_ia',(p,self.ia.modelos(),None)))
            except Exception:self.eventos.put(('modelos_ia',(p,[],'Abre Ollama para ver los modelos instalados.')))
        threading.Thread(target=consultar_modelos,daemon=True).start()
        tk.Label(f,text='Ollama ejecuta la IA en tu equipo, sin clave ni pago por uso. La activación descarga un modelo de aproximadamente 2 GB.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',10)).pack(anchor='w',pady=(7,10))
        self.boton(f,'Activar IA local',self.activar_ia,RED).pack(anchor='w')
        self.boton(f,'Vincular playlist de Spotify',self.vincular_playlist).pack(anchor='w',pady=(12,0))
        tk.Label(f,text='No se guarda el audio ni el historial del chat.\nArrastra la imagen para mover a Capri. Clic para chatear.\nTecla configurable en Voz · Esc: detener voz.',wraplength=420,justify='left',bg=BG,fg=MUTED,font=('Chakra Petch',10)).pack(anchor='w',pady=20)
        for widget in (self.micro_combo,self.whisper_combo,self.perfil_voz_combo,self.modelo_combo,motor,forma):widget.configure(style='Capri.TCombobox')
        ui.conectar_rueda()
        localizar_widgets(self.root,True)
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
        else:self.micro_estado.set('Elige tu entrada. Se conserva para las siguientes capturas.')

    def elegir_microfono(self,event=None):
        indice=self.micro_combo.current()
        if indice<0 or indice>=len(self.micro_opciones):return
        elegido=self.micro_opciones[indice]
        if hasattr(self,'panel_prueba'):
            self.panel_prueba.descartar()
        try:self.guardar('microfono',elegido)
        except OSError:
            self.micro_estado.set('No pude guardar la elección. Revisa los permisos de la carpeta de Capri.');return
        if self.escuchando:self.parar()
        nombre=elegido['nombre'] if elegido else 'Predeterminado de Windows'
        self.micro_estado.set('Guardado: '+nombre+'. Se usará en la siguiente captura.')

    def activar_ia(self):
        pythonw=Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw if pythonw.exists() else sys.executable),str(BASE/'activar_ia.py')],creationflags=HIDDEN)

    def preparar_reconocimiento(self):
        lanzador=BASE/'Preparar Capri.pyw'
        if not lanzador.exists():
            messagebox.showinfo('Capri',ui('Abre el archivo «Abrir Capri.pyw» actualizado para preparar Whisper.'));return
        pythonw=Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw if pythonw.exists() else sys.executable),str(lanzador)],creationflags=HIDDEN)
        self.cerrar()

    def guardar(self,k,v):
        if k=='idioma':v=codigo_idioma(v)
        if k=='tecla_hablar':
            from voz import atajo_valido
            if not atajo_valido(v):return
        if k=='escala_avatar':v=limitar_escala(v)
        anterior=self.cfg.get(k)
        self.cfg[k]=v
        if k=='control_ampliado' and not v:self.control_pc.cancelar()
        if k=='modo_visual':
            if v=='personaje' and not self.companera.originales:
                self.cfg[k]='pantalla';self.poner_chat('Capri','Falta el arte del personaje. Actualiza la instalación.');return
            if anterior!=v:
                self.asomo=None;self.juego.atrapame=False;self.iniciar_transito('modo',anterior=anterior)
        archivo=BASE/'ajustes.json'
        try:
            persistido=json.loads(archivo.read_text(encoding='utf-8-sig'))
            if not isinstance(persistido,dict):persistido=dict(self.cfg)
        except (OSError,ValueError):persistido=dict(self.cfg)
        persistido[k]=v
        archivo.write_text(json.dumps(persistido,ensure_ascii=False,indent=2),encoding='utf8')
        if k=='idioma':
            self.interrumpir()
            activar_idioma(v)
            self.ia.idioma=self.voz.idioma=v
            if self.ajustes and self.ajustes.winfo_exists() and hasattr(self,'idioma_combo'):
                from idiomas import IDIOMAS
                self.idioma_combo.current(list(IDIOMAS).index(v))
            if hasattr(self,'caches_morfosis'):self.caches_morfosis.clear()
            if self.panel and self.panel.winfo_exists():
                from idiomas import fuente
                for campo in (self.chat,self.entrada):campo.configure(font=(fuente(v),11))
                for rol in ('yo','capri'):self.chat.tag_configure(rol,font=('Yu Gothic UI' if v=='ja' else 'Chakra Petch',10,'bold'))
                self.pintar_historial()
            localizar_widgets(self.root,True)
        if k=='tecla_hablar' and self.atajo:
            self.atajo.cerrar()
            self.atajo=Atajo(lambda:self.eventos.put(('micro',None)),lambda t:self.eventos.put(('aviso',t)),v)
        if k=='voz' and not v:
            self.voz.parar();self.voz_ticket=None;self.narracion_activa=False
            if self.dialogo.objetivo:self.dialogo.mostrar(self.dialogo.objetivo)
        if k=='dialogos_escritorio' and not v:self.dialogo.ocultar()
        if k=='modelo_whisper':self.micro.modelo_whisper=v
        if k=='umbral_microfono_db':self.micro.umbral_microfono_db=v
        if k=='escala_avatar':
            if self.transito:self.finalizar_transito()
            self.finalizar_intro();self.aplicar_escala()
        if k in ('activacion_voz','microfono','reconocimiento','modelo_whisper'):
            self.detener_activacion();self.activacion_reintento=0

    def suspender_atajo(self):
        self.atajo_suspendido=bool(self.atajo)
        if self.atajo:self.atajo.cerrar();self.atajo=None

    def terminar_captura_tecla(self,tecla):
        try:
            if tecla:self.guardar('tecla_hablar',tecla)
        finally:
            if getattr(self,'atajo_suspendido',False) and not self.cerrado and not self.saliendo:
                self.atajo=Atajo(lambda:self.eventos.put(('micro',None)),lambda t:self.eventos.put(('aviso',t)),self.cfg.get('tecla_hablar','F8'))
            self.atajo_suspendido=False

    def elegir_modelo_ia(self,nombre):
        if nombre not in self.modelo_combo.cget('values'):return
        self.parar()
        self.guardar('modelo',nombre)
        self.guardar('ia',True)
        self.modelo_estado.set('Seleccionado: '+nombre+'. La primera carga puede tardar más.')
        threading.Thread(target=self.preparar_ia,daemon=True).start()

    def vincular_playlist(self):
        nombre=simpledialog.askstring(ui('Playlist de Spotify'),ui('¿Con qué nombre quieres pedir esta playlist?'),parent=self.ajustes)
        if not nombre:return
        enlace=simpledialog.askstring(ui('Playlist de Spotify'),ui('Pega su enlace de Spotify. Puede seguir siendo privada:'),parent=self.ajustes)
        if not enlace:return
        from playlists import vincular
        try:vincular(nombre,enlace,BASE)
        except (OSError,ValueError) as e:messagebox.showerror(ui('Playlist de Spotify'),ui(str(e)),parent=self.ajustes);return
        messagebox.showinfo(ui('Playlist de Spotify'),ui('Vinculada. Puedes decir «Capri, pon mi playlist '+nombre+'».'),parent=self.ajustes)

    def conectar_opera(self):
        from puente_opera import iniciar
        puente=iniciar()
        carpeta=BASE/'integraciones/opera-capri'
        if not carpeta.exists():carpeta=BASE.parent/'integraciones/opera-capri'
        ventana=tk.Toplevel(self.root);ventana.title('Conectar YouTube con Opera');ventana.configure(bg=BG)
        ventana.geometry('570x345');ventana.attributes('-topmost',True)
        texto=('1. Abre el gestor de extensiones de Opera GX.\n'
               '2. Activa Modo desarrollador y elige Cargar extensión descomprimida.\n'
               '3. Selecciona la carpeta que abre el botón de abajo.\n'
               '4. Recarga YouTube e inicia un vídeo. Después puedes usar otra pestaña.\n\n'
               'La extensión solo accede a YouTube y a la conexión local con Capri.\n'
               'No lee otras páginas, contraseñas ni archivos.')
        tk.Label(ventana,text=texto,bg=BG,fg=FG,font=('Chakra Petch',11),justify='left',wraplength=535).pack(padx=18,pady=16)
        fila=tk.Frame(ventana,bg=BG);fila.pack()
        def gestor():
            from core import abrir_opera
            try:abrir_opera(pagina='opera://extensions')
            except OSError as e:messagebox.showerror('Opera GX',ui(str(e)),parent=ventana)
        tk.Button(fila,text='Abrir gestor de Opera',command=gestor).pack(side='left',padx=6)
        tk.Button(fila,text='Abrir carpeta de extensión',command=lambda:os.startfile(str(carpeta))).pack(side='left',padx=6)
        estado=tk.StringVar()
        tk.Label(ventana,textvariable=estado,bg=BG,fg=GREEN,font=('Chakra Petch',11),wraplength=530).pack(pady=16)
        def actualizar():
            if not ventana.winfo_exists():return
            estado.set(puente.error or ('Conectada con YouTube; puedes usar otra pestaña.' if puente.conectado() else 'Esperando la extensión y una pestaña de YouTube…'))
            ventana.after(700,actualizar)
        actualizar()

    def cerrar(self):
        if self.animacion_cierre and self.cfg.get('animaciones',True) and not self.saliendo:
            self.iniciar_despedida();return
        self.cerrar_inmediato()

    def iniciar_despedida(self):
        from despedida import Despedida
        self.saliendo=True;self.cerrar_radial();self.dialogo.ocultar();self.ocultar_entrada_personaje()
        self.actualizar_indicador_voz()
        self.respuesta_stop.set();self.micro_stop.set();self.detener_activacion();self.voz.parar()
        if self.transito and self.transito.get('morfosis'):self.transito['morfosis'].detener()
        self.transito=None;self.intro_activa=False
        origen=(self.root.winfo_x()+self.root.winfo_width()/2,self.root.winfo_y()+self.root.winfo_height()/2)
        imagen=getattr(self.companera,'imagen',None) if self.es_personaje() else self.imagen_ref
        if imagen is None:
            fotos=self.companera.fotos if self.es_personaje() else self.avatar.fotos
            if fotos:imagen=fotos[0]
        sw=self.root.winfo_screenwidth();sh=self.root.winfo_screenheight()
        self.salida=Despedida(sw,sh,origen,imagen);self.inicio_salida=time.monotonic()
        self.ocultar_reubicacion_intro();self.entrada_compacta.pack_forget()
        self.canvas.configure(width=sw,height=sh);self.root.geometry(f'{sw}x{sh}+0+0');self.pasar_clics_intro(True)
        self.pintar_despedida()

    def pintar_despedida(self):
        from despedida import DURACION
        if self.cerrado:return
        p=(time.monotonic()-self.inicio_salida)/DURACION
        if p>=1:self.cerrar_inmediato();return
        self.salida.dibujar(self.canvas,p);self.restaurar_reubicacion()
        self.root.after(16,self.pintar_despedida)

    def cerrar_inmediato(self):
        if self.cerrado:return
        if self.transito and self.transito.get('morfosis'):self.transito['morfosis'].detener()
        self.cerrar_radial()
        if self.activacion_permitida:
            from puente_opera import cerrar
            cerrar()
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
            root=tk.Tk();root.withdraw();messagebox.showinfo('Capri','Capri ya está abierta. Busca su imagen flotante.');root.destroy();return
    try:
        app=Capri();app.root.mainloop()
    finally:
        if mutex:
            k.CloseHandle.argtypes=[ctypes.c_void_p];k.CloseHandle(mutex)

if __name__=='__main__':main()
