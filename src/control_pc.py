"""Control ampliado optativo. Operaciones fijas y confirmaciones de un solo uso."""
from pathlib import Path
import os
import re
import time
import threading
import subprocess
from dataclasses import dataclass
from core import normalizar

ACCIONES=('archivo_abrir','archivo_buscar','archivo_listar','archivo_leer','archivo_crear_carpeta',
          'archivo_borrar','archivo_mover','archivo_renombrar','ventana_listar','ventana_minimizar',
          'ventana_maximizar','ventana_cerrar','programa_listar','programa_abrir','equipo_apagar','equipo_reiniciar','equipo_cancelar_apagado')
SISTEMA='''Si control ampliado está activo, también puedes usar estas acciones:
archivo_abrir, archivo_buscar, archivo_listar, archivo_leer, archivo_crear_carpeta, archivo_borrar.
valor debe ser un nombre o ruta EXACTO del mensaje. Para el archivo seleccionado: valor="seleccionado", solo si el usuario pide el seleccionado o esta imagen/este archivo.
archivo_mover y archivo_renombrar: valor="origen | destino", ambos datos extraídos literalmente.
ventana_minimizar, ventana_maximizar, ventana_cerrar: valor es parte literal del título o nombre de la aplicación.
ventana_listar y equipo_apagar, equipo_reiniciar, equipo_cancelar_apagado: valor vacío.
programa_listar: valor vacío para listar aplicaciones instaladas; programa_abrir: nombre literal de otra aplicación instalada fuera de las apps de la lista básica.
No confirmes borrados ni cierres: el ejecutor SIEMPRE preguntará. "sí" no es una nueva orden de borrar.
No inventes rutas, nombres, aplicaciones o argumentos. Nada de código, scripts o comandos.'''


def validar(accion,valor,texto):
    if accion not in ACCIONES or not isinstance(valor,str):return False
    n=normalizar(texto)
    if accion in ('ventana_listar','programa_listar','equipo_apagar','equipo_reiniciar','equipo_cancelar_apagado'):
        claves={'programa_listar':('programas','aplicaciones'),'ventana_listar':('ventanas','aplicaciones abiertas'),'equipo_apagar':('apaga','apagar'),
                'equipo_reiniciar':('reinicia','reiniciar'),'equipo_cancelar_apagado':('cancela','cancelar')}
        return not valor and any(k in n for k in claves[accion])
    if valor=='seleccionado':return bool(re.search(r'\b(?:seleccionad[oa]|esta imagen|este archivo)\b',n))
    partes=valor.split(' | ') if accion in ('archivo_mover','archivo_renombrar') else [valor]
    if len(partes)!=(2 if accion in ('archivo_mover','archivo_renombrar') else 1):return False
    return all(p.strip() and normalizar(p.strip()) in n and not any(ord(c)<32 for c in p) for p in partes)


def seleccionado():
    script="""[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$s=New-Object -ComObject Shell.Application
$r=@();foreach($w in $s.Windows()){try{foreach($i in $w.Document.SelectedItems()){$r+=$i.Path}}catch{}}
ConvertTo-Json -InputObject @($r) -Compress"""
    import base64,json
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],
                     capture_output=True,text=True,encoding='utf8',errors='replace',timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if r.returncode:raise OSError('No pude consultar la selección del Explorador.')
    rutas=json.loads(r.stdout or '[]')
    if len(rutas)!=1:raise ValueError('Selecciona un solo archivo en el Explorador y vuelve a pedirlo.')
    return Path(rutas[0])


def huella(ruta):
    s=ruta.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)


def reciclar(ruta):
    # Backend moderno obligatorio: RECYCLEONDELETE, sin fallback a borrado permanente.
    from send2trash.win.modern import send2trash
    if str(ruta).startswith('\\\\'):raise ValueError('No envío archivos de red a la Papelera.')
    send2trash(str(ruta))
    if ruta.exists():raise OSError('Windows no confirmó que el archivo saliera de esa ruta.')


@dataclass
class Pendiente:
    accion:str
    ruta:object
    identidad:object
    destino:object
    vence:float


class ControlPC:
    def __init__(self,habilitado,raices=None,basura=None,reloj=None):
        self.habilitado=habilitado;self.basura=basura or reciclar;self.reloj=reloj or time.monotonic
        self.raices=raices;self.pendiente=None;self.lock=threading.RLock()

    def cancelar(self):
        with self.lock:self.pendiente=None

    def carpetas(self):
        if self.raices is not None:return self.raices
        from escritorio import carpeta_usuario
        return [carpeta_usuario(n) for n in ('Pictures','Desktop','Downloads','Documents','Music','Videos')]

    def buscar(self,nombre):
        # Búsqueda de nombre acotada, no se lee contenido ni se sigue enlaces.
        encontrados=[];limite=self.reloj()+3;vistos=0
        for raiz in self.carpetas():
            for carpeta,dirs,files in os.walk(raiz,followlinks=False):
                dirs[:]=[d for d in dirs if not d.startswith('.') and d not in ('node_modules','venv','AppData') and not Path(carpeta,d).is_symlink()]
                for n in files+dirs:
                    vistos+=1
                    if self.reloj()>limite or vistos>20000:return encontrados
                    if normalizar(nombre) in normalizar(n):
                        encontrados.append(Path(carpeta,n))
                        if len(encontrados)>=12:return encontrados
        return encontrados

    def resolver(self,valor,nuevo=False):
        if valor=='seleccionado':ruta=seleccionado()
        else:
            v=valor.strip().strip('"«»');ruta=Path(os.path.expandvars(os.path.expanduser(v)))
            alias={'imagenes':'Pictures','fotos':'Pictures','escritorio':'Desktop','documentos':'Documents','descargas':'Downloads','musica':'Music','videos':'Videos'}
            if normalizar(v) in alias and self.raices is None:
                from escritorio import carpeta_usuario
                ruta=carpeta_usuario(alias[normalizar(v)])
            elif not ruta.is_absolute():
                candidatos=self.buscar(v)
                exactos=[p for p in candidatos if normalizar(p.name)==normalizar(v)]
                candidatos=exactos or candidatos
                if len(candidatos)!=1:raise ValueError('Necesito la ruta completa de un solo archivo. Coincidencias: '+('; '.join(str(p) for p in candidatos[:4]) or 'ninguna')+'.')
                ruta=candidatos[0]
        if ruta.is_symlink():raise ValueError('Indica el archivo real, no un enlace.')
        ruta=ruta.resolve(strict=not nuevo)
        if not ruta.is_absolute() or ruta==Path(ruta.anchor):raise ValueError('Indica un archivo o carpeta concreto.')
        return ruta

    def confirmar(self,texto):
        with self.lock:
            pendiente=self.pendiente
            if not pendiente:return None
            self.pendiente=None
            n=' '.join(re.sub(r'[,;:]',' ',normalizar(texto)).strip(' .!¡¿?').split())
            if not self.habilitado():return 'Control ampliado desactivado. Cancelé la operación.'
            if self.reloj()>pendiente.vence:return 'La confirmación caducó. Pídeme de nuevo la operación.'
            if n not in ('si','si eliminar','si borralo','si borrala','si estoy seguro','si estoy segura','confirmo','si confirmo','si hazlo'):
                if n in ('no','cancelar','cancela','no lo hagas','dejalo','no gracias'):return 'Cancelado. No hice cambios.'
                return None
            if pendiente.accion.startswith('equipo_'):return self.energia(pendiente.accion)
            if pendiente.accion=='ventana_cerrar':
                from ventanas import visibles,controlar
                actual=next((v for v in visibles() if v['id']==pendiente.ruta['id'] and v['titulo']==pendiente.ruta['titulo']),None)
                if not actual:return 'Esa ventana cambió. Solicita el cierre de nuevo.'
                return controlar(pendiente.accion,actual)
            ruta=pendiente.ruta
            if not ruta.exists() or ruta.is_symlink() or huella(ruta)!=pendiente.identidad:
                return 'El archivo cambió desde que pedí confirmación. No hice cambios; vuelve a solicitarlo.'
            if pendiente.accion=='archivo_borrar':
                self.basura(ruta);return 'Envié a la Papelera: '+str(ruta)
            destino=pendiente.destino
            if destino.exists():return 'El destino ya existe. No sobrescribí nada.'
            if not destino.parent.is_dir():return 'La carpeta de destino ya no existe.'
            # rename no sustituye archivos existentes en Windows.
            ruta.rename(destino);return 'Archivo trasladado a: '+str(destino)

    def energia(self,accion):
        if not self.habilitado():raise PermissionError('Control ampliado desactivado.')
        parametros={'equipo_apagar':['/s','/t','60'],'equipo_reiniciar':['/r','/t','60'],'equipo_cancelar_apagado':['/a']}[accion]
        r=subprocess.run(['shutdown.exe',*parametros],capture_output=True,timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if r.returncode:raise OSError('Windows no aceptó la solicitud de apagado o reinicio.')
        return 'Cancelé el apagado pendiente.' if accion=='equipo_cancelar_apagado' else 'Windows lo realizará en 60 segundos. Puedes pedirme cancelar el apagado.'

    def ejecutar(self,accion,valor):
        with self.lock:
            if not self.habilitado():raise PermissionError('Activa Control ampliado en Ajustes para esa operación.')
            self.pendiente=None
            if accion not in ACCIONES:raise ValueError('Operación no disponible.')
            if accion.startswith('programa_'):
                import base64,json
                script="[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false); @(Get-StartApps | Select-Object Name,AppID) | ConvertTo-Json -Compress"
                r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],
                                 capture_output=True,text=True,encoding='utf8',errors='replace',timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if r.returncode:raise OSError('No pude consultar las aplicaciones instaladas.')
                apps=json.loads(r.stdout or '[]');apps=[apps] if isinstance(apps,dict) else apps
                if accion=='programa_listar':return 'Aplicaciones instaladas: '+('; '.join(a['Name'] for a in apps[:60]) or 'ninguna disponible')
                opciones=[a for a in apps if normalizar(a['Name'])==normalizar(valor)]
                if not opciones:opciones=[a for a in apps if normalizar(valor) in normalizar(a['Name'])]
                if len(opciones)!=1:return 'Necesito un nombre más preciso. Coincidencias: '+('; '.join(a['Name'] for a in opciones[:8]) or 'ninguna')
                app=opciones[0];subprocess.Popen(['explorer.exe','shell:AppsFolder\\'+app['AppID']],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                return 'Solicité abrir '+app['Name']+'.'
            if accion.startswith('equipo_'):
                if accion=='equipo_cancelar_apagado':return self.energia(accion)
                self.pendiente=Pendiente(accion,None,None,None,self.reloj()+120)
                return '¿Confirmas '+('apagar' if accion=='equipo_apagar' else 'reiniciar')+' el computador? Guarda tu trabajo. Responde «sí, confirmo» o «cancelar».'
            if accion.startswith('ventana_'):
                from ventanas import visibles,controlar
                ventanas=visibles()
                if accion=='ventana_listar':return 'Ventanas abiertas: '+('; '.join(v['titulo'] for v in ventanas[:15]) or 'ninguna')
                coincidencias=[v for v in ventanas if normalizar(valor) in normalizar(v['titulo'])]
                if len(coincidencias)!=1:return 'Necesito un título de ventana más preciso. Coincidencias: '+('; '.join(v['titulo'] for v in coincidencias[:5]) or 'ninguna')
                v=coincidencias[0]
                if accion!='ventana_cerrar':return controlar(accion,v)
                self.pendiente=Pendiente(accion,v,None,None,self.reloj()+120)
                return '¿Confirmas cerrar «'+v['titulo']+'»? Puede contener trabajo sin guardar. Responde «sí, confirmo» o «cancelar».'
            if accion=='archivo_buscar':
                return 'Encontré: '+('; '.join(str(p) for p in self.buscar(valor)) or 'ninguna coincidencia')
            partes=valor.split(' | ');ruta=self.resolver(partes[0],nuevo=accion=='archivo_crear_carpeta')
            if accion=='archivo_abrir':
                formatos=('.png','.jpg','.jpeg','.bmp','.gif','.webp','.txt','.md','.pdf','.mp3','.wav','.mp4','.mkv',
                          '.docx','.xlsx','.pptx','.csv','.json','.log','.rtf','.odt','.ods')
                if ruta.is_file() and ruta.suffix.lower() not in formatos:
                    return 'Esta función abre documentos y medios. Para abrir aplicaciones, pídeme su nombre instalado.'
                os.startfile(str(ruta));return 'Abrí '+str(ruta)
            if accion=='archivo_listar':
                if not ruta.is_dir():return 'Esa ruta no es una carpeta.'
                return 'Contenido de '+str(ruta)+': '+('; '.join(p.name for p in list(ruta.iterdir())[:40]) or 'vacía')
            if accion=='archivo_leer':
                if not ruta.is_file() or ruta.stat().st_size>100000:return 'Puedo leer archivos de texto de hasta 100 KB.'
                return ruta.read_text(encoding='utf8')[:6000]
            if accion=='archivo_crear_carpeta':
                ruta.mkdir(exist_ok=False);return 'Creé la carpeta '+str(ruta)
            if not ruta.is_file():return 'Esta operación requiere un archivo individual.'
            destino=None
            if accion in ('archivo_mover','archivo_renombrar'):
                if len(partes)!=2:raise ValueError('Falta el destino de la operación.')
                destino=Path(partes[1].strip().strip('"«»'))
                if accion=='archivo_renombrar':
                    if destino.name!=str(destino) or destino.name in ('','.','..'):raise ValueError('El nombre nuevo debe ser solo un nombre de archivo.')
                    destino=ruta.with_name(destino.name)
                else:destino=self.resolver(partes[1],nuevo=True)
                if destino.exists():raise ValueError('El destino ya existe; no lo sobrescribiré.')
            self.pendiente=Pendiente(accion,ruta,huella(ruta),destino,self.reloj()+120)
            detalle='enviar a la Papelera' if accion=='archivo_borrar' else 'trasladar a '+str(destino)
            return '¿Confirmas '+detalle+' este archivo?\n'+str(ruta)+'\nResponde «sí, confirmo» o «cancelar». No hice cambios todavía.'
