"""Abrir Capri: instalador local, con progreso y cancelación."""
from pathlib import Path
import base64
import hashlib
import io
import json
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
import traceback
import zipfile

PAYLOAD = '__CAPRI_PAYLOAD__'
HASH = '__CAPRI_HASH__'
DESTINO = Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'Capri'
HIDDEN = getattr(subprocess,'CREATE_NO_WINDOW',0)

class Preparar:
    def __init__(self):
        self.root=tk.Tk();self.root.title('Capri · Preparación');self.root.geometry('560x360');self.root.configure(bg='#0b0c13')
        self.q=queue.Queue();self.cancelar=threading.Event();self.proceso=None
        tk.Label(self.root,text='CAPRI',fg='#ff4267',bg='#0b0c13',font=('Segoe UI',27,'bold')).pack(anchor='w',padx=26,pady=(24,3))
        tk.Label(self.root,text='Tu compañera de escritorio',fg='#b5ff7c',bg='#0b0c13',font=('Segoe UI',12)).pack(anchor='w',padx=27,pady=(0,17))
        self.estado=tk.StringVar(value='Preparando la aplicación…')
        tk.Label(self.root,textvariable=self.estado,fg='#f6eff1',bg='#0b0c13',font=('Segoe UI',11),wraplength=505,justify='left').pack(fill='x',padx=26)
        self.barra=ttk.Progressbar(self.root,mode='indeterminate');self.barra.pack(fill='x',padx=26,pady=17);self.barra.start(12)
        self.detalle=tk.StringVar(value='La primera apertura necesita internet. Verás cada paso y el avance de las descargas.')
        tk.Label(self.root,textvariable=self.detalle,fg='#aaa2b3',bg='#0b0c13',wraplength=505,justify='left',font=('Segoe UI',9)).pack(fill='x',padx=26)
        self.boton=tk.Button(self.root,text='Cancelar',command=self.cerrar,bg='#282432',fg='#f6eff1',relief='flat',padx=15,pady=8);self.boton.pack(anchor='e',padx=26,pady=17)
        self.root.protocol('WM_DELETE_WINDOW',self.cerrar)
        self.root.after(100,self.poll)
        self.root.after(200,self.iniciar)

    def iniciar(self):
        self.cancelar.clear();self.boton.configure(text='Cancelar',command=self.cerrar)
        self.barra.configure(mode='indeterminate');self.barra.start(12)
        threading.Thread(target=self.trabajar,daemon=True).start()

    def comando(self,args,plazo=600):
        with (DESTINO/'instalacion.log').open('ab') as log:
            self.proceso=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=HIDDEN)
            inicio=time.monotonic()
            while self.proceso.poll() is None:
                if self.cancelar.wait(.2):
                    self.proceso.terminate();raise InterruptedError('Preparación cancelada.')
                if time.monotonic()-inicio>plazo:
                    self.proceso.terminate();raise TimeoutError('Este paso tardó demasiado. Comprueba la conexión y vuelve a abrir Capri.')
            if self.proceso.returncode:
                raise RuntimeError('No se completó la instalación. El detalle está en '+str(DESTINO/'instalacion.log'))

    def trabajar(self):
        try:
            DESTINO.mkdir(parents=True,exist_ok=True)
            origen=Path(__file__).resolve()
            permanente=DESTINO/'Preparar Capri.pyw'
            if origen!=permanente.resolve():permanente.write_bytes(origen.read_bytes())
            paquete=base64.b64decode(PAYLOAD)
            if hashlib.sha256(paquete).hexdigest()!=HASH:raise ValueError('El archivo de Capri está incompleto.')
            with zipfile.ZipFile(io.BytesIO(paquete)) as z:
                for nombre in z.namelist():
                    p=Path(nombre)
                    if p.is_absolute() or '..' in p.parts or ':' in nombre or '\\' in nombre:raise ValueError('Paquete no válido.')
                z.extractall(DESTINO)
            sys.path.insert(0,str(DESTINO))
            from recursos import descargar,extraer_seguro,ARTE,MODELO_URL,MODELO_NOMBRE
            python=DESTINO/'.venv/Scripts/python.exe'
            if not python.exists():
                self.q.put(('estado','1/5 · Creando un entorno propio para Capri…'))
                base_python=Path(sys.executable).with_name('python.exe')
                self.comando([str(base_python if base_python.exists() else Path(sys.executable)),'-m','venv',str(DESTINO/'.venv')],120)
            marca=DESTINO/'dependencias-listas.txt'
            dependencias=(DESTINO/'requirements.txt').read_bytes()
            version=hashlib.sha256(dependencias).hexdigest()
            if not marca.exists() or marca.read_text()!=version:
                self.q.put(('estado','2/5 · Instalando micrófono, voz e imágenes…'))
                self.q.put(('detalle','Este paso puede tardar varios minutos. No tienes que escribir comandos.'))
                self.comando([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(DESTINO/'requirements.txt')],720)
                self.comando([str(python),'-c','import PIL,sounddevice,vosk,edge_tts,faster_whisper,send2trash.win.modern'],45)
                marca.write_text(version)
            for numero,(nombre,url) in enumerate(ARTE):
                archivo=DESTINO/'assets'/nombre
                if archivo.exists() and archivo.stat().st_size>100:continue
                self.q.put(('estado',f'3/5 · Descargando la referencia de Capri ({numero+1}/{len(ARTE)})…'))
                try:
                    descargar(url,archivo,lambda n,t:self.q.put(('progreso',(n,t))),self.cancelar,maximo=12_000_000,plazo=90)
                except InterruptedError:raise
                except Exception:
                    if numero==0:raise
                    continue
                if archivo.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                    archivo.unlink(missing_ok=True);raise ValueError('El servidor no devolvió una imagen válida de Capri.')
            modelos=DESTINO/'modelos'
            if not (modelos/MODELO_NOMBRE/'am/final.mdl').is_file():
                self.q.put(('estado','4/5 · Preparando el micrófono en español (39 MB)…'))
                archivo=DESTINO/'voz-es.zip'
                descargar(MODELO_URL,archivo,lambda n,t:self.q.put(('progreso',(n,t))),self.cancelar,maximo=100_000_000,plazo=600)
                self.q.put(('estado','4/5 · Descomprimiendo el reconocimiento de voz…'))
                extraer_seguro(archivo,modelos)
                if not (modelos/MODELO_NOMBRE/'am/final.mdl').is_file():raise ValueError('El modelo de voz no está completo.')
                archivo.unlink(missing_ok=True)
            self.q.put(('estado','5/5 · Preparando reconocimiento preciso en español (148 MB)…'))
            from preparar_whisper import preparar
            preparar(modelos,lambda t:self.q.put(('estado',t)),lambda n,t:self.q.put(('progreso',(n,t))),self.cancelar)
            if self.cancelar.is_set():return
            self.q.put(('estado','Iniciando Capri…'))
            # Un lanzador permanente evita depender de la ubicación del archivo descargado.
            lanzador=DESTINO/'Abrir Capri.vbs'
            pythonw=DESTINO/'.venv/Scripts/pythonw.exe'
            linea='CreateObject("WScript.Shell").Run """'+str(pythonw)+'"" ""'+str(DESTINO/'app.py')+'""", 0, False\r\n'
            lanzador.write_text(linea,encoding='utf-16')
            # Acceso directo normal, solo para la cuenta actual.
            # Otra ruta por contenido evita que Inicio conserve un icono anterior.
            datos_icono=(DESTINO/'capri.ico').read_bytes()
            icono_acceso=DESTINO/('capri-icono-'+hashlib.sha256(datos_icono).hexdigest()[:12]+'.ico')
            icono_acceso.write_bytes(datos_icono)
            datos=base64.b64encode(json.dumps([str(pythonw),str(DESTINO/'app.py'),str(DESTINO),str(icono_acceso)]).encode('utf8')).decode('ascii')
            script="$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+datos+"'))|ConvertFrom-Json;$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut([IO.Path]::Combine($w.SpecialFolders.Item('Desktop'),'Capri.lnk'));$s.TargetPath=$p[0];$s.Arguments='\"'+$p[1]+'\"';$s.WorkingDirectory=$p[2];$s.IconLocation=$p[3]+',0';$s.Save()"
            codificado=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
            try:self.comando(['powershell.exe','-NoProfile','-EncodedCommand',codificado],20)
            except InterruptedError:raise
            except Exception:pass
            if self.cancelar.is_set():return
            with (DESTINO/'arranque.log').open('ab') as log:
                self.proceso=subprocess.Popen([str(pythonw),str(DESTINO/'app.py')],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=HIDDEN)
            time.sleep(1.5)
            if self.proceso.poll() not in (None,0):raise RuntimeError('No se pudo abrir la interfaz. Revisa '+str(DESTINO/'arranque.log'))
            self.q.put(('fin',None))
        except InterruptedError:pass
        except Exception as e:
            try:
                with (DESTINO/'instalacion.log').open('a',encoding='utf8') as log:traceback.print_exc(file=log)
            except OSError:pass
            self.q.put(('error',str(e)[:400]))

    def poll(self):
        for i in range(100):
            try:tipo,v=self.q.get_nowait()
            except queue.Empty:break
            if tipo=='estado':self.estado.set(v)
            elif tipo=='detalle':self.detalle.set(v)
            elif tipo=='progreso':
                n,t=v
                if t:
                    self.barra.stop();self.barra.configure(mode='determinate');self.barra['value']=n*100/t
                    self.detalle.set(f'{n/1_000_000:.1f} / {t/1_000_000:.1f} MB')
            elif tipo=='error':
                self.barra.stop();self.estado.set('No se pudo completar la preparación.')
                self.detalle.set(v);self.boton.configure(text='Reintentar',command=self.iniciar)
            elif tipo=='fin':self.root.destroy();return
        self.root.after(100,self.poll)

    def cerrar(self):
        self.cancelar.set()
        if self.proceso and self.proceso.poll() is None:self.proceso.terminate()
        self.root.destroy()

if __name__=='__main__':Preparar().root.mainloop()
