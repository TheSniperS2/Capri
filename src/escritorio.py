"""Acciones acotadas de Windows; datos del usuario separados del código."""
from pathlib import Path
from urllib.parse import quote
import base64
import json
import os
import subprocess

HIDDEN=getattr(subprocess,'CREATE_NO_WINDOW',0)

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
 $limite=[DateTime]::UtcNow.AddSeconds(12)
 $invocado=$false
 $nombre=''
 while ([DateTime]::UtcNow -lt $limite) {
   $pids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
   $raices=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
   foreach ($raiz in $raices) {
    if ($raiz.Current.ProcessId -notin $pids) {continue}
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

def controlar_spotify(consulta='',accion='reproducir',abrir=None,correr=None):
    if accion not in ('reproducir','buscar','pausa'):raise ValueError('Acción de Spotify desconocida.')
    if accion=='pausa' or (accion=='reproducir' and not consulta.strip()):
        from multimedia import controlar_sesion
        return controlar_sesion('pausa' if accion=='pausa' else 'reanudar',correr=correr)
    abrir=abrir or getattr(os,'startfile',None)
    if abrir is None:raise OSError('Spotify necesita Windows.')
    consulta=consulta.strip()[:500]
    if accion!='pausa':
        abrir('spotify:search:'+quote(consulta,safe='') if consulta else 'spotify:')
    if accion=='buscar':return 'Abrí la búsqueda de «'+consulta+'» en Spotify.'
    correr=correr or subprocess.run
    encoded=base64.b64encode(SPOTIFY_UI.encode('utf-16-le')).decode('ascii')
    try:
        resultado=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                         input=json.dumps({'consulta':consulta,'accion':accion}),text=True,
                         encoding='utf-8',errors='replace',capture_output=True,timeout=18,creationflags=HIDDEN)
        datos=json.loads(resultado.stdout.strip())
        if resultado.returncode==0 and datos.get('ok') is True:
            return 'Pausé Spotify.' if accion=='pausa' else 'Activé la reproducción en Spotify'+(' de «'+consulta+'».' if consulta else '.')
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    if consulta:return 'Abrí la búsqueda de «'+consulta+'» en Spotify, pero no pude confirmar la reproducción desde sus controles.'
    return 'No pude confirmar el control de reproducción. Spotify debe estar abierto, con la sesión iniciada y sus controles disponibles.'
