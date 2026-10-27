"""Instalación de IA local solicitada desde el botón Activar IA local."""
from pathlib import Path
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
import urllib.request
from recursos import descargar

BASE=Path(__file__).resolve().parent
HIDDEN=getattr(subprocess,'CREATE_NO_WINDOW',0)

def ping():
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=2) as r:json.load(r)
        return True
    except Exception:return False

class Activar:
    def __init__(self):
        self.root=tk.Tk();self.root.title('Capri · IA local');self.root.geometry('540x330');self.root.configure(bg='#0b0c13')
        self.q=queue.Queue();self.cancelar=threading.Event();self.proceso=None
        tk.Label(self.root,text='Conversa con Capri',bg='#0b0c13',fg='#ff4267',font=('Segoe UI',21,'bold')).pack(anchor='w',padx=24,pady=(23,12))
        self.estado=tk.StringVar(value='La primera vez se descargan Ollama y una IA de unos 2 GB. Después la conversación funciona en tu PC.')
        tk.Label(self.root,textvariable=self.estado,bg='#0b0c13',fg='#f6eff1',wraplength=485,justify='left',font=('Segoe UI',11)).pack(fill='x',padx=24,pady=8)
        self.barra=ttk.Progressbar(self.root,mode='determinate');self.barra.pack(fill='x',padx=24,pady=15)
        self.boton=tk.Button(self.root,text='Descargar y activar',command=self.iniciar,bg='#ff4267',fg='#100c14',relief='flat',padx=16,pady=10,font=('Segoe UI',11,'bold'));self.boton.pack(anchor='w',padx=24)
        self.root.protocol('WM_DELETE_WINDOW',self.cerrar);self.root.after(100,self.poll)

    def iniciar(self):
        self.boton.configure(state='disabled');threading.Thread(target=self.trabajar,daemon=True).start()

    def trabajar(self):
        try:
            local=Path(os.environ['LOCALAPPDATA'])
            exe=shutil.which('ollama')
            if not exe:
                ruta=local/'Programs/Ollama/ollama.exe'
                if ruta.exists():exe=str(ruta)
            if not ping():
                if not exe:
                    self.q.put(('estado','Descargando Ollama desde su sitio oficial…'))
                    instalador=BASE/'OllamaSetup.exe'
                    descargar('https://ollama.com/download/OllamaSetup.exe',instalador,
                              lambda n,t:self.q.put(('progreso',(n,t))),self.cancelar,maximo=2_500_000_000,plazo=900)
                    if self.cancelar.is_set():return
                    self.q.put(('estado','Instalando Ollama en tu cuenta de Windows…'))
                    self.proceso=subprocess.Popen([str(instalador),'/VERYSILENT','/NORESTART'],creationflags=HIDDEN)
                    if self.proceso.wait(timeout=300) != 0:raise RuntimeError('La instalación de Ollama no terminó correctamente.')
                    ruta=local/'Programs/Ollama/ollama.exe'
                    exe=str(ruta) if ruta.exists() else shutil.which('ollama')
                    if not exe:raise RuntimeError('No se encontró Ollama después de instalarlo.')
                if not ping():
                    subprocess.Popen([exe,'serve'],creationflags=HIDDEN,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)
                for i in range(50):
                    if self.cancelar.wait(1):return
                    if ping():break
                else:raise RuntimeError('Ollama no respondió. Ábrelo desde Inicio y vuelve a intentar.')
            self.q.put(('estado','Descargando llama3.2:3b. Puede tardar varios minutos según tu conexión.'))
            req=urllib.request.Request('http://127.0.0.1:11434/api/pull',data=json.dumps({'model':'llama3.2:3b','stream':True}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=90) as r:
                for linea in r:
                    if self.cancelar.is_set():return
                    estado=json.loads(linea)
                    if estado.get('error'):raise RuntimeError(estado['error'])
                    if estado.get('total'):self.q.put(('progreso',(estado.get('completed',0),estado['total'])))
                    elif estado.get('status'):self.q.put(('estado','Modelo: '+estado['status']))
            cfg={}
            try:cfg=json.loads((BASE/'ajustes.json').read_text(encoding='utf8'))
            except (OSError,ValueError):pass
            cfg.update({'ia':True,'modelo':'llama3.2:3b'})
            (BASE/'ajustes.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
            self.q.put(('fin','IA activada. Ya puedes hablar de cualquier tema con Capri. No necesitas cerrar el chat.'))
        except Exception as e:self.q.put(('error',str(e)[:250]))

    def poll(self):
        for i in range(100):
            try:tipo,v=self.q.get_nowait()
            except queue.Empty:break
            if tipo=='progreso':
                n,t=v;self.barra['value']=n*100/t if t else 0
            else:
                self.estado.set(v)
                if tipo in ('fin','error'):
                    self.boton.configure(text='Cerrar' if tipo=='fin' else 'Reintentar',state='normal',command=self.cerrar if tipo=='fin' else self.iniciar)
        self.root.after(100,self.poll)

    def cerrar(self):
        self.cancelar.set()
        if self.proceso and self.proceso.poll() is None:self.proceso.terminate()
        self.root.destroy()

if __name__=='__main__':Activar().root.mainloop()
