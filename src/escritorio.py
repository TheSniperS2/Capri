"""Acciones acotadas de Windows; datos del usuario separados del código."""
from pathlib import Path
from urllib.parse import quote
import base64
import json
import os
import subprocess

HIDDEN=getattr(subprocess,'CREATE_NO_WINDOW',0)


def foco_protegido(nombre,rect,monitor):
    """No activar Spotify sobre juegos conocidos ni aplicaciones a pantalla completa."""
    juegos={'league of legends.exe','leagueclient.exe','leagueclientux.exe','valorant-win64-shipping.exe',
            'cs2.exe','dota2.exe','fortniteclient-win64-shipping.exe','gta5.exe'}
    if nombre.lower() in juegos:return True
    if nombre.lower() in ('spotify.exe','explorer.exe'):return False
    x,y,d,b=rect;mx,my,md,mb=monitor
    return x<=mx+2 and y<=my+2 and d>=md-2 and b>=mb-2


def proteger_foco():
    """Consulta solo geometría y ejecutable del primer plano, sin cambiar ventanas."""
    if os.name!='nt':return True
    import ctypes
    from ctypes import wintypes as w
    try:
        u=ctypes.windll.user32;k=ctypes.windll.kernel32
        u.GetForegroundWindow.restype=w.HWND
        hwnd=u.GetForegroundWindow()
        if not hwnd:return True
        u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        rect=w.RECT()
        if not u.GetWindowRect(hwnd,ctypes.byref(rect)):return True
        u.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];u.MonitorFromWindow.restype=w.HANDLE
        class Monitor(ctypes.Structure):
            _fields_=[('cbSize',w.DWORD),('rect',w.RECT),('trabajo',w.RECT),('flags',w.DWORD)]
        info=Monitor();info.cbSize=ctypes.sizeof(info)
        u.GetMonitorInfoW.argtypes=[w.HANDLE,ctypes.POINTER(Monitor)]
        if not u.GetMonitorInfoW(u.MonitorFromWindow(hwnd,2),ctypes.byref(info)):return True
        pid=w.DWORD();u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        handle=k.OpenProcess(0x1000,False,pid.value)
        if not handle:return True
        try:
            ruta=ctypes.create_unicode_buffer(32768);longitud=w.DWORD(len(ruta))
            k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
            if not k.QueryFullProcessImageNameW(handle,0,ruta,ctypes.byref(longitud)):return True
            return foco_protegido(Path(ruta.value).name,(rect.left,rect.top,rect.right,rect.bottom),
                                  (info.rect.left,info.rect.top,info.rect.right,info.rect.bottom))
        finally:
            k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle(handle)
    except (OSError,AttributeError,ValueError):return True

def carpeta_usuario(nombre):
    permitidas={'Downloads','Documents','Desktop','Pictures','Music','Videos'}
    if nombre not in permitidas:raise ValueError('Carpeta no reconocida.')
    # Respetar carpetas redirigidas a OneDrive o a otra unidad.
    import winreg
    claves={'Downloads':'{374DE290-123F-4565-9164-39C4925E467B}','Documents':'Personal',
            'Desktop':'Desktop','Pictures':'My Pictures','Music':'My Music','Videos':'My Video'}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            valor=winreg.QueryValueEx(key,claves[nombre])[0]
            return Path(os.path.expandvars(valor))
    except OSError:return Path.home()/nombre

# Solo controles accesibles de procesos Spotify: no enviar teclas a la ventana activa.
# El nombre de canción nunca se concatena como código PowerShell.
SPOTIFY_UI=r'''
$ErrorActionPreference='Stop'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient
 Add-Type -AssemblyName UIAutomationTypes
 $datos=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function Normalizar([string]$t) {
   $s=$t.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
   return [regex]::Replace($s,'\p{Mn}','')
 }
 $limite=[DateTime]::UtcNow.AddSeconds($(if($datos.navegada){12}else{4}))
 $invocado=$false
 $buscada=$false;$buscadorAbierto=$false
 $nombre=''
 while ([DateTime]::UtcNow -lt $limite) {
   $pids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
   $raices=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
   foreach ($raiz in $raices) {
    if ($raiz.Current.ProcessId -notin $pids) {continue}
    if($datos.consulta -and -not $buscada -and -not $datos.navegada){
     $edits=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
     foreach($e in $raiz.FindAll([Windows.Automation.TreeScope]::Descendants,$edits)){
      if((Normalizar $e.Current.Name) -match '(buscar|search|quieres reproducir|want to play)'){
       $vp=$null
       if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp) -and -not $vp.Current.IsReadOnly){
        $vp.SetValue($datos.consulta);$buscada=$true;Start-Sleep -Milliseconds 800;break
       }
      }
     }
     if($buscada -and $datos.accion -eq 'buscar'){@{ok=$true}|ConvertTo-Json -Compress;exit 0}
     if(-not $buscada){
      if(-not $buscadorAbierto){
       $items=$raiz.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
       foreach($e in $items){
        if((Normalizar $e.Current.Name) -match '^(buscar|search)$'){
         $vp=$null
         if($e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$vp)){$vp.Invoke();$buscadorAbierto=$true;break}
        }
       }
      }
      continue
     }
    }
    $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
    $botones=$raiz.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
    foreach ($b in $botones) {
     $n=$b.Current.Name
     if ($invocado) {
       if ((Normalizar $n) -match '^(pausa|pausar|pause)(\s|$)') {
         @{ok=$true;nombre=$nombre}|ConvertTo-Json -Compress;exit 0
       }
       continue
     }
     $elegido=$false
     if ($datos.accion -eq 'pausa') {$elegido=(Normalizar $n) -match '^(pausa|pausar|pause)$'}
     elseif (-not $datos.consulta) {$elegido=(Normalizar $n) -match '^(reproducir|play|reanudar|resume)$'}
     elseif ((Normalizar $n) -match '^(reproducir|play)\s+\S') {
       $tokens=@((Normalizar $datos.consulta) -split '\W+'|Where-Object {$_.Length -gt 1 -and $_ -notin @('de','the','la','el','por','by')})
       $coinciden=@($tokens|Where-Object {(Normalizar $n).Contains($_)})
       $elegido=$tokens.Count -gt 0 -and $coinciden.Count -eq $tokens.Count
     }
     if ($elegido -and $b.Current.IsEnabled) {
       $patron=$null
       if ($b.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$patron)) {
         $patron.Invoke();$invocado=$true;$nombre=$n
         if ($datos.accion -eq 'pausa') {@{ok=$true;nombre=$nombre}|ConvertTo-Json -Compress;exit 0}
         break
       }
     }
    }
   }
   Start-Sleep -Milliseconds 250
 }
 @{ok=$false;nombre=$nombre}|ConvertTo-Json -Compress
} catch {@{ok=$false;error='No pude acceder a los controles de Spotify.'}|ConvertTo-Json -Compress}
'''

def controlar_spotify(consulta='',accion='reproducir',abrir=None,correr=None,proteger=None):
    if accion not in ('reproducir','buscar','pausa'):raise ValueError('Acción de Spotify desconocida.')
    if accion=='pausa' or (accion=='reproducir' and not consulta.strip()):
        from multimedia import controlar_sesion
        return controlar_sesion('pausa' if accion=='pausa' else 'reanudar',correr=correr)
    consulta=consulta.strip()[:500]
    # Intentar primero controles accesibles; URI compatible solo fuera de juegos.
    correr=correr or subprocess.run
    encoded=base64.b64encode(SPOTIFY_UI.encode('utf-16-le')).decode('ascii')
    try:
        resultado=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                         input=json.dumps({'consulta':consulta,'accion':accion}),text=True,
                         encoding='utf-8',errors='replace',capture_output=True,timeout=18,creationflags=HIDDEN)
        datos=json.loads(resultado.stdout.strip())
        if resultado.returncode==0 and datos.get('ok') is True:
            if accion=='buscar':return 'Solicité la búsqueda de «'+consulta+'» en Spotify en segundo plano.'
            return 'Pausé Spotify.' if accion=='pausa' else 'Activé la reproducción en Spotify'+(' de «'+consulta+'».' if consulta else '.')
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    if consulta:
        try:bloqueado=(proteger or proteger_foco)()
        except Exception:bloqueado=True
        if bloqueado:
            return 'La búsqueda en segundo plano no respondió. No abrí su ventana para proteger una posible partida o pantalla completa. Puedes pausar, reanudar o pasar de canción sin salir del juego; para buscar otra por nombre, vuelve al escritorio y repite la petición.'
        abrir=abrir or getattr(os,'startfile',None)
        if abrir is None:raise OSError('Spotify necesita Windows.')
        # Codificación porcentual: %20 para espacios y %2B para un + literal.
        abrir('spotify:search:'+quote(consulta,safe=''))
        if accion=='buscar':return 'Abrí la búsqueda de «'+consulta+'» en Spotify.'
        try:
            r=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                     input=json.dumps({'consulta':consulta,'accion':accion,'navegada':True}),text=True,
                     encoding='utf8',errors='replace',capture_output=True,timeout=18,creationflags=HIDDEN)
            datos=json.loads(r.stdout.strip())
            if r.returncode==0 and datos.get('ok') is True:return 'Activé la reproducción en Spotify de «'+consulta+'».'
        except (OSError,ValueError,subprocess.TimeoutExpired):pass
        return 'Abrí la búsqueda de «'+consulta+'» en Spotify, pero no pude confirmar la reproducción desde sus controles.'
    return 'No pude confirmar el control de reproducción. Spotify debe estar abierto, con la sesión iniciada y sus controles disponibles.'
