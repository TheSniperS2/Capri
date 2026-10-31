"""Panel de enlace y catálogo visual del personaje."""
from tema_ui import tk
from tema_ui import LienzoUI as CanvasUI
from tkinter import ttk
from PIL import Image,ImageTk,ImageDraw
from fuentes import FAMILIA

FONDO='#10090d';TARJETA='#211018';TEXTO='#fff0f3';SUAVE='#bb929f';ACENTO='#ff4267';VERDE='#ffb1c2'

def separar_bordes(ventana,margen=32):
    """Respeta la barra de tareas y deja aire alrededor de las ventanas auxiliares."""
    from companera import area_trabajo
    ventana.update_idletasks()
    l,t,r,b=area_trabajo()
    w,h=ventana.winfo_width(),ventana.winfo_height()
    x=max(l+margen,min(ventana.winfo_x(),r-w-margen))
    y=max(t+margen,min(ventana.winfo_y(),b-h-margen))
    ventana.geometry(f'+{x}+{y}')

class VentanaCyber:
    """Marco angular, arrastrable y sin la decoración estándar de Windows."""
    def __init__(self,ventana,titulo,cerrar=None):
        import os
        self.ventana=ventana;self.titulo=titulo;self.cerrar=cerrar or ventana.destroy;self.drag=None;self.resize=None
        ventana.overrideredirect(True);ventana.configure(bg='#010203');ventana.attributes('-topmost',True)
        if os.name=='nt':ventana.attributes('-transparentcolor','#010203')
        self.canvas=CanvasUI(ventana,bg='#010203',highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.cuerpo=tk.Frame(self.canvas,bg=FONDO)
        self.item=self.canvas.create_window(14,50,window=self.cuerpo,anchor='nw')
        self.canvas.bind('<Configure>',self.dibujar)
        self.canvas.bind('<ButtonPress-1>',self.iniciar);self.canvas.bind('<B1-Motion>',self.mover)
        ventana.bind('<Escape>',lambda e:self.cerrar(),add='+')
        self.dibujar()
        separar_bordes(ventana)
        from ventanas import registrar_apoyo
        registrar_apoyo(ventana)

    def dibujar(self,e=None):
        c=self.canvas;w=max(100,c.winfo_width());h=max(100,c.winfo_height());c.delete('chrome')
        c.create_polygon(16,1,w-16,1,w-1,16,w-1,h-16,w-16,h-1,1,h-1,1,16,
                         fill=FONDO,outline='#b72e4e',width=2,tags='chrome')
        c.create_polygon(17,4,w-17,4,w-4,17,w-4,38,4,38,4,17,fill='#35101d',outline='',tags='chrome')
        c.create_text(22,21,text='CAPRI // '+self.titulo,anchor='w',fill='#ffbdca',font=(FAMILIA,10,'bold'),tags='chrome')
        c.create_polygon(w-59,8,w-20,8,w-12,16,w-12,32,w-59,32,fill='#5e1a30',outline='',tags='chrome')
        c.create_line(w-39,16,w-31,24,fill=TEXTO,width=2,tags='chrome')
        c.create_line(w-39,24,w-31,16,fill=TEXTO,width=2,tags='chrome')
        c.create_line(14,40,w-14,40,fill='#5d2134',tags='chrome')
        c.create_line(18,h-8,min(w-30,150),h-8,fill='#f60031',width=3,tags='chrome')
        c.create_line(w-23,h-9,w-10,h-22,fill='#ff829e',width=2,tags='chrome')
        c.itemconfigure(self.item,width=max(1,w-28),height=max(1,h-68));c.tag_lower('chrome')

    def iniciar(self,e):
        self.drag=None;self.resize=None
        if e.y>self.canvas.winfo_height()-28 and e.x>self.canvas.winfo_width()-32:
            self.resize=(e.x_root,e.y_root,self.ventana.winfo_width(),self.ventana.winfo_height());return
        if e.y>37:return
        if e.x>self.canvas.winfo_width()-62:self.cerrar();return
        self.drag=(e.x_root,e.y_root,self.ventana.winfo_x(),self.ventana.winfo_y())

    def mover(self,e):
        if self.resize:
            x,y,w,h=self.resize;minw,minh=self.ventana.minsize()
            w=max(minw,min(self.ventana.winfo_screenwidth()-self.ventana.winfo_x(),w+e.x_root-x))
            h=max(minh,min(self.ventana.winfo_screenheight()-self.ventana.winfo_y(),h+e.y_root-y))
            self.ventana.geometry(f'{w}x{h}');return
        if not self.drag:return
        x,y,a,b=self.drag;w=self.ventana.winfo_width();h=self.ventana.winfo_height()
        a=max(0,min(self.ventana.winfo_screenwidth()-w,a+e.x_root-x))
        b=max(0,min(self.ventana.winfo_screenheight()-h,b+e.y_root-y))
        self.ventana.geometry(f'+{a}+{b}')

class PanelAjustes:
    def __init__(self,ventana):
        self.ventana=ventana;self.secciones={};self.vistas={};self.botones={};self.barras={};self.actual=None
        self.tag_rueda='CapriRueda'+str(id(self))
        ventana.bind_class(self.tag_rueda,'<MouseWheel>',self.rueda)
        from tema_ui import EstiloUI
        self.estilo=estilo=EstiloUI(ventana)
        estilo.theme_use('clam')
        estilo.configure('Capri.TCombobox',padding=7,font=(FAMILIA,10),fieldbackground=TARJETA,
                         background='#421327',foreground=TEXTO,arrowcolor=ACENTO,bordercolor='#7b293e')
        estilo.map('Capri.TCombobox',fieldbackground=[('readonly',TARJETA)],foreground=[('readonly',TEXTO)],
                   selectbackground=[('readonly','#591930')],selectforeground=[('readonly',TEXTO)])
        estilo.configure('TButton',background='#421327',foreground=TEXTO,padding=6,font=(FAMILIA,9,'bold'),borderwidth=0)
        estilo.map('TButton',background=[('active','#7b293e')],foreground=[('disabled','#83636b')])
        estilo.configure('TCheckbutton',background=TARJETA,foreground=TEXTO,font=(FAMILIA,9))
        estilo.map('TCheckbutton',background=[('active',TARJETA)],foreground=[('active',VERDE)])
        estilo.configure('Capri.Vertical.TScrollbar',background='#7b293e',troughcolor=FONDO,
                         arrowcolor=ACENTO,bordercolor=FONDO)
        cabecera=CanvasUI(ventana,height=72,bg=FONDO,highlightthickness=0)
        cabecera.pack(fill='x')
        def pintar_cabecera(e):
            cabecera.delete('all');w=e.width
            cabecera.create_polygon(12,4,w-28,4,w-12,20,w-12,62,12,62,fill='#261019',outline='')
            cabecera.create_text(28,25,text='ENLACE PERSONAL',anchor='w',fill=TEXTO,font=(FAMILIA,17,'bold'))
            cabecera.create_text(28,47,text='AJUSTES DEL CONSTRUCTO',anchor='w',fill=ACENTO,font=(FAMILIA,9))
            cabecera.create_line(w-120,47,w-28,47,fill='#ef4668',width=2)
        cabecera.bind('<Configure>',pintar_cabecera)
        self.titulo=tk.StringVar();self.detalle=tk.StringVar()
        cuerpo=tk.Frame(ventana,bg=FONDO);cuerpo.pack(fill='both',expand=True)
        self.lateral=tk.Frame(cuerpo,bg='#190d13',width=172);self.lateral.pack(side='left',fill='y',padx=(12,0),pady=12)
        self.lateral.pack_propagate(False)
        tk.Label(self.lateral,text='CONFIGURACIÓN',bg='#190d13',fg=VERDE,font=(FAMILIA,10,'bold')).pack(anchor='w',padx=16,pady=(16,12))
        self.contenedor=tk.Frame(cuerpo,bg=FONDO);self.contenedor.pack(side='left',fill='both',expand=True,padx=16,pady=12)
        tk.Label(self.contenedor,textvariable=self.titulo,bg=FONDO,fg=TEXTO,font=(FAMILIA,18,'bold')).pack(anchor='w')
        tk.Label(self.contenedor,textvariable=self.detalle,bg=FONDO,fg=SUAVE,font=(FAMILIA,9),wraplength=490,justify='left').pack(anchor='w',pady=(4,12))
        self.zona=tk.Frame(self.contenedor,bg=FONDO);self.zona.pack(fill='both',expand=True)
        pie=tk.Frame(ventana,bg=FONDO);pie.pack(fill='x',padx=12,pady=(0,6))
        tk.Frame(pie,bg='#542333',height=1).pack(fill='x',pady=(0,8))
        tk.Label(pie,text='● GUARDADO AUTOMÁTICO',bg=FONDO,fg=VERDE,font=(FAMILIA,9)).pack(side='left',padx=10,pady=10)
        BotonCyber(pie,text='VOLVER AL ESCRITORIO',command=ventana.winfo_toplevel().destroy,bg='#4b1427',fg=TEXTO,
                  activebackground=ACENTO,relief='flat',font=(FAMILIA,9,'bold'),padx=15,pady=8).pack(side='right',padx=16,pady=8)
        ventana.winfo_toplevel().bind('<Map>',lambda e:self.conectar_rueda(e.widget),add='+')

    def seccion(self,nombre,descripcion):
        exterior=tk.Frame(self.zona,bg=FONDO)
        lienzo=CanvasUI(exterior,bg=FONDO,highlightthickness=0)
        barra=BarraCyber(exterior,lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set);lienzo.pack(side='left',fill='both',expand=True)
        interior=tk.Frame(lienzo,bg=FONDO,padx=8,pady=8)
        item=lienzo.create_window(0,0,window=interior,anchor='nw')
        interior.bind('<Configure>',lambda e:self.refrescar(nombre))
        def adaptar(e):lienzo.itemconfigure(item,width=e.width);self.refrescar(nombre)
        lienzo.bind('<Configure>',adaptar)
        boton=BotonCyber(self.lateral,text=nombre,command=lambda:self.mostrar(nombre),
                        bg='#190d13',fg=SUAVE,activebackground='#421327',activeforeground=TEXTO,
                        relief='flat',font=(FAMILIA,11,'bold'),padx=16,pady=13)
        boton.pack(fill='x',padx=6,pady=3)
        self.botones[nombre]=boton;self.secciones[nombre]=interior
        self.vistas[nombre]=(exterior,lienzo,descripcion)
        self.barras[nombre]=barra
        if self.actual is None:self.mostrar(nombre)
        return interior

    def mostrar(self,nombre):
        if self.actual:self.vistas[self.actual][0].pack_forget();self.botones[self.actual].configure(bg='#190d13',fg=SUAVE)
        self.actual=nombre;self.vistas[nombre][0].pack(fill='both',expand=True)
        self.botones[nombre].configure(bg='#431424',fg=VERDE)
        self.titulo.set(nombre);self.detalle.set(self.vistas[nombre][2])
        from idiomas import localizar_widgets
        localizar_widgets(self.ventana.winfo_toplevel())
        self.vistas[nombre][1].yview_moveto(0)
        self.ventana._root().after_idle(lambda:self.refrescar(nombre) if self.ventana.winfo_exists() else None)

    def refrescar(self,nombre):
        if nombre not in self.vistas:return
        lienzo=self.vistas[nombre][1];interior=self.secciones[nombre];barra=self.barras[nombre]
        altura=max(1,lienzo.winfo_height());contenido=interior.winfo_reqheight()
        lienzo.configure(scrollregion=(0,0,max(1,lienzo.winfo_width()),max(altura,contenido)))
        if contenido>altura+2:
            if not barra.winfo_manager():barra.pack(side='right',fill='y',padx=(8,0))
        else:
            barra.pack_forget();lienzo.yview_moveto(0)

    def conectar_rueda(self,widget=None):
        widget=widget or self.ventana
        if widget.winfo_toplevel() is not self.ventana.winfo_toplevel():return
        tags=widget.bindtags()
        if self.tag_rueda not in tags:widget.bindtags((self.tag_rueda,)+tags)
        for hijo in widget.winfo_children():self.conectar_rueda(hijo)

    def rueda(self,e):
        if self.actual:
            self.vistas[self.actual][1].yview_scroll(-int(e.delta/120),'units')
        return 'break'

class TarjetaAspecto(CanvasUI):
    def __init__(self,padre,foto,nombre,accion):
        super().__init__(padre,bg=FONDO,highlightthickness=0,width=178,height=218,takefocus=True)
        self.foto=foto;self.nombre=nombre;self.accion=accion;self.activa=False
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',lambda e:accion())
        self.bind('<Return>',lambda e:accion());self.bind('<space>',lambda e:accion())

    def marcar(self,activa):self.activa=activa;self.dibujar()

    def dibujar(self):
        self.delete('all');w=max(100,self.winfo_width());h=max(160,self.winfo_height())
        color=ACENTO if self.activa else '#7c293e'
        self.create_polygon(12,1,w-20,1,w-1,20,w-1,h-12,w-12,h-1,1,h-1,1,12,
                            fill='#2c101b' if self.activa else TARJETA,outline=color,width=2)
        self.create_image(w/2,h*.43,image=self.foto,tags='vista_aspecto')
        self.create_line(14,h-46,w-14,h-46,fill=color)
        self.create_text(w/2,h-26,text=self.nombre,fill=VERDE if self.activa else TEXTO,font=(FAMILIA,11,'bold'))
        if self.activa:self.create_text(w-12,16,text='ACTIVO',anchor='e',fill='#ffb3c4',font=(FAMILIA,8,'bold'))


class GaleriaAspectos:
    def __init__(self,root,imagen,seleccion,elegir,modo='personaje'):
        from companera import COLORES_HALO,sombra_glitch
        self.ventana=tk.Toplevel(root);self.ventana.title('Capri // Aspectos');self.ventana.configure(bg=FONDO)
        self.ventana.geometry('680x640');self.ventana.minsize(560,560)
        self.marco=VentanaCyber(self.ventana,'ASPECTOS');contenido=self.marco.cuerpo
        self.fotos=[];self.botones={};self.elegir=elegir;self.seleccion=seleccion;self.modo=modo;self.imagen=imagen
        if modo=='pantalla':
            from disenos_pantalla import normalizar
            self.seleccion=normalizar(seleccion)
        tk.Label(contenido,text='ASPECTOS DE PANTALLA' if modo=='pantalla' else 'ELIGE TU FRECUENCIA',bg=FONDO,fg=TEXTO,font=(FAMILIA,18,'bold')).pack(anchor='w',padx=16,pady=(8,4))
        tk.Label(contenido,text='Diseño del marco y del chat · el color se elige aparte' if modo=='pantalla' else 'Sombras del constructo · aplicación instantánea',bg=FONDO,fg=SUAVE,font=(FAMILIA,10)).pack(anchor='w',padx=16,pady=(0,8))
        rejilla=tk.Frame(contenido,bg=FONDO);rejilla.pack(fill='both',expand=True,padx=8,pady=(0,8))
        opciones=[('violeta','Violeta'),('neon','Neón'),('hielo','Hielo'),('rojo','Rojo'),('ninguno','Sin sombra')]
        if modo=='pantalla':
            from avatar import ASPECTOS_PANTALLA
            opciones=[(clave,datos[0]) for clave,datos in ASPECTOS_PANTALLA.items()]
        im=imagen.copy();im.thumbnail((125,158),Image.Resampling.LANCZOS)
        for i,(clave,nombre) in enumerate(opciones):
            vista=Image.new('RGBA',(160,182))
            if modo=='pantalla':
                from avatar import miniatura_pantalla
                vista.alpha_composite(miniatura_pantalla(imagen,clave),(0,12))
            else:
                if clave in COLORES_HALO:vista.alpha_composite(sombra_glitch(im,COLORES_HALO[clave]),(8+(160-im.width)//2,8))
                vista.alpha_composite(im,((160-im.width)//2,4))
            foto=ImageTk.PhotoImage(vista);self.fotos.append(foto)
            boton=TarjetaAspecto(rejilla,foto,nombre,lambda k=clave:self.aplicar(k))
            boton.grid(row=i//3,column=i%3,sticky='nsew',padx=6,pady=6);self.botones[clave]=boton
        for col in range(3):rejilla.columnconfigure(col,weight=1)
        for fila in range(2):rejilla.rowconfigure(fila,weight=1)
        self.marcar()
        if modo=='pantalla':
            from tema_ui import observar
            observar(self.refrescar_color)

    def refrescar_color(self):
        if not self.ventana.winfo_exists():return
        from avatar import miniatura_pantalla
        self.fotos=[]
        for clave,boton in self.botones.items():
            vista=Image.new('RGBA',(160,182));vista.alpha_composite(miniatura_pantalla(self.imagen,clave),(0,12))
            foto=ImageTk.PhotoImage(vista);self.fotos.append(foto);boton.foto=foto;boton.dibujar()

    def marcar(self):
        for k,b in self.botones.items():b.marcar(k==self.seleccion)

    def aplicar(self,clave):
        if self.modo=='pantalla':
            from disenos_pantalla import normalizar
            clave=normalizar(clave)
        self.elegir(clave);self.seleccion=clave;self.marcar()

class CampoHex(CanvasUI):
    """Entrada hexadecimal con el mismo contorno y altura que sus acciones."""
    def __init__(self,padre,variable,aplicar):
        super().__init__(padre,width=174,height=44,bg=padre.cget('bg'),highlightthickness=0)
        self.activo=False
        self.entrada=tk.Entry(self,textvariable=variable,bg=TARJETA,fg=TEXTO,insertbackground=ACENTO,
                              font=('Consolas',11),relief='flat',bd=0,highlightthickness=0)
        self.item=self.create_window(48,22,window=self.entrada,anchor='w',width=112)
        self.entrada.bind('<Return>',lambda e:aplicar())
        self.entrada.bind('<FocusIn>',lambda e:self.enfocar(True));self.entrada.bind('<FocusOut>',lambda e:self.enfocar(False))
        self.bind('<Configure>',lambda e:self.dibujar())
        self.bind('<Button-1>',lambda e:self.entrada.focus_set())
        self.dibujar()

    def enfocar(self,activo):self.activo=activo;self.dibujar()

    def dibujar(self):
        self.delete('marco');w=max(174,self.winfo_width());h=44
        self.create_rectangle(2,2,w-2,h-2,fill=TARJETA,outline='',tags='marco')
        self.create_line(2,h-3,w-2,h-3,fill=ACENTO if self.activo else SUAVE,width=2 if self.activo else 1,tags='marco')
        self.create_text(24,22,text='HEX',fill=SUAVE,font=(FAMILIA,8,'bold'),tags='marco')
        self.itemconfigure(self.item,width=w-62);self.tag_lower('marco')


class PanelColores:
    def __init__(self,root,elegir):
        import tkinter as nativo
        from tema_ui import COLORES,actual,observar
        from idiomas import ui
        self.elegir=elegir;self.muestras={};self.fotos_muestras={}
        self.ventana=tk.Toplevel(root);self.ventana.title('Capri · Color')
        self.ventana.geometry('660x510');self.ventana.minsize(660,510)
        self.marco=VentanaCyber(self.ventana,'COLOR');cuerpo=self.marco.cuerpo
        tk.Label(cuerpo,text='COLOR DE LA INTERFAZ',bg=FONDO,fg=TEXTO,font=(FAMILIA,18,'bold')).pack(anchor='w',padx=18,pady=(8,4))
        tk.Label(cuerpo,text='Una paleta para Capri, sus menús y sus ventanas. Las imágenes y los efectos conservan sus colores.',
                 bg=FONDO,fg=SUAVE,font=(FAMILIA,10),wraplength=590,justify='left').pack(anchor='w',padx=18,pady=(0,12))
        rejilla=tk.Frame(cuerpo,bg=FONDO);rejilla.pack(fill='x',padx=16)
        for i,(nombre,valor) in enumerate(COLORES):
            # Las muestras muestran su color real, independiente del tema activo.
            muestra=nativo.Canvas(rejilla,width=136,height=80,bg=FONDO,highlightthickness=0,takefocus=True,cursor='hand2')
            muestra.grid(row=i//4,column=i%4,sticky='ew',padx=5,pady=5)
            muestra.create_rectangle(4,3,131,76,fill='#211018',outline=valor,tags='borde')
            circulo=Image.new('RGBA',(256,256));ImageDraw.Draw(circulo).ellipse((8,8,247,247),fill=valor)
            foto=ImageTk.PhotoImage(circulo.resize((32,32),Image.Resampling.LANCZOS),master=muestra)
            self.fotos_muestras[valor]=foto;muestra.create_image(28,27,image=foto)
            muestra.create_text(14,58,text=ui(nombre),anchor='w',fill='#fff0f3',font=(FAMILIA,10,'bold'))
            muestra.bind('<Button-1>',lambda e,v=valor:self.aplicar(v));muestra.bind('<Return>',lambda e,v=valor:self.aplicar(v))
            self.muestras[valor]=muestra
        for col in range(4):rejilla.columnconfigure(col,weight=1)
        personalizada=tk.Frame(cuerpo,bg=FONDO);personalizada.pack(fill='x',padx=20,pady=(18,8))
        tk.Label(personalizada,text='Color personalizado',bg=FONDO,fg=TEXTO,font=(FAMILIA,10,'bold')).pack(anchor='w',pady=(0,8))
        fila=tk.Frame(personalizada,bg=FONDO);fila.pack(fill='x')
        self.hex=tk.StringVar(value=actual())
        self.campo_hex=CampoHex(fila,self.hex,self.aplicar_hex)
        self.campo_hex.grid(row=0,column=0,sticky='ew',padx=(0,10))
        BotonCyber(fila,text='Aplicar',command=self.aplicar_hex,pady=12,estilo='principal',bg=ACENTO,fg=FONDO).grid(row=0,column=1,sticky='ew',padx=(0,8))
        BotonCyber(fila,text='Elegir otro color',command=self.elegir_otro,pady=12,estilo='secundario',bg=FONDO).grid(row=0,column=2,sticky='ew')
        fila.columnconfigure(3,weight=1)
        self.aviso=tk.StringVar()
        tk.Label(cuerpo,textvariable=self.aviso,bg=FONDO,fg=SUAVE,font=(FAMILIA,10)).pack(anchor='w',padx=20)
        observar(self.marcar);self.marcar()

    def aplicar(self,valor):
        self.elegir(valor);self.hex.set(valor);self.aviso.set('')

    def aplicar_hex(self):
        import re
        from idiomas import ui
        valor=self.hex.get().strip()
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',valor):
            self.aviso.set(ui('Escribe un color como #40d9e6.'));return
        self.aplicar(valor.lower())

    def elegir_otro(self):
        from tkinter import colorchooser
        from tema_ui import actual
        from idiomas import ui
        _,valor=colorchooser.askcolor(color=actual(),parent=self.ventana,title=ui('Color personalizado'))
        if valor:self.aplicar(valor)

    def marcar(self):
        if not self.ventana.winfo_exists():return
        from tema_ui import actual,color
        for valor,muestra in self.muestras.items():
            muestra.configure(bg=color(FONDO));muestra.itemconfigure('borde',width=3 if valor==actual() else 1,fill=color(TARJETA))


class BarraCyber(CanvasUI):
    def __init__(self,padre,command):
        super().__init__(padre,width=14,bg=padre.cget('bg'),highlightthickness=0)
        self.command=command;self.primero=0.;self.ultimo=1.;self.arrastre=None
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',self.iniciar)
        self.bind('<B1-Motion>',self.mover)

    def set(self,primero,ultimo):
        self.primero=float(primero);self.ultimo=float(ultimo);self.dibujar()

    def dibujar(self):
        self.delete('all');h=max(1,self.winfo_height());w=max(10,self.winfo_width())
        if self.ultimo-self.primero>=.999:return
        self.create_rectangle(w/2-1,6,w/2+1,h-6,fill='#3b202a',outline='')
        pista=max(1,h-12);a=6+self.primero*pista;b=min(h-6,max(a+30,6+self.ultimo*pista))
        a=max(6,min(a,b-30))
        self.create_rectangle(w/2-3,a,w/2+3,b,fill='#c04c69',outline='')
        medio=(a+b)/2
        for dy in (-3,0,3):self.create_line(w/2-2,medio+dy,w/2+2,medio+dy,fill='#f49bb0')

    def iniciar(self,e):
        h=max(1,self.winfo_height());rango=self.ultimo-self.primero
        if not self.primero*h<=e.y<=max(self.primero*h+28,self.ultimo*h):
            self.command('moveto',max(0,min(1-rango,e.y/h-rango/2)))
        self.arrastre=(e.y,self.primero)
    def mover(self,e):
        if self.arrastre:
            y,antes=self.arrastre;valor=antes+(e.y-y)/max(1,self.winfo_height())
            self.command('moveto',max(0,min(1-(self.ultimo-self.primero),valor)))

class InterruptorCyber(CanvasUI):
    def __init__(self,padre,text='',variable=None,command=None,**kw):
        for k in ('fg','selectcolor','activebackground','activeforeground','font'):kw.pop(k,None)
        kw.pop('bg',None)
        super().__init__(padre,height=42,bg=padre.cget('bg'),highlightthickness=0,takefocus=True,**kw)
        self.texto=text;self.variable=variable or tk.BooleanVar(value=False);self.command=command
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',lambda e:self.invoke())
        self.bind('<space>',lambda e:self.invoke());self.bind('<Return>',lambda e:self.invoke())

    def invoke(self):
        self.variable.set(not self.variable.get())
        if self.command:self.command()
        self.dibujar()

    def dibujar(self):
        self.delete('all');w=max(150,self.winfo_width());h=self.winfo_height();y=h/2
        on=self.variable.get();color=ACENTO if on else '#63404a'
        self.create_polygon(5,y-9,31,y-9,36,y-4,36,y+9,10,y+9,5,y+4,fill='#52192e' if on else '#23131b',outline=color)
        x=25 if on else 13;self.create_rectangle(x-4,y-5,x+4,y+5,fill=VERDE if on else '#9b7881',outline='')
        self.create_text(48,y,text=self.texto,anchor='w',width=max(80,w-54),fill=TEXTO,font=(FAMILIA,10))

class EscalaCyber(CanvasUI):
    def __init__(self,padre,from_=0,to=100,resolution=1,command=None,label='',showvalue=True,**kw):
        for k in ('fg','troughcolor','orient','activebackground','highlightthickness'):kw.pop(k,None)
        kw.pop('bg',None)
        super().__init__(padre,height=64 if label else (46 if showvalue else 34),bg=padre.cget('bg'),highlightthickness=0,takefocus=True,**kw)
        self.minimo=float(from_);self.maximo=float(to);self.paso=float(resolution);self.valor=self.minimo
        self.etiqueta=label;self.mostrar_valor=showvalue;self.estado='normal';self.comando_tcl=''
        if command:self.configure(command=command)
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',self.cambiar);self.bind('<B1-Motion>',self.cambiar)
        self.bind('<Left>',lambda e:self.tecla(-1));self.bind('<Right>',lambda e:self.tecla(1))

    def configure(self,cnf=None,**kw):
        if 'command' in kw:
            if self.comando_tcl:self.deletecommand(self.comando_tcl)
            self.comando_tcl=self.register(kw.pop('command'))
        if 'state' in kw:self.estado=kw.pop('state')
        resultado=super().configure(cnf,**kw) if cnf is not None or kw else None
        if hasattr(self,'valor'):self.dibujar()
        return resultado
    config=configure

    def cget(self,k):
        if k=='command':return self.comando_tcl
        if k=='state':return self.estado
        return super().cget(k)
    __getitem__=cget
    def get(self):return int(self.valor) if self.paso>=1 else self.valor
    def set(self,v):
        self.valor=max(self.minimo,min(self.maximo,round((float(v)-self.minimo)/self.paso)*self.paso+self.minimo));self.dibujar()

    def emitir(self):
        if self.comando_tcl:self.tk.call(self.comando_tcl,self.get())
    def cambiar(self,e):
        if self.estado=='disabled':return
        self.focus_set();self.set(self.minimo+(self.maximo-self.minimo)*max(0,min(1,(e.x-12)/max(1,self.winfo_width()-24))));self.emitir()
    def tecla(self,d):
        if self.estado!='disabled':self.set(self.valor+d*self.paso);self.emitir()

    def dibujar(self):
        self.delete('all');w=max(100,self.winfo_width());h=max(30,self.winfo_height());y=h-18
        x=14+(w-28)*(self.valor-self.minimo)/max(.001,self.maximo-self.minimo)
        color=ACENTO if self.estado!='disabled' else '#68424d'
        if self.etiqueta:self.create_text(12,10,text=self.etiqueta,anchor='w',fill=SUAVE,font=(FAMILIA,9))
        if self.mostrar_valor:self.create_text(w-12,10,text=f'{self.get():g}',anchor='e',fill=VERDE,font=(FAMILIA,10,'bold'))
        self.create_line(14,y,w-14,y,fill='#5d3040',width=2);self.create_line(14,y,x,y,fill=color,width=2)
        for k in range(5):
            xx=14+(w-28)*k/4;self.create_line(xx,y+6,xx,y+9,fill='#69404c')
        self.create_rectangle(x-4,y-7,x+4,y+7,fill=VERDE if self.estado!='disabled' else '#76515c',outline=color)

class SelectorCyber(CanvasUI):
    def __init__(self,padre,values=(),state='readonly',font=None,**kw):
        kw.pop('style',None)
        super().__init__(padre,height=44,bg=FONDO,highlightthickness=0,takefocus=True,**kw)
        self.valores=tuple(values);self.estado=state;self.valor='';self.popup=None
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',lambda e:self.abrir())
        self.bind('<Return>',lambda e:self.abrir());self.bind('<space>',lambda e:self.abrir())

    def bind(self,sequence=None,func=None,add=None):
        if sequence=='<<ComboboxSelected>>' and func:self.al_seleccionar=func
        return super().bind(sequence,func,add)

    def event_generate(self,sequence,**kw):
        if sequence=='<<ComboboxSelected>>' and not self.winfo_viewable() and hasattr(self,'al_seleccionar'):
            return self.al_seleccionar(None)
        return super().event_generate(sequence,**kw)

    def configure(self,cnf=None,**kw):
        if 'values' in kw:self.valores=tuple(kw.pop('values'))
        if 'state' in kw:self.estado=kw.pop('state')
        kw.pop('style',None);kw.pop('font',None)
        resultado=super().configure(cnf,**kw) if cnf is not None or kw else None
        if hasattr(self,'valor'):self.dibujar()
        return resultado
    config=configure
    def cget(self,k):
        if k=='values':return self.valores
        if k=='state':return self.estado
        return super().cget(k)
    __getitem__=cget
    def get(self):return self.valor
    def set(self,v):self.valor=str(v);self.dibujar()
    def current(self,i=None):
        if i is None:return self.valores.index(self.valor) if self.valor in self.valores else -1
        if 0<=i<len(self.valores):self.set(self.valores[i])

    def dibujar(self):
        self.delete('all');w=max(100,self.winfo_width())
        self.create_polygon(8,3,w-8,3,w-2,9,w-2,35,w-8,41,2,41,2,9,fill=TARJETA,outline='#83324a')
        self.create_text(14,22,text=self.valor,anchor='w',width=max(40,w-56),fill=SUAVE if self.estado=='disabled' else TEXTO,font=(FAMILIA,10))
        self.create_line(w-36,10,w-36,34,fill='#653041')
        self.create_polygon(w-26,19,w-16,19,w-21,25,fill=ACENTO,outline='')

    def abrir(self):
        if self.estado=='disabled' or not self.valores:return
        if self.popup and self.popup.winfo_exists():return
        from companera import area_trabajo
        import os
        l,t,r,b=area_trabajo();w=max(160,self.winfo_width());filas=min(8,len(self.valores));alto=38
        h=filas*alto+16;x=max(l+8,min(r-w-8,self.winfo_rootx()));y=self.winfo_rooty()+46
        if y+h>b-8:y=max(t+8,self.winfo_rooty()-h-2)
        p=self.popup=tk.Toplevel(self);p.overrideredirect(True);p.attributes('-topmost',True);p.configure(bg='#010203')
        if os.name=='nt':p.attributes('-transparentcolor','#010203')
        p.geometry(f'{w}x{h}+{x}+{y}')
        borde=CanvasUI(p,width=w,height=h,bg='#010203',highlightthickness=0);borde.pack()
        borde.create_polygon(8,1,w-10,1,w-1,10,w-1,h-9,w-9,h-1,1,h-1,1,8,fill=TARJETA,outline='#9e3b56')
        lista=self.popup_lista=CanvasUI(borde,bg=TARJETA,highlightthickness=0,width=w-32,height=filas*alto)
        borde.create_window(10,8,window=lista,anchor='nw');lista.configure(scrollregion=(0,0,w-32,len(self.valores)*alto))
        self.popup_filas=filas;self.popup_activo=max(0,self.current())
        fondos=[]
        for i,v in enumerate(self.valores):
            yy=i*alto
            fondos.append(lista.create_rectangle(0,yy,w-32,yy+alto,fill=TARJETA,outline=''))
            if i==self.current():lista.create_rectangle(1,yy+10,4,yy+28,fill=ACENTO,outline='')
            lista.create_text(15,yy+alto/2,text=v,anchor='w',fill=TEXTO,font=(FAMILIA,10))
            if i<len(self.valores)-1:lista.create_line(14,yy+alto-1,w-46,yy+alto-1,fill='#361c27')
        if len(self.valores)>filas:
            barra=BarraCyber(borde,lista.yview);barra.configure(bg=TARJETA);borde.create_window(w-18,8,window=barra,anchor='nw',height=filas*alto)
            lista.configure(yscrollcommand=barra.set)
        # Todas las listas cortas empiezan arriba: el elemento seleccionado no oculta los anteriores.
        lista.yview_moveto(0)
        def cerrar():
            if p.winfo_exists():p.grab_release();p.destroy()
            self.popup=None
        def elegir(e=None):
            indice=self.popup_activo if e is None else int(lista.canvasy(e.y)//alto)
            if 0<=indice<len(self.valores):self.current(indice);cerrar();self.event_generate('<<ComboboxSelected>>')
        def resaltar(indice):
            self.popup_activo=max(0,min(len(self.valores)-1,indice))
            for i,item in enumerate(fondos):lista.itemconfigure(item,fill='#4d1b2d' if i==self.popup_activo else TARJETA)
        def teclado(paso):
            resaltar(self.popup_activo+paso)
            if self.popup_activo*alto<lista.canvasy(0):lista.yview_moveto(self.popup_activo/len(self.valores))
            elif (self.popup_activo+1)*alto>lista.canvasy(filas*alto):lista.yview_moveto((self.popup_activo-filas+1)/len(self.valores))
            return 'break'
        resaltar(self.popup_activo)
        lista.bind('<Motion>',lambda e:resaltar(int(lista.canvasy(e.y)//alto)))
        lista.bind('<MouseWheel>',lambda e:(lista.yview_scroll(-int(e.delta/120),'units'),'break')[-1])
        lista.bind('<ButtonRelease-1>',elegir);lista.bind('<Return>',lambda e:elegir());p.bind('<Escape>',lambda e:cerrar())
        lista.bind('<Down>',lambda e:teclado(1));lista.bind('<Up>',lambda e:teclado(-1))
        def fuera(e):
            if p.winfo_exists() and not (p.winfo_rootx()<=e.x_root<p.winfo_rootx()+w and p.winfo_rooty()<=e.y_root<p.winfo_rooty()+h):cerrar()
        p.bind('<ButtonPress-1>',fuera);p.grab_set();lista.focus_set()

class CapturadorTecla(CanvasUI):
    def __init__(self,padre,valor,comenzar,terminar):
        super().__init__(padre,height=54,bg=FONDO,highlightthickness=0,takefocus=True)
        self.valor=valor;self.comenzar=comenzar;self.terminar=terminar;self.capturando=False
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',self.iniciar)
        self.bind('<KeyPress>',self.capturar);self.bind('<FocusOut>',lambda e:self.finalizar(None) if self.capturando else None)
        self.bind('<Destroy>',lambda e:self.finalizar(None) if e.widget is self and self.capturando else None)

    def iniciar(self,e=None):
        if not self.capturando:self.comenzar();self.capturando=True
        self.focus_set();self.dibujar()
    def capturar(self,e):
        if not self.capturando:return
        if e.keysym=='Escape':self.finalizar(None);return 'break'
        if e.keysym in ('Control_L','Control_R','Alt_L','Alt_R','Shift_L','Shift_R','Super_L','Super_R'):return 'break'
        from voz import atajo_valido
        base={'space':'Space','Return':'Enter','Prior':'PageUp','Next':'PageDown'}.get(e.keysym,e.keysym.upper() if len(e.keysym)==1 else e.keysym)
        partes=[]
        if e.state&4:partes.append('Ctrl')
        if e.state&(8|0x20000):partes.append('Alt')
        if e.state&1:partes.append('Shift')
        if e.state&64:partes.append('Win')
        valor='+'.join(partes+[base])
        if atajo_valido(valor):self.finalizar(valor)
        return 'break'
    def finalizar(self,valor):
        if not self.capturando:return
        self.capturando=False
        if valor:self.valor=valor
        self.terminar(valor)
        if self.winfo_exists():self.dibujar()
    def dibujar(self):
        self.delete('all');w=max(150,self.winfo_width())
        self.create_polygon(8,4,w-10,4,w-2,12,w-2,42,w-10,50,2,50,2,12,fill='#461526' if self.capturando else TARJETA,outline=ACENTO)
        self.create_text(16,27,text='Pulsa la tecla o combinación…' if self.capturando else self.valor,anchor='w',fill=TEXTO,font=(FAMILIA,11,'bold'))
        if not self.capturando:self.create_text(w-16,27,text='CAMBIAR',anchor='e',fill=VERDE,font=(FAMILIA,9,'bold'))

class BotonCyber(CanvasUI):
    def __init__(self,padre,text='',command=None,bg='#471528',fg=TEXTO,padx=14,pady=8,font=None,estilo='angular',**kw):
        from tkinter import font as tkfont
        self.fuente=font or (FAMILIA,10,'bold');self.texto=text;self.command=command
        self.color=bg;self.tinta=fg;self.estado=kw.pop('state','normal');self.hover=False;self.estilo=estilo
        for k in ('activebackground','activeforeground','relief','bd','cursor','disabledforeground','highlightthickness'):kw.pop(k,None)
        from idiomas import ui
        ancho=max(tkfont.Font(root=padre,font=self.fuente).measure(ui(text,k)) for k in ('es','en','pt','ja'))+padx*2+12
        super().__init__(padre,width=ancho,height=20+pady*2,bg=padre.cget('bg'),highlightthickness=0,takefocus=True,**kw)
        self.bind('<Configure>',lambda e:self.dibujar());self.bind('<Button-1>',lambda e:self.invoke())
        self.bind('<Return>',lambda e:self.invoke());self.bind('<space>',lambda e:self.invoke())
        self.bind('<Enter>',lambda e:self.resaltar(True));self.bind('<Leave>',lambda e:self.resaltar(False))

    def configure(self,cnf=None,**kw):
        for clave,atributo in (('state','estado'),('text','texto'),('command','command'),('fg','tinta'),('bg','color')):
            if clave in kw:setattr(self,atributo,kw.pop(clave))
        resultado=super().configure(cnf,**kw) if cnf is not None or kw else None
        if hasattr(self,'texto'):self.dibujar()
        return resultado
    config=configure
    def cget(self,k):
        if k=='text':return self.texto
        if k=='state':return self.estado
        return super().cget(k)
    __getitem__=cget
    def invoke(self):
        if self.estado!='disabled' and self.command:return self.command()
    def resaltar(self,valor):self.hover=valor;self.dibujar()
    def dibujar(self):
        self.delete('all');w=max(40,self.winfo_width());h=max(28,self.winfo_height())
        des=self.estado=='disabled';borde='#603340' if des else ('#ff97ae' if self.hover else '#a43c57')
        if self.estilo in ('principal','secundario'):
            r=5;relleno='#28151d' if des else ('#ff7898' if self.hover and self.estilo=='principal' else self.color)
            self.create_polygon(2+r,2,w-2-r,2,w-2,2,w-2,2+r,w-2,h-2-r,w-2,h-2,w-2-r,h-2,
                                2+r,h-2,2,h-2,2,h-2-r,2,2+r,2,2,
                                fill=relleno,outline='' if self.estilo=='principal' else borde,smooth=True,splinesteps=18)
        else:
            from disenos_pantalla import chaflan
            self.create_polygon(*chaflan(2,2,w-2,h-2,7),fill='#28151d' if des else self.color,outline=borde)
        self.create_text(w/2,h/2,text=self.texto,fill='#916e79' if des else self.tinta,font=self.fuente)

class MarcoTransmision(CanvasUI):
    """Marco de chat con cabecera, sin fondos rectangulares en los recortes."""
    def __init__(self,padre,titulo,**kw):
        super().__init__(padre,bg=padre.cget('bg'),highlightthickness=0,**kw)
        self.titulo=titulo;self.cuerpo=tk.Frame(self,bg='#180d13')
        self.item=self.create_window(12,35,window=self.cuerpo,anchor='nw')
        self.bind('<Configure>',self.dibujar)
    def retraducir(self):self.dibujar()
    def dibujar(self,e=None):
        self.delete('marco');w=max(60,self.winfo_width());h=max(50,self.winfo_height())
        self.create_polygon(10,1,w-17,1,w-1,17,w-1,h-10,w-10,h-1,1,h-1,1,10,
                            fill='#180d13',outline='#773047',tags='marco')
        self.create_line(16,28,w-16,28,fill='#542333',tags='marco')
        from idiomas import ui,idioma_actual
        from tkinter import font
        familia='Yu Gothic UI' if idioma_actual()=='ja' else FAMILIA
        fuente=font.Font(root=self,font=(familia,9,'bold'));titulo=ui(self.titulo)
        while titulo and fuente.measure(titulo)>w-36:titulo=titulo[:-2]+'…' if len(titulo)>1 else ''
        self.create_text(16,15,text=titulo,anchor='w',fill=VERDE,font=fuente,tags='marco')
        self.itemconfigure(self.item,width=max(1,w-24),height=max(1,h-47));self.tag_lower('marco')

class TarjetaInfo(CanvasUI):
    def __init__(self,padre,titulo,detalle):
        super().__init__(padre,height=72,bg=FONDO,highlightthickness=0)
        self.titulo=titulo;self.detalle=detalle;self.bind('<Configure>',lambda e:self.dibujar())
    def dibujar(self):
        self.delete('all');w=max(120,self.winfo_width())
        self.create_polygon(8,2,w-12,2,w-2,12,w-2,62,w-10,70,2,70,2,8,fill=TARJETA,outline='#542333')
        self.create_text(16,20,text=self.titulo,anchor='w',fill=VERDE,font=(FAMILIA,10,'bold'))
        self.create_text(16,46,text=self.detalle,anchor='w',width=max(80,w-32),fill=SUAVE,font=(FAMILIA,9))
