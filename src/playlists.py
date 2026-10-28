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

def interpretar_cancion_playlist(texto):
    m=re.fullmatch(r'(?:reproduce|reproducir|pon(?:er|me|ga|gas|e)?|toca|escucha|quiero escuchar)\s+(?:(?:la|una)\s+)?(?:(?:canci[oó]n|tema)\s+)?(.+?)\s+(?:de|en|dentro de)\s+(?:(?:mi|mis|la|las)\s+)?(?:playlist|playlists|lista(?: de reproducci[oó]n)?)\s+(?:llamada\s+)?(.+?)(?:\s+en\s+Spotify)?[.!]?$',texto.strip(),re.I)
    if not m:return None
    cancion,nombre=(v.strip(' «»"\'“”.!') for v in m.groups())
    if not cancion or not nombre or len(cancion)>200 or len(nombre)>200:return None
    return {'cancion':cancion,'nombre':nombre}

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
 function N([string]$s) {return [regex]::Replace([regex]::Replace($s.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD),'\p{Mn}',''),'\s+',' ').Trim()}
 function NombreLista([string]$s,[string]$buscado) {
  $s=N $s;$buscado=N $buscado
  return $s -eq $buscado -or $s -match ('^'+[regex]::Escape($buscado)+'(?:\s+|\s*[•·,|:-]\s*)(?:playlist|lista(?: de reproduccion)?)\b')
 }
 function EsBiblioteca([string]$s) {return (N $s) -match '^(?:tu biblioteca|your library|biblioteca)(?:\s*[,.:•-].*)?$'}
 function EsBusqueda([string]$s) {return (N $s) -match '(buscar en (tu |la )?biblioteca|search (in )?(your )?library)'}
 function Invocar($e) {
  $p=$null
  if($e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)) {$p.Invoke();return $true}
  if($e.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)) {$p.Select();return $true}
  return $false
 }
 function Fila($e,$raiz) {
  $actual=$e;$respaldo=$e;$tieneFila=$false
  for($i=0;$i -lt 20 -and $actual;$i++) {
   if([Windows.Automation.Automation]::Compare($actual,$raiz)){break}
   if($actual.Current.ControlType.ProgrammaticName -match '(ListItem|TreeItem|DataItem)$') {
    if(-not $tieneFila -or (NombreLista $actual.Current.Name $d.nombre)){$respaldo=$actual;$tieneFila=$true}
   } elseif(-not $tieneFila -and (NombreLista $actual.Current.Name $d.nombre) -and $actual.Current.ControlType.ProgrammaticName -match '(Custom|Group|Button|Hyperlink)$'){$respaldo=$actual}
   $actual=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($actual)
  }
  return $respaldo
 }
 function UriLista([string]$s) {
  if($s -cmatch '^spotify:playlist:([A-Za-z0-9]{22})$'){return 'spotify:playlist:'+$Matches[1]}
  if($s -cmatch '^https://open\.spotify\.com/(?:intl-[a-z]{2}/)?playlist/([A-Za-z0-9]{22})(?:[/?].*)?$'){return 'spotify:playlist:'+$Matches[1]}
  return ''
 }
 function Enlace($e) {
  $p=$null;$enlace=''
  if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p)){$enlace=UriLista $p.Current.Value}
  return $enlace
 }
 function Accionable($e) {
  if(-not $e.Current.IsEnabled){return $false}
  $p=$null
  if($e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){return $true}
  if($e.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)){return $true}
  return $false
 }
 function Agrupar($entradas) {
  # La URI identifica una playlist; RuntimeId solo identifica un control.
  # Se conserva la distinción de filas desconocidas: no elegir por azar.
  $porFila=@{};$grupos=New-Object 'System.Collections.Generic.Dictionary[string,object]' ([StringComparer]::Ordinal)
  foreach($e in $entradas){if($e.uri){$porFila[$e.llave]=$e.uri}}
  foreach($e in $entradas) {
   $uri=$e.uri;if(-not $uri -and $porFila.ContainsKey($e.llave)){$uri=$porFila[$e.llave]}
   $llave=if($uri){$uri}else{'fila:'+$e.llave}
   if(-not $grupos.ContainsKey($llave)){$grupos[$llave]=@{fila=$e.fila;uri=$uri;controles=@()}}
   $grupos[$llave].controles+=,$e.control
  }
  return ,$grupos
 }
 $limite=[DateTime]::UtcNow.AddSeconds(10);$filtrada=$false;$buscadorAbierto=$false;$expansion=$false;$codigo='sin_ventana';$entradas=@();$candidatos=@{};$fallo=$null;$etapa='inicio';$inspeccionCompleta=$false
 while([DateTime]::UtcNow -lt $limite -and -not $inspeccionCompleta) {
  $ids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $ventanas=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
  foreach($v in $ventanas) {
   if($v.Current.ProcessId -notin $ids) {continue}
   try {
   $codigo='biblioteca_no_accesible'
   $etapa='leer_ventana'
   $elementos=$v.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $biblioteca=$null
   foreach($e in $elementos) {
    if ((EsBiblioteca $e.Current.Name) -and $e.Current.ControlType.ProgrammaticName -match '(Pane|Group|List|Tree|Custom)$') {$biblioteca=$e;break}
   }
   # Algunas versiones exponen el título como botón/encabezado y el panel
   # carece de nombre. Subir solo hasta el contenedor local con lista/buscador.
   if(-not $biblioteca) {
    foreach($e in $elementos) {
     if(-not (EsBiblioteca $e.Current.Name)){continue}
     $ancestro=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($e)
     for($i=0;$i -lt 5 -and $ancestro;$i++) {
      if([Windows.Automation.Automation]::Compare($ancestro,$v) -or $ancestro.Current.ControlType.ProgrammaticName -match '(Window|Document)$'){break}
      $hijos=$ancestro.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
      $busqueda=@($hijos|Where-Object {EsBusqueda $_.Current.Name})
      $listas=@($hijos|Where-Object {$_.Current.ControlType.ProgrammaticName -match '(List|Tree|DataGrid)$'})
      if($busqueda.Count -gt 0 -or $listas.Count -gt 0){$biblioteca=$ancestro;break}
      $ancestro=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($ancestro)
     }
     if($biblioteca){break}
    }
   }
   if(-not $biblioteca -and -not $expansion -and -not $d.inspeccionar) {
    foreach($e in $elementos) {
     if((N $e.Current.Name) -match '^(?:ampliar|expandir|abrir|expand|open)\s+(?:tu biblioteca|your library)$' -and (Invocar $e)){$expansion=$true;break}
    }
   }
   if (-not $biblioteca) {continue}
   $etapa='leer_biblioteca'
   $items=$biblioteca.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $codigo='lista_no_localizada'
   if(-not $filtrada -and -not $d.inspeccionar) {
    $buscadores=@($items|Where-Object {EsBusqueda $_.Current.Name})
    foreach($e in $buscadores) {
      $p=$null
      if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p) -and -not $p.Current.IsReadOnly) {$p.SetValue($d.nombre);$filtrada=$true;break}
    }
    if($filtrada){continue}
    if(-not $buscadorAbierto) {
     foreach($e in $buscadores) {
      if($e.Current.ControlType -eq [Windows.Automation.ControlType]::Button -and (Invocar $e)){$buscadorAbierto=$true;break}
     }
    }
   }
   $entradas=@()
   $etapa='leer_candidatos'
   foreach($e in $items) {
    $coincide=NombreLista $e.Current.Name $d.nombre
    $uri=Enlace $e
    if($d.uri){
     $coincide=$uri -ceq $d.uri
    }
    if(-not $coincide){continue}
    $fila=Fila $e $biblioteca;$llave=($fila.GetRuntimeId() -join ',')
    if(-not (Accionable $e) -and -not (Accionable $fila)){continue}
    if(-not $uri) {
     $enlaces=New-Object 'System.Collections.Generic.Dictionary[string,bool]' ([StringComparer]::Ordinal)
     $hijos=$fila.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
     foreach($h in $hijos){$u=Enlace $h;if($u){$enlaces[$u]=$true}}
     if($enlaces.Count -eq 1){$uri=@($enlaces.Keys)[0]}
    }
    $entradas+=,@{llave=$llave;uri=$uri;fila=$fila;control=$e}
   }
   $etapa='agrupar'
   $candidatos=Agrupar $entradas
   if($d.inspeccionar){$inspeccionCompleta=$true;$codigo='inspeccion';break}
   if($candidatos.Count -gt 1){
    $identificadas=@($candidatos.Values|Where-Object {$_.uri})
    $codigo=if($identificadas.Count -gt 1){'listas_ambiguas'}else{'controles_ambiguos'}
    continue
   }
   if($candidatos.Count -eq 1) {
    $c=@($candidatos.Values)[0];$codigo='lista_no_invocable'
    $ordenados=@($c.controles|Sort-Object {if($_.Current.ControlType.ProgrammaticName -match '(Button|Hyperlink)$'){0}else{1}})
    foreach($e in $ordenados){if(Invocar $e){@{ok=$true}|ConvertTo-Json -Compress;exit 0}}
    if(Invocar $c.fila){@{ok=$true}|ConvertTo-Json -Compress;exit 0}
   }
   } catch {$codigo='error_accesibilidad';$fallo=@{etapa=$etapa;tipo=$_.Exception.GetType().FullName;mensaje=$_.Exception.Message;linea=$_.InvocationInfo.ScriptLineNumber};continue}
  }
  Start-Sleep -Milliseconds 250
 }
 $detalle=@($entradas|Select-Object -First 20|ForEach-Object {@{fila=$_.llave;tipo=$_.control.Current.ControlType.ProgrammaticName;tipoFila=$_.fila.Current.ControlType.ProgrammaticName;identificada=[bool]$_.uri}})
 @{ok=$false;codigo=$codigo;controles=@($entradas).Count;grupos=$candidatos.Count;detalle=$detalle;error=$fallo}|ConvertTo-Json -Compress -Depth 5
} catch {@{ok=$false;codigo='error_accesibilidad';error=@{etapa=$etapa;tipo=$_.Exception.GetType().FullName;mensaje=$_.Exception.Message;linea=$_.InvocationInfo.ScriptLineNumber}}|ConvertTo-Json -Compress -Depth 5}
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

# Selección estrictamente dentro de la página de playlist. Filtrar su tabla
# permite encontrar canciones virtualizadas sin usar la búsqueda global.
CANCION_PLAYLIST_UI=r'''
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $d=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function N([string]$s) {return [regex]::Replace($s.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD),'\p{Mn}','').Trim()}
 function TituloPagina([string]$s,[string]$esperado) {
  return $s -match '^(.+) - (?:playlist by|playlist de|lista de reproducci[oó]n de) .+ \| Spotify$' -and (N $Matches[1]) -eq (N $esperado)
 }
 function BotonCancion([string]$s,[string]$titulo,[bool]$pausa) {
  $verbo=if($pausa){'^(?:pausar|pause)\s+'}else{'^(?:reproducir|play)\s+'}
  return (N $s) -match ($verbo+[regex]::Escape((N $titulo))+'(?:$|,? (?:de|by) )')
 }
 $limite=[DateTime]::UtcNow.AddSeconds(12);$filtrada=$false;$busquedaAbierta=$false;$invocado=$false
 while([DateTime]::UtcNow -lt $limite) {
  $ids=@(Get-Process -Name Spotify -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $ventanas=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
  foreach($v in $ventanas) {
   if($v.Current.ProcessId -notin $ids){continue}
   $todos=$v.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $paginas=@($todos|Where-Object {$_.Current.ControlType -eq [Windows.Automation.ControlType]::Group -and (TituloPagina $_.Current.Name $d.nombre)})
   if($paginas.Count -ne 1){continue}
   $items=$paginas[0].FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   if(-not $filtrada -and -not $invocado) {
    $buscadores=@($items|Where-Object {(N $_.Current.Name) -match '(buscar en (esta |la )?(playlist|lista)|search in (this )?playlist)'})
    foreach($e in $buscadores) {
      $p=$null
      if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p) -and -not $p.Current.IsReadOnly){$p.SetValue($d.cancion);$filtrada=$true;break}
    }
    if($filtrada){continue}
    if(-not $busquedaAbierta) {
     foreach($e in $buscadores) {
      $p=$null
      if($e.Current.ControlType -eq [Windows.Automation.ControlType]::Button -and $e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke();$busquedaAbierta=$true;break}
     }
    }
   }
   # Solo filas directas de la tabla de esta playlist: las recomendaciones
   # y las celdas anidadas no son canciones adicionales de la lista.
   $tablas=@($items|Where-Object {$_.Current.ControlType -eq [Windows.Automation.ControlType]::DataGrid -and (N $_.Current.Name) -eq (N $d.nombre)})
   if($tablas.Count -ne 1){continue}
   $filas=@($tablas[0].FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)|Where-Object {$_.Current.ControlType.ProgrammaticName -match '(DataItem|ListItem)$'})
   # Spotify oculta el botón de la fila al comenzar a sonar. Corroborar la
   # fila pausada con el título exacto del reproductor y la playlist activa.
   $filaSonando=@($filas|Where-Object {(N $_.Current.Name) -match ('^(?:pausar|pause)\s+'+[regex]::Escape((N $d.cancion))+'(?:\s|$)')})
   $playlistSonando=@($todos|Where-Object {$_.Current.ControlType -eq [Windows.Automation.ControlType]::Button -and (N $_.Current.Name) -match ('^(?:pausar|pause)\s+'+[regex]::Escape((N $d.nombre))+'$')})
   $actualExacta=$false
   foreach($g in $todos) {
    if($g.Current.ControlType -eq [Windows.Automation.ControlType]::Group -and (N $g.Current.Name) -match '^(estas escuchando:|now playing:)') {
     foreach($h in $g.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)) {
      if($h.Current.ControlType -eq [Windows.Automation.ControlType]::Hyperlink -and (N $h.Current.Name) -eq (N $d.cancion)){$actualExacta=$true}
     }
    }
   }
   if($filaSonando.Count -eq 1 -and $playlistSonando.Count -eq 1 -and $actualExacta){@{ok=$true}|ConvertTo-Json -Compress;exit 0}
   $coincidentes=@()
   foreach($fila in $filas) {
    $celdas=$fila.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
    $titulo=@($celdas|Where-Object {($_.Current.ControlType -eq [Windows.Automation.ControlType]::Hyperlink -and (N $_.Current.Name) -eq (N $d.cancion)) -or ($_.Current.ControlType -eq [Windows.Automation.ControlType]::Button -and ((BotonCancion $_.Current.Name $d.cancion $false) -or (BotonCancion $_.Current.Name $d.cancion $true)))})
    if($titulo.Count -gt 0){$coincidentes+=,@{fila=$fila;celdas=$celdas}}
   }
   if($coincidentes.Count -gt 1){@{ok=$false}|ConvertTo-Json -Compress;exit 0}
   if($coincidentes.Count -ne 1){continue}
   $play=@();$pausa=@()
   foreach($b in $coincidentes[0].celdas) {
    if($b.Current.ControlType -ne [Windows.Automation.ControlType]::Button -or -not $b.Current.IsEnabled){continue}
    if(BotonCancion $b.Current.Name $d.cancion $false){$play+=,$b}
    if(BotonCancion $b.Current.Name $d.cancion $true){$pausa+=,$b}
   }
   if($pausa.Count -eq 1){@{ok=$true}|ConvertTo-Json -Compress;exit 0}
   if(-not $invocado -and $play.Count -eq 1){
    $p=$null
    if($play[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke();$invocado=$true}
   }
  }
  Start-Sleep -Milliseconds 250
 }
 @{ok=$false;paginas=$paginas.Count;tablas=$tablas.Count;filas=$filas.Count;coincidentes=$coincidentes.Count;play=$play.Count;pausa=$pausa.Count;invocado=$invocado}|ConvertTo-Json -Compress
} catch {@{ok=$false;error=$_.Exception.Message;linea=$_.InvocationInfo.ScriptLineNumber}|ConvertTo-Json -Compress}
'''

def reproducir_cancion_playlist(cancion,nombre,carpeta=None,correr=None):
    correr=correr or subprocess.run
    if not all(isinstance(v,str) and v.strip() and len(v)<=200 for v in (cancion,nombre)):
        return 'Necesito el título de la canción y el nombre de la playlist.'
    try:
        uri=cargar(carpeta).get(clave(nombre))
        biblioteca=resultado_ui(BIBLIOTECA_PS,{'nombre':nombre,'uri':uri_playlist(uri) if uri else ''},correr)
        if not biblioteca.get('ok'):
            return error_biblioteca(nombre,biblioteca)
        if ejecutar_ui(CANCION_PLAYLIST_UI,{'nombre':nombre,'cancion':cancion},correr):
            return 'Reproduciendo «'+cancion+'» dentro de tu playlist «'+nombre+'».'
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    return 'No pude confirmar «'+cancion+'» dentro de la playlist «'+nombre+'». Spotify debe exponer su tabla y los controles de la canción; no la busqué fuera de esa playlist.'

def resultado_ui(script,datos,correr):
    codigo=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    r=correr(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',codigo],
             input=json.dumps(datos),text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=18,creationflags=HIDDEN)
    valor=json.loads(r.stdout.strip())
    if r.returncode!=0 or not isinstance(valor,dict):return {'ok':False,'codigo':'error_accesibilidad'}
    if script in (BIBLIOTECA_PS,CANCION_PLAYLIST_UI) and correr is subprocess.run:
        # Estado de la última operación, con excepción local si falla.
        diagnostico={k:valor[k] for k in ('codigo','controles','grupos','detalle','error') if k in valor}
        diagnostico.update(ok=valor.get('ok') is True,etapa='biblioteca' if script==BIBLIOTECA_PS else 'cancion')
        try:(BASE/'diagnostico-playlist.json').write_text(json.dumps(diagnostico),encoding='utf8')
        except OSError:pass
    return {**valor,'ok':valor.get('ok') is True}

def ejecutar_ui(script,datos,correr):
    return resultado_ui(script,datos,correr)['ok']

def error_biblioteca(nombre,resultado):
    detalle={
        'sin_ventana':'Spotify todavía no ofrece una ventana accesible. Espera a que termine de abrirse y repite la orden.',
        'biblioteca_no_accesible':'No pude leer Tu biblioteca de Spotify. La biblioteca puede estar contraída o no estar expuesta a la accesibilidad de Windows; eso no significa que la playlist no exista.',
        'lista_no_localizada':'No pude localizar «'+nombre+'» entre los elementos que Spotify expuso en Tu biblioteca.',
        'listas_ambiguas':'Spotify expone varias playlists llamadas «'+nombre+'». Necesito distinguir cuál quieres.',
        'controles_ambiguos':'No pude identificar con seguridad la entrada de «'+nombre+'» en Tu biblioteca. Spotify expuso controles que no pude asociar a una única playlist.',
        'lista_no_invocable':'Encontré «'+nombre+'» en Tu biblioteca, pero Spotify no ofreció un control accesible para abrirla.'
    }.get(resultado.get('codigo'),'No pude consultar Tu biblioteca de Spotify mediante sus controles accesibles; no puedo confirmar si «'+nombre+'» está disponible.')
    return detalle+' No hice una búsqueda general.'

def reproducir_playlist(nombre,carpeta=None,abrir=None,correr=None):
    correr=correr or subprocess.run
    listas=cargar(carpeta);uri=listas.get(clave(nombre));abierta=False
    try:
        # Sin URI de apertura: no sacar al usuario de un juego a pantalla completa.
        biblioteca=resultado_ui(BIBLIOTECA_PS,{'nombre':nombre,'uri':uri_playlist(uri) if uri else ''},correr)
        abierta=biblioteca['ok']
        if not abierta:return error_biblioteca(nombre,biblioteca)
        if abierta and ejecutar_ui(PLAYLIST_UI,{'consulta':nombre,'accion':'playlist'},correr):
            return 'Activé la reproducción de la playlist «'+nombre+'» en Spotify.'
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
    if abierta:return 'Abrí la playlist «'+nombre+'», pero Spotify no confirmó la reproducción.'
    return error_biblioteca(nombre,{'codigo':'error_accesibilidad'})
