"""Ventanas visibles de Windows, sin inspeccionar contenido ni capturar pantalla."""
import os
import ctypes
from ctypes import wintypes as w


def area_trabajo():
    if os.name!='nt':return (0,0,1920,1040)
    rect=w.RECT()
    if ctypes.windll.user32.SystemParametersInfoW(0x30,0,ctypes.byref(rect),0):
        return (rect.left,rect.top,rect.right,rect.bottom)
    return (0,0,ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1))


def visibles():
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
        if pid.value==os.getpid():return True
        clase=ctypes.create_unicode_buffer(256);u.GetClassNameW(hwnd,clase,256)
        if clase.value in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):return True
        oculto=w.DWORD()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(w.HWND(hwnd),14,ctypes.byref(oculto),4)==0 and oculto.value:return True
        r=w.RECT()
        if not u.GetWindowRect(hwnd,ctypes.byref(r)) or r.right-r.left<180 or r.bottom-r.top<100:return True
        n=u.GetWindowTextLengthW(hwnd);texto=ctypes.create_unicode_buffer(n+1);u.GetWindowTextW(hwnd,texto,n+1)
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
