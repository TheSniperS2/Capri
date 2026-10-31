"""Paleta de interfaz compartida. Nunca transforma ilustraciones ni efectos."""
import colorsys
import re
import tkinter as _tk
from tkinter import ttk as _ttk
import weakref
from idiomas import Lienzo

PREDETERMINADO='#ff4267'
COLORES=(('Rojo',PREDETERMINADO),('Cian','#40d9e6'),('Azul','#689bff'),
         ('Violeta','#b58aff'),('Verde','#52dea2'),('Ámbar','#ffc466'),
         ('Rosa','#f786d4'),('Blanco','#d8e4ef'))
_actual=PREDETERMINADO
_widgets=weakref.WeakSet()
_estilos=weakref.WeakSet()
_observadores=[]
_origenes={}
_cache={}
_opciones={'bg','background','fg','foreground','insertbackground','selectbackground',
           'selectforeground','highlightbackground','highlightcolor','activebackground',
           'activeforeground','disabledforeground','readonlybackground','fieldbackground','troughcolor','selectcolor'}
_tintas={'fill','outline','activefill','activeoutline','disabledfill','disabledoutline'}

def normalizar(valor):
    return valor.lower() if isinstance(valor,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',valor) else PREDETERMINADO

def actual():return _actual

def color(valor):
    if not isinstance(valor,str):return valor
    origen=_origenes.get(valor.lower(),valor.lower())
    if _actual==PREDETERMINADO or not re.fullmatch(r'#[0-9a-f]{6}',origen):return origen
    if origen in ('#010203','#000000','#ffffff'):return origen
    if origen in _cache:return _cache[origen]
    rgb=tuple(int(origen[i:i+2],16)/255 for i in (1,3,5))
    _,l,s=colorsys.rgb_to_hls(*rgb)
    if s<.10:return origen
    target=tuple(int(_actual[i:i+2],16)/255 for i in (1,3,5))
    h,lum,sat=colorsys.rgb_to_hls(*target)
    # Oscuros siguen oscuros y los textos claros conservan su legibilidad.
    nueva_l=l if l>.78 else min(.85,l*max(.5,min(1.25,lum/.6294)))
    salida='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,nueva_l,min(1,s*sat/.74)))
    if origen==PREDETERMINADO:salida=_actual
    _cache[origen]=salida;_origenes.setdefault(salida,origen)
    return salida

def observar(metodo):_observadores.append(weakref.WeakMethod(metodo))

def activar(valor):
    global _actual
    _actual=normalizar(valor);_cache.clear()
    for w in list(_widgets):
        try:
            if w.winfo_exists():w._refrescar_tema()
        except _tk.TclError:pass
    for estilo in list(_estilos):
        try:estilo.refrescar()
        except _tk.TclError:pass
    vivos=[]
    for ref in _observadores:
        metodo=ref()
        if metodo is not None:
            try:metodo()
            except _tk.TclError:pass
            vivos.append(ref)
    _observadores[:]=vivos

class _Colores:
    def __init__(self,*args,**kw):
        self._colores_ui={}
        kw=self._preparar_colores(kw)
        super().__init__(*args,**kw);_widgets.add(self)

    def _preparar_colores(self,kw):
        kw=dict(kw)
        for k,v in kw.items():
            if k in _opciones:
                self._colores_ui[k]=_origenes.get(str(v).lower(),v);kw[k]=color(v)
        return kw

    def configure(self,cnf=None,**kw):
        if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
        if not kw:return super().configure(cnf) if cnf is not None else super().configure()
        kw=self._preparar_colores(kw)
        return super().configure(cnf,**kw) if cnf is not None else super().configure(**kw)
    config=configure

    def _refrescar_tema(self):
        if self._colores_ui:super().configure(**{k:color(v) for k,v in self._colores_ui.items()})

class LienzoUI(_Colores,Lienzo):
    def __init__(self,*args,**kw):
        self._colores_items={};super().__init__(*args,**kw)

    def _create(self,tipo,args,kw):
        fuentes={k:_origenes.get(str(v).lower(),v) for k,v in kw.items() if k in _tintas}
        item=super()._create(tipo,args,{k:color(v) if k in _tintas else v for k,v in kw.items()})
        self._colores_items[item]=fuentes
        return item

    def itemconfigure(self,item,cnf=None,**kw):
        if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
        fuentes={k:_origenes.get(str(v).lower(),v) for k,v in kw.items() if k in _tintas}
        for identificador in self.find_withtag(item):self._colores_items.setdefault(identificador,{}).update(fuentes)
        return super().itemconfigure(item,cnf,**{k:color(v) if k in _tintas else v for k,v in kw.items()})
    itemconfig=itemconfigure

    def delete(self,*args):
        if 'all' in args:self._colores_items.clear()
        else:
            for tag in args:
                for item in self.find_withtag(tag):self._colores_items.pop(item,None)
        return super().delete(*args)

    def _refrescar_tema(self):
        super()._refrescar_tema()
        for item,fuentes in self._colores_items.items():
            if fuentes:_tk.Canvas.itemconfigure(self,item,**{k:color(v) for k,v in fuentes.items()})

class _TkUI:
    """Clases propias: no modifica tkinter ni los lienzos de los efectos."""
    def __getattr__(self,nombre):return getattr(_tk,nombre)

tk=_TkUI()
for _nombre in ('Tk','Toplevel','Frame','Label','LabelFrame','Entry','Text','Button','Checkbutton','Scrollbar'):
    setattr(tk,_nombre,type(_nombre,(_Colores,getattr(_tk,_nombre)),{}))

class TextoUI(_Colores,_tk.Text):
    def __init__(self,*args,**kw):
        self._colores_etiquetas={};super().__init__(*args,**kw)
    def tag_configure(self,nombre,cnf=None,**kw):
        if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
        self._colores_etiquetas.setdefault(nombre,{}).update({k:_origenes.get(str(v).lower(),v) for k,v in kw.items() if k in _opciones})
        return super().tag_configure(nombre,cnf,**{k:color(v) if k in _opciones else v for k,v in kw.items()})
    tag_config=tag_configure
    def tag_delete(self,*nombres):
        for nombre in nombres:self._colores_etiquetas.pop(nombre,None)
        return super().tag_delete(*nombres)
    def _refrescar_tema(self):
        super()._refrescar_tema()
        for nombre,kw in self._colores_etiquetas.items():
            if kw:_tk.Text.tag_configure(self,nombre,**{k:color(v) for k,v in kw.items()})

tk.Text=TextoUI

class EstiloUI(_ttk.Style):
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw);self._reglas={};self._mapas={};_estilos.add(self)
    def configure(self,estilo,query_opt=None,**kw):
        if kw:self._reglas.setdefault(estilo,{}).update(kw)
        return super().configure(estilo,query_opt,**{k:color(v) if 'color' in k or k in _opciones else v for k,v in kw.items()})
    def map(self,estilo,query_opt=None,**kw):
        if kw:self._mapas.setdefault(estilo,{}).update(kw)
        return super().map(estilo,query_opt,**{k:[(*fila[:-1],color(fila[-1])) for fila in v] for k,v in kw.items()})
    def refrescar(self):
        for nombre,kw in self._reglas.items():self.configure(nombre,**kw)
        for nombre,kw in self._mapas.items():self.map(nombre,**kw)
