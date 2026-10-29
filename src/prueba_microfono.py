"""Prueba explícita del micrófono: cinco segundos en memoria, sin dictado ni red."""
import array
from dataclasses import dataclass
import math
import queue
import threading
import time
import tkinter as tk
from idiomas import Lienzo as CanvasUI

from reconocimiento import energia

def umbral_db(valor):
    if valor is None:return None
    try:valor=float(valor)
    except (TypeError,ValueError):return None
    return min(-20,max(-75,valor)) if math.isfinite(valor) else None

def decibelios(rms):
    return max(-90,min(0,20*math.log10(max(rms,1e-9))))

def filtrar(datos,umbral):
    umbral=umbral_db(umbral)
    return bytes(len(datos)) if umbral is not None and decibelios(energia(datos))<umbral else datos

@dataclass(frozen=True)
class Muestra:
    pcm:bytes
    tasa:int

def grabar(micro,detener,actualizar,dispositivo=None,duracion=5):
    import sounddevice as sd
    from voz import resolver_microfono,_abrir_entrada
    indice=resolver_microfono(dispositivo)
    datos=sd.query_devices(indice,kind='input') if indice is not None else sd.query_devices(kind='input')
    cola=queue.Queue(maxsize=160);fragmentos=[];cantidad=0
    micro.diagnostico={'seleccion':dispositivo,'motor':'prueba-sin-transcripcion','intentos':[]}
    def recibir(datos,frames,reloj,error):
        try:cola.put_nowait(bytes(datos))
        except queue.Full:pass
    with _abrir_entrada(indice,datos,recibir,detener,micro.diagnostico['intentos']) as tasa:
        limite=int(tasa*2*duracion);plazo=time.monotonic()+duracion+3
        while cantidad<limite and not detener.is_set():
            if time.monotonic()>plazo:raise RuntimeError('El micrófono dejó de entregar audio.')
            try:bloque=cola.get(timeout=.1)
            except queue.Empty:continue
            bloque=bloque[:limite-cantidad];fragmentos.append(bloque);cantidad+=len(bloque)
            pico=max((abs(x) for x in array.array('h',bloque)),default=0)/32768
            actualizar(decibelios(energia(bloque)),pico,cantidad/(tasa*2))
    return Muestra(b''.join(fragmentos),int(tasa)) if fragmentos else None

def reproducir(muestra,detener):
    import sounddevice as sd
    if detener.is_set() or not muestra or not muestra.pcm:return
    tasa=int(sd.query_devices(kind='output')['default_samplerate'])
    pcm=muestra.pcm
    if tasa!=muestra.tasa:
        import numpy as np
        a=np.frombuffer(pcm,dtype='<i2')
        posiciones=np.arange(round(len(a)*tasa/muestra.tasa))*muestra.tasa/tasa
        pcm=np.interp(posiciones,np.arange(len(a)),a).astype('<i2').tobytes()
    with sd.RawOutputStream(samplerate=tasa,channels=1,dtype='int16',latency='low') as salida:
        paso=int(tasa*.05)*2
        for i in range(0,len(pcm),paso):
            if detener.is_set():salida.abort();return
            salida.write(pcm[i:i+paso])

from ajustes_ui import BotonCyber,InterruptorCyber,EscalaCyber

class PanelPrueba(tk.Frame):
    def __init__(self,padre,micro,cfg,guardar,antes_grabar=None):
        super().__init__(padre,bg='#211018',padx=12,pady=12)
        self.micro=micro;self.cfg=cfg;self.guardar=guardar;self.raiz=self._root()
        self.antes_grabar=antes_grabar
        self.cola=queue.Queue();self.stop=threading.Event();self.ticket=0
        self.activa=False;self.cerrado=False;self.muestra=None;self.hilo=None;self.db=-90
        fg='#f6eff1';bg='#211018'
        tk.Label(self,text='Prueba de micrófono',bg=bg,fg=fg,font=('Segoe UI',11,'bold')).pack(anchor='w')
        tk.Label(self,text='Graba 5 segundos y escucha cómo llega tu voz. No necesitas decir Capri.',
                 bg=bg,fg='#bb929f',wraplength=425,justify='left').pack(anchor='w',pady=(3,8))
        self.medidor=CanvasUI(self,height=25,bg='#10090d',highlightthickness=0)
        self.medidor.pack(fill='x');self.medidor.bind('<Configure>',lambda e:self.dibujar())
        self.etiqueta=tk.StringVar(value='Sin prueba · el micrófono se abre al pulsar Grabar.')
        tk.Label(self,textvariable=self.etiqueta,bg=bg,fg=fg,wraplength=425,justify='left').pack(anchor='w',pady=5)
        botones=tk.Frame(self,bg=bg);botones.pack(fill='x')
        self.b_grabar=BotonCyber(botones,text='Grabar prueba · 5 s',command=self.grabar,bg='#4a1427',fg=fg,
                               activebackground='#77243c',activeforeground='#ffadbf',relief='flat',padx=10,pady=7,font=('Chakra Petch',9,'bold'))
        self.b_grabar.pack(side='left')
        self.b_oir=BotonCyber(botones,text='Escuchar prueba',command=self.oir,state='disabled',bg='#4a1427',fg=fg,
                            disabledforeground='#80748e',activebackground='#77243c',activeforeground='#ffadbf',relief='flat',padx=10,pady=7,font=('Chakra Petch',9,'bold'))
        self.b_oir.pack(side='left',padx=6)
        self.automatico=tk.BooleanVar(value=umbral_db(cfg.get('umbral_microfono_db')) is None)
        InterruptorCyber(self,text='Umbral automático (recomendado)',variable=self.automatico,command=self.cambiar,
                       bg=bg,fg=fg,selectcolor='#10090d',activebackground=bg,activeforeground=fg).pack(anchor='w',pady=(10,0))
        self.escala=EscalaCyber(self,from_=-75,to=-20,resolution=1,orient='horizontal',bg=bg,fg=fg,
                             highlightthickness=0,troughcolor='#10090d',label='Umbral manual · dB')
        self.escala.set(umbral_db(cfg.get('umbral_microfono_db')) or -56)
        self.escala.configure(state='disabled' if self.automatico.get() else 'normal')
        self.escala.bind('<ButtonRelease-1>',self.cambiar);self.escala.bind('<KeyRelease>',self.cambiar)
        if not self.automatico.get():self.escala.pack(fill='x',pady=(6,0))
        self.ayuda_umbral=tk.Label(self,text='Izquierda: capta voz más baja. Derecha: exige hablar más fuerte.\n'
                 'La línea marca el umbral manual. Pasarlo no garantiza reconocer las palabras.\n'
                 'La prueba se escucha sin este filtro y se borra al cerrar Ajustes.',bg=bg,fg='#bb929f',wraplength=425,justify='left')
        self.ayuda_umbral.pack(anchor='w',pady=(6,0))
        self.ayuda_manual=self.ayuda_umbral.cget('text')
        if self.automatico.get():self.ayuda_umbral.configure(text='El umbral se ajusta automáticamente a tu voz.')
        self.bind('<Destroy>',self.destruir)
        self.pendiente=self.raiz.after(60,self.poll)

    def cambiar(self,event=None):
        valor=None if self.automatico.get() else float(self.escala.get())
        self.escala.configure(state='disabled' if valor is None else 'normal')
        if valor is None:self.escala.pack_forget()
        elif not self.escala.winfo_manager():self.escala.pack(fill='x',pady=(6,0),before=self.ayuda_umbral)
        self.ayuda_umbral.configure(text='El umbral se ajusta automáticamente a tu voz.' if valor is None else self.ayuda_manual)
        self.guardar('umbral_microfono_db',valor);self.dibujar()

    def dibujar(self):
        c=self.medidor;w=max(1,c.winfo_width());c.delete('all')
        valor=umbral_db(self.cfg.get('umbral_microfono_db'))
        color='#b5ff7c' if valor is None or self.db>=valor else '#bb929f'
        c.create_rectangle(0,0,w*max(0,(self.db+75)/75),25,fill=color,outline='')
        if valor is not None:
            x=w*(valor+75)/75;c.create_line(x,0,x,25,fill='#ff4267',width=3)

    def ejecutar(self,funcion):
        self.stop=threading.Event();stop=self.stop;self.ticket+=1;ticket=self.ticket
        self.activa=True;self.b_grabar.configure(text='Detener prueba');self.b_oir.configure(state='disabled')
        def trabajar():
            try:
                resultado=funcion(stop,ticket)
                if not self.cerrado and ticket==self.ticket:self.cola.put((ticket,'fin',resultado,None))
            except Exception as e:
                if not self.cerrado and ticket==self.ticket:self.cola.put((ticket,'fin',None,None if stop.is_set() else str(e)))
        self.hilo=threading.Thread(target=trabajar,daemon=True);self.hilo.start()

    def grabar(self):
        if self.activa:self.stop.set();return
        if self.antes_grabar:self.antes_grabar()
        self.muestra=None;self.etiqueta.set('Preparando el micrófono…')
        self.ejecutar(lambda stop,t:self.micro.probar(stop,lambda db,pico,s:self.cola.put((t,'nivel',(db,pico,s),None)),self.cfg.get('microfono')))

    def oir(self):
        if self.activa or not self.muestra:return
        muestra=self.muestra;self.etiqueta.set('Reproduciendo la prueba…')
        self.ejecutar(lambda stop,t:self.micro.reproducir_prueba(muestra,stop))

    def poll(self):
        if self.cerrado:return
        for _ in range(200):
            try:ticket,tipo,valor,error=self.cola.get_nowait()
            except queue.Empty:break
            if ticket!=self.ticket:continue
            if tipo=='nivel':
                self.db,pico,segundos=valor;self.dibujar()
                umbral=umbral_db(self.cfg.get('umbral_microfono_db'))
                paso='' if umbral is None else (' · supera el umbral' if self.db>=umbral else ' · debajo del umbral')
                self.etiqueta.set(f'Grabando {segundos:.1f}/5 s · {self.db:.0f} dB'+(' · saturación: baja la ganancia del micrófono' if pico>.98 else paso))
            elif tipo=='fin':
                self.activa=False;self.b_grabar.configure(text='Grabar prueba · 5 s')
                if valor is not None:self.muestra=valor
                self.b_oir.configure(state='normal' if self.muestra else 'disabled')
                self.etiqueta.set('No pude completar la prueba: '+error[:160] if error else ('Prueba lista. Pulsa Escuchar prueba.' if self.muestra else ('Prueba detenida.' if self.stop.is_set() else 'No llegó audio del micrófono.')))
        self.pendiente=self.raiz.after(60,self.poll)

    def descartar(self):
        self.stop.set();self.ticket+=1;self.muestra=None;self.activa=False;self.db=-90
        self.b_oir.configure(state='disabled');self.b_grabar.configure(text='Grabar prueba · 5 s')
        self.etiqueta.set('Micrófono cambiado. Graba otra prueba.');self.dibujar()

    def destruir(self,event):
        if event.widget is not self:return
        self.cerrado=True;self.stop.set();self.ticket+=1;self.muestra=None
        if self.pendiente:self.raiz.after_cancel(self.pendiente);self.pendiente=None
