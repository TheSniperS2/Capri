"""Playlists de la cuenta iniciada: biblioteca local o enlace vinculado por nombre."""
from pathlib import Path
from urllib.parse import urlsplit
import base64
import json
import os
import re
import subprocess
import unicodedata
from escritorio import HIDDEN

BASE=Path(__file__).resolve().parent

def clave(nombre):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD',nombre.casefold()) if unicodedata.category(c)!='Mn').split())

def uri_playlist(enlace):
    enlace=enlace.strip()
    if re.fullmatch(r'spotify:playlist:[A-Za-z0-9]{22}',enlace):return enlace
    p=urlsplit(enlace)
    if p.scheme=='https' and p.hostname=='open.spotify.com' and not p.username and not p.password:
        m=re.fullmatch(r'/(?:intl-[a-z]{2}/)?playlist/([A-Za-z0-9]{22})/?',p.path)
        if m:return 'spotify:playlist:'+m[1]
    raise ValueError('Pega el enlace de una playlist de open.spotify.com o su URI spotify:playlist:.')

def cargar(carpeta=None):
    try:
        datos=((carpeta or BASE)/'playlists.json').read_text(encoding='utf-8')
        valor=json.loads(datos)
        return valor if isinstance(valor,dict) else {}
    except (OSError,ValueError):return {}

def vincular(nombre,enlace,carpeta=None):
    if not nombre.strip():raise ValueError('Falta el nombre de la playlist.')
    uri=uri_playlist(enlace)
    listas=cargar(carpeta);listas[clave(nombre)]=uri
    ((carpeta or BASE)/'playlists.json').write_text(json.dumps(listas,ensure_ascii=False,indent=2),encoding='utf-8')

# Descubrir por nombre en Tu biblioteca; nunca buscar una playlist privada en
# los resultados públicos. Solo se invocan controles de procesos Spotify.
BIBLIOTECA_PS=r'''
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $d=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function N([string]$s) {return [regex]::Replace($s.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD),'\p{Mn}','')}
 function Invocar($e) {
  $p=$null
  if($e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)) {$p.Invoke();return $true}
  if($e.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)) {$p.Select();return $true}
  return $false
 }
 $limite=[DateTime]::UtcNow.AddSeconds(10);$filtrada=$false
 while([DateTime]::UtcNow -lt $limite) {
  $ids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $ventanas=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
  foreach($v in $ventanas) {
   if($v.Current.ProcessId -notin $ids) {continue}
   $elementos=$v.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $biblioteca=$null
   foreach($e in $elementos) {
    if ((N $e.Current.Name) -match '^(tu biblioteca|your library)$' -and $e.Current.ControlType.ProgrammaticName -match '(Pane|Group|List|Tree)$') {$biblioteca=$e;break}
   }
   if (-not $biblioteca) {continue}
   $items=$biblioteca.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   if(-not $filtrada -and -not $d.uri) {
    foreach($e in $items) {
     if ((N $e.Current.Name) -match '(buscar en (tu |la )?biblioteca|search (in )?your library)') {
      $p=$null
      if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p) -and -not $p.Current.IsReadOnly) {$p.SetValue($d.nombre);$filtrada=$true;break}
      if($e.Current.ControlType -eq [Windows.Automation.ControlType]::Button) {[void](Invocar $e)}
     }
    }
   }
   $candidatos=@()
   foreach($e in $items) {
    $nombre=N $e.Current.Name;$buscado=N $d.nombre
    if($d.uri){
     $p=$null;$enlace=''
     if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p)){$enlace=$p.Current.Value}
     elseif($e.TryGetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$p)){$enlace=$p.Current.Value}
     $id=($d.uri -split ':')[-1]
     if($enlace -match ('playlist[:/]'+[regex]::Escape($id)+'(?:[/?]|$)')){$candidatos+=,$e}
     continue
    }
    if(($nombre -eq $buscado -or $nombre.StartsWith($buscado+' Playlist') -or $nombre.StartsWith($buscado+' playlist') -or $nombre.StartsWith($buscado+' Lista') -or $nombre.StartsWith($buscado+' lista')) -and $e.Current.ControlType.ProgrammaticName -match '(ListItem|TreeItem|Hyperlink|Button)$') {$candidatos+=,$e}
   }
   if($candidatos.Count -eq 1 -and (Invocar $candidatos[0])) {@{ok=$true}|ConvertTo-Json -Compress;exit 0}
  }
  Start-Sleep -Milliseconds 250
 }
 @{ok=$false}|ConvertTo-Json -Compress
} catch {@{ok=$false}|ConvertTo-Json -Compress}
'''

# El alias vinculado puede ser distinto del título real (incluso ser emojis).
# Usar el título y los controles de la página de playlist, nunca el reproductor
# global ni los botones de canciones individuales.
PLAYLIST_UI=r'''
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $datos=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function Coincide([string]$nombre,[string]$titulo,[bool]$pausa) {
  $prefijo=if($pausa){'^(?:Pausar|Pause)\s+'}else{'^(?:Reproducir|Play)\s+'}
  return $nombre -match ($prefijo+[regex]::Escape($titulo)+'$')
 }
 $limite=[DateTime]::UtcNow.AddSeconds(12)
 $tituloAnterior='';$estable=0;$invocado=$false;$tituloInvocado=''
 while([DateTime]::UtcNow -lt $limite) {
  $ids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $ventanas=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
  foreach($v in $ventanas) {
   if($v.Current.ProcessId -notin $ids){continue}
   $grupos=$v.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $paginas=@()
   foreach($g in $grupos) {
    if($g.Current.ControlType -eq [Windows.Automation.ControlType]::Group -and $g.Current.Name -match '^(.+) - (?:playlist by|playlist de|lista de reproducci[oó]n de) .+ \| Spotify$') {
     $paginas+=,@{grupo=$g;titulo=$Matches[1]}
    }
   }
   if($paginas.Count -ne 1){continue}
   $pagina=$paginas[0];$titulo=$pagina.titulo
   if($titulo -eq $tituloAnterior){$estable++}else{$tituloAnterior=$titulo;$estable=0}
   # Esperar que la navegación deje de cambiar antes de invocar el botón.
   if($estable -lt 3){continue}
   $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
   $botones=$pagina.grupo.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
   $play=@();$pausa=@()
   foreach($b in $botones){
    if(-not $b.Current.IsEnabled){continue}
    if(Coincide $b.Current.Name $titulo $false){$play+=,$b}
    if(Coincide $b.Current.Name $titulo $true){$pausa+=,$b}
   }
   if($datos.solo_inspeccionar){@{ok=($play.Count -eq 1 -or $pausa.Count -eq 1);titulo=$titulo;reproducir=$play.Count;pausar=$pausa.Count}|ConvertTo-Json -Compress;exit 0}
   if($pausa.Count -eq 1 -and (-not $invocado -or $titulo -eq $tituloInvocado)){
    @{ok=$true;titulo=$titulo}|ConvertTo-Json -Compress;exit 0
   }
   if(-not $invocado -and $play.Count -eq 1){
    $patron=$null
    if($play[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$patron)){
     $patron.Invoke();$invocado=$true;$tituloInvocado=$titulo
    }
   }
  }
  Start-Sleep -Milliseconds 300
 }
 @{ok=$false}|ConvertTo-Json -Compress
} catch {@{ok=$false}|ConvertTo-Json -Compress}
'''

def ejecutar_ui(script,datos,correr):
    codigo=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    r=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',codigo],
             input=json.dumps(datos),text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=18,creationflags=HIDDEN)
    valor=json.loads(r.stdout.strip())
    return r.returncode==0 and isinstance(valor,dict) and valor.get('ok') is True

def reproducir_playlist(nombre,carpeta=None,abrir=None,correr=None):
    correr=correr or subprocess.run
    listas=cargar(carpeta);uri=listas.get(clave(nombre));abierta=False
    try:
        # Sin URI de apertura: no sacar al usuario de un juego a pantalla completa.
        abierta=ejecutar_ui(BIBLIOTECA_PS,{'nombre':nombre,'uri':uri_playlist(uri) if uri else ''},correr)
        if abierta and ejecutar_ui(PLAYLIST_UI,{'consulta':nombre,'accion':'playlist'},correr):
            return 'Activé la reproducción de la playlist «'+nombre+'» en Spotify.'
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    if abierta:return 'Abrí la playlist «'+nombre+'», pero Spotify no confirmó la reproducción.'
    return 'No encontré «'+nombre+'» en Tu biblioteca. Puedes vincular su enlace en Ajustes → Playlists de Spotify; no necesitas hacerla pública.'
