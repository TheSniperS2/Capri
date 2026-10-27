"""Controla la sesión multimedia de Spotify sin cambiar su cola ni sus búsquedas."""
import base64
import json
import subprocess

MEDIA_PS=r'''
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName System.Runtime.WindowsRuntime
 $tipo=[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]
 $tipoMedia=[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties,Windows.Media.Control,ContentType=WindowsRuntime]
 $asTask=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1
 function Esperar($operacion,[Type]$tipoResultado) {
   $tarea=$asTask.MakeGenericMethod($tipoResultado).Invoke($null,@($operacion))
   if (-not $tarea.Wait(4000)) {throw 'Spotify no respondió a tiempo.'}
   return $tarea.Result
 }
 $datos=[Console]::In.ReadToEnd()|ConvertFrom-Json
 $gestor=Esperar ($tipo::RequestAsync()) $tipo
 $sesion=$gestor.GetSessions()|Where-Object {$_.SourceAppUserModelId -match '(?i)spotify'}|Select-Object -First 1
 if (-not $sesion) {@{ok=$false;error='No hay una sesión multimedia de Spotify disponible.'}|ConvertTo-Json -Compress;exit 0}
 $ok=$true
 switch ($datos.accion) {
  'reanudar' {$ok=Esperar ($sesion.TryPlayAsync()) ([bool])}
  'pausa' {$ok=Esperar ($sesion.TryPauseAsync()) ([bool])}
  'siguiente' {$ok=Esperar ($sesion.TrySkipNextAsync()) ([bool])}
  'anterior' {$ok=Esperar ($sesion.TrySkipPreviousAsync()) ([bool])}
  'estado' {}
  default {throw 'Acción desconocida.'}
 }
 if ($datos.accion -ne 'estado') {Start-Sleep -Milliseconds 400}
 $estado=$sesion.GetPlaybackInfo().PlaybackStatus.ToString()
 $titulo='';$artista=''
 try {$media=Esperar ($sesion.TryGetMediaPropertiesAsync()) $tipoMedia;$titulo=$media.Title;$artista=$media.Artist} catch {}
 @{ok=[bool]$ok;estado=$estado;titulo=$titulo;artista=$artista}|ConvertTo-Json -Compress
} catch {@{ok=$false;error='No pude acceder a la sesión multimedia de Spotify.'}|ConvertTo-Json -Compress}
'''

def sesion_spotify(accion='estado',correr=None):
    if accion not in ('estado','reanudar','pausa','siguiente','anterior'):raise ValueError('Acción multimedia desconocida.')
    correr=correr or subprocess.run
    encoded=base64.b64encode(MEDIA_PS.encode('utf-16-le')).decode('ascii')
    try:
        r=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                 input=json.dumps({'accion':accion}),text=True,encoding='utf-8',errors='replace',capture_output=True,
                 timeout=16,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        datos=json.loads(r.stdout.strip())
        if r.returncode==0 and isinstance(datos,dict):return datos
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    return {'ok':False,'error':'No pude acceder a la sesión multimedia de Spotify.'}

def controlar_sesion(accion,correr=None):
    datos=sesion_spotify(accion,correr)
    if not datos.get('ok'):return datos.get('error','Spotify no confirmó la acción.')+' Abre Spotify y selecciona una canción primero.'
    if accion=='reanudar':
        return 'Reanudé la reproducción que estaba puesta en Spotify.' if datos.get('estado')=='Playing' else 'Pedí reanudar Spotify, pero todavía no confirmó que esté reproduciendo.'
    if accion=='pausa':
        return 'Pausé Spotify.' if datos.get('estado')=='Paused' else 'Pedí pausar Spotify, pero todavía no confirmó la pausa.'
    if accion=='siguiente':return 'Pedí a Spotify pasar a la siguiente canción de la cola actual.'
    if accion=='anterior':return 'Pedí a Spotify volver a la canción anterior de la cola actual.'
    titulo=datos.get('titulo','').strip();artista=datos.get('artista','').strip()
    if not titulo:return 'Spotify no comunicó el nombre de la canción actual.'
    estado={'Playing':'Está sonando','Paused':'Está pausada'}.get(datos.get('estado'),'Spotify tiene seleccionada')
    return estado+' «'+titulo+'»'+(' de '+artista if artista else '')+'.'
