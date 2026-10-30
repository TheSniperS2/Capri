"""Ventanas visibles de Windows, sin inspeccionar contenido ni capturar pantalla."""
import os
import ctypes
from ctypes import wintypes as w
APOYOS_PROPIOS=set()


def registrar_apoyo(ventana):
    if os.name!='nt':return
    ventana.update_idletasks();u=ctypes.windll.user32
    u.GetAncestor.argtypes=[w.HWND,w.UINT];u.GetAncestor.restype=w.HWND
    hwnd=int(u.GetAncestor(w.HWND(ventana.winfo_id()),2) or ventana.winfo_id())
    APOYOS_PROPIOS.add(hwnd)
    def retirar(evento):
        if evento.widget==ventana:APOYOS_PROPIOS.discard(hwnd)
    ventana.bind('<Destroy>',retirar,add='+')

def preparar_no_activar(ventana):
    """Windows no debe activar este aviso ni añadirlo a Alt+Tab."""
    if os.name!='nt':return None
    ventana.update_idletasks();u=ctypes.windll.user32
    u.GetAncestor.argtypes=[w.HWND,w.UINT];u.GetAncestor.restype=w.HWND
    hwnd=u.GetAncestor(w.HWND(ventana.winfo_id()),2) or ventana.winfo_id()
    get=u.GetWindowLongPtrW;set_=u.SetWindowLongPtrW
    get.argtypes=[w.HWND,ctypes.c_int];get.restype=ctypes.c_ssize_t
    set_.argtypes=[w.HWND,ctypes.c_int,ctypes.c_ssize_t];set_.restype=ctypes.c_ssize_t
    set_(hwnd,-20,(get(hwnd,-20)|0x08000000|0x80)&~0x40000)
    return hwnd


def mostrar_no_activar(ventana):
    hwnd=preparar_no_activar(ventana);ventana.deiconify()
    if hwnd and ventana.state()!='withdrawn':
        u=ctypes.windll.user32;u.ShowWindow.argtypes=[w.HWND,ctypes.c_int]
        u.SetWindowPos.argtypes=[w.HWND,w.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.UINT]
        u.ShowWindow(hwnd,4)
        u.SetWindowPos(hwnd,w.HWND(-1),0,0,0,0,0x0010|0x0001|0x0002|0x0040)


def area_trabajo():
    if os.name!='nt':return (0,0,1920,1040)
    rect=w.RECT()
    if ctypes.windll.user32.SystemParametersInfoW(0x30,0,ctypes.byref(rect),0):
        return (rect.left,rect.top,rect.right,rect.bottom)
    return (0,0,ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1))


def apoyo_propio_permitido(titulo):
    return titulo.startswith(('Capri · Ajustes','Capri · Aspectos','Capri // Aspectos','Capri · Conversación','Capri · Playlists','Capri · YouTube','Conectar YouTube con Opera'))


def visibles(incluir_propias=False):
    if os.name!='nt':return []
    u=ctypes.windll.user32;salida=[]
    u.IsWindowVisible.argtypes=[w.HWND];u.IsIconic.argtypes=[w.HWND]
    u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
    u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    u.GetWindowTextLengthW.argtypes=[w.HWND];u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    def ver(hwnd,param):
        if not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd):return True
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        propia=pid.value==os.getpid()
        if propia and not incluir_propias:return True
        clase=ctypes.create_unicode_buffer(256);u.GetClassNameW(hwnd,clase,256)
        if clase.value in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):return True
        oculto=w.DWORD()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(w.HWND(hwnd),14,ctypes.byref(oculto),4)==0 and oculto.value:return True
        r=w.RECT()
        if not u.GetWindowRect(hwnd,ctypes.byref(r)) or r.right-r.left<180 or r.bottom-r.top<100:return True
        n=u.GetWindowTextLengthW(hwnd);texto=ctypes.create_unicode_buffer(n+1);u.GetWindowTextW(hwnd,texto,n+1)
        if propia and int(hwnd) not in APOYOS_PROPIOS and not apoyo_propio_permitido(texto.value):return True
        if texto.value:salida.append({'id':int(hwnd),'titulo':texto.value,'rect':(r.left,r.top,r.right,r.bottom)})
        return True
    cb=callback(ver);u.EnumWindows.argtypes=[callback,w.LPARAM];u.EnumWindows(cb,0)
    return salida


def controlar(accion,ventana):
    if os.name!='nt':raise OSError('Este control necesita Windows.')
    u=ctypes.windll.user32;hwnd=w.HWND(ventana['id'])
    if not u.IsWindow(hwnd):raise OSError('Esa ventana ya no está abierta.')
    if accion=='ventana_cerrar':
        u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        if not u.PostMessageW(hwnd,0x10,0,0):raise OSError('Windows no permitió cerrar la ventana.')
        return 'Envié la solicitud de cierre a «'+ventana['titulo']+'». La aplicación puede pedir guardar cambios.'
    u.ShowWindow.argtypes=[w.HWND,ctypes.c_int]
    u.ShowWindow(hwnd,6 if accion=='ventana_minimizar' else 3)
    return ('Minimicé' if accion=='ventana_minimizar' else 'Maximicé')+' «'+ventana['titulo']+'».'


def activa():
    if os.name!='nt':return None
    u=ctypes.windll.user32;u.GetForegroundWindow.restype=w.HWND
    hwnd=int(u.GetForegroundWindow() or 0)
    ventana=next((v for v in visibles() if v['id']==hwnd),None)
    if ventana:
        pid=w.DWORD();u.GetWindowThreadProcessId(w.HWND(hwnd),ctypes.byref(pid));ventana['pid']=pid.value
    return ventana


def minimizar_travesura(ventana):
    actual=activa()
    if not actual or actual['id']!=ventana['id']:return False
    controlar('ventana_minimizar',actual)
    u=ctypes.windll.user32;u.IsIconic.argtypes=[w.HWND]
    return bool(u.IsIconic(w.HWND(ventana['id'])))


def restaurar_travesura(ventana,activar=True):
    if os.name!='nt':return
    u=ctypes.windll.user32;u.IsWindow.argtypes=[w.HWND];u.IsIconic.argtypes=[w.HWND]
    hwnd=w.HWND(ventana['id'])
    if u.IsWindow(hwnd) and u.IsIconic(hwnd):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if ventana.get('pid') is not None and pid.value!=ventana['pid']:return
        u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];u.ShowWindow(hwnd,9 if activar else 4)
