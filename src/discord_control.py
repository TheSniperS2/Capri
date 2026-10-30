"""Controles propios de Discord de escritorio mediante accesibilidad de Windows."""
import base64
import json
import re
import subprocess


def interpretar_discord(texto,contexto=False):
    from core import Orden,normalizar,limpiar_peticion
    n=normalizar(limpiar_peticion(texto)).strip(' .!?¿¡')
    n=re.sub(r'\s+',' ',n)
    explicito=bool(re.search(r'\bdiscord$',n))
    if re.fullmatch(r'(?:abre(?:me)?|abrir(?:me)?|inicia(?:r)?)\s+discord',n):return Orden('discord_abrir')
    if not explicito and not contexto:return None
    n=re.sub(r'\s+(?:(?:(?:en|de|del|al|in|on|no)\s+)?(?:el\s+)?discord)$','',n)
    ordenes={
        'discord_mutear':('silenciame','muteame','silenciarme','mutearme','mutear','silenciar','silencia mi microfono','mutea mi microfono','mute me'),
        'discord_desmutear':('desmuteame','desmutearme','desmutear','desilenciame','activa mi microfono','quita mi silencio','unmute me'),
        'discord_ensordecer':('ensordeceme','ensordecerme','ensordecer','silencia mi audio','deafen me'),
        'discord_desensordecer':('desensordeceme','desensordecerme','desensordecer','activa mi audio','quita el ensordecimiento','undeafen me'),
    }
    for accion,frases in ordenes.items():
        if n in frases:return Orden(accion)
    m=re.fullmatch(r'(?:uneme|unete|unirme|entra|entrar|conectame)\s+(?:al|a(?: un)?)\s+(?:canal(?: de voz)?\s+)?(.+?)(?:\s+(?:del|en el)\s+servidor\s+(.+?))?',n)
    if m and 0<len(m[1])<=120 and (not m[2] or len(m[2])<=120):
        return Orden('discord_unir',json.dumps({'canal':m[1].strip(' «»"'),'servidor':(m[2] or '').strip(' «»"')},ensure_ascii=False))
    return None


DISCORD_UI=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $d=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function N($v){
  $s=$v.Normalize([Text.NormalizationForm]::FormD)
  return ([regex]::Replace($s,'\p{Mn}','')).ToLowerInvariant().Trim()
 }
 function Invocar($e,$conmutar=$false){
  $p=$null
  if(!$e.Current.IsEnabled){return $false}
  if($e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke();return $true}
  if($conmutar -and $e.TryGetCurrentPattern([Windows.Automation.TogglePattern]::Pattern,[ref]$p)){$p.Toggle();return $true}
  if($e.TryGetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$p)){$p.DoDefaultAction();return $true}
  return $false
 }
 function Raiz {
  $ids=@(Get-Process -Name Discord,DiscordCanary,DiscordPTB -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $rs=@([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)|Where-Object {$_.Current.ProcessId -in $ids})
  if($rs.Count -ne 1){return $null};return $rs[0]
 }
 $r=Raiz
 if(!$r){@{ok=$false;codigo='ventana'}|ConvertTo-Json -Compress;exit 0}
 function Items {return $r.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)}
 if($d.accion -eq 'unir'){
  if($d.servidor){
   $servidores=@((Items)|Where-Object {$_.Current.ControlType -in @([Windows.Automation.ControlType]::TreeItem,[Windows.Automation.ControlType]::Button) -and (N $_.Current.Name) -eq (N $d.servidor)})
   if($servidores.Count -ne 1 -or !(Invocar $servidores[0])){@{ok=$false;codigo='servidor'}|ConvertTo-Json -Compress;exit 0}
   Start-Sleep -Milliseconds 500
  }
  $nombre='^'+[regex]::Escape((N $d.canal))+'(?:\s*[,(:-].*|\s+(?:canal de voz|voice channel|canal de voz).*)?$'
  $canales=@((Items)|Where-Object {$_.Current.ControlType -in @([Windows.Automation.ControlType]::TreeItem,[Windows.Automation.ControlType]::Hyperlink,[Windows.Automation.ControlType]::Button) -and (N $_.Current.Name) -match $nombre -and (N ($_.Current.Name+' '+$_.Current.HelpText)) -match 'canal de voz|voice channel|ボイス|音声'})
  if($canales.Count -ne 1 -or !(Invocar $canales[0])){@{ok=$false;codigo='canal'}|ConvertTo-Json -Compress;exit 0}
  Start-Sleep -Milliseconds 250
  $entrar=@((Items)|Where-Object {$_.Current.ControlType -eq [Windows.Automation.ControlType]::Button -and (N $_.Current.Name) -match '^(unirse a voz|unirse al canal|join voice|entrar no canal)(\s|$)'})
  if($entrar.Count -eq 1){[void](Invocar $entrar[0])}
  @{ok=$true;solicitado=$true}|ConvertTo-Json -Compress;exit 0
 }
 $micro=$d.accion -in @('mutear','desmutear')
 $activar=$d.accion -in @('mutear','ensordecer')
 $sinMute=if($micro){'^(silenciar|mute|desativar microfone)(\s*\(|$)'}else{'^(ensordecer|deafen|ensurdecer)(\s*\(|$)'}
 $conMute=if($micro){'^(activar microfono|desactivar silencio|unmute|ativar microfone)(\s*\(|$)'}else{'^(desensordecer|activar sonido|undeafen|desensurdecer)(\s*\(|$)'}
 function Estado {
  $bs=@((Items)|Where-Object {$_.Current.ControlType -eq [Windows.Automation.ControlType]::Button})
  $on=@($bs|Where-Object {(N $_.Current.Name) -match $conMute})
  $off=@($bs|Where-Object {(N $_.Current.Name) -match $sinMute})
  $candidatos=@($on)+@($off)
  if($candidatos.Count -eq 1){
   $tp=$null
   if($candidatos[0].TryGetCurrentPattern([Windows.Automation.TogglePattern]::Pattern,[ref]$tp)){
    $estado=$tp.Current.ToggleState
    if($estado -eq [Windows.Automation.ToggleState]::Indeterminate){return $null}
    return @{muted=($estado -eq [Windows.Automation.ToggleState]::On);boton=$candidatos[0]}
   }
  }
  if($on.Count -eq 1 -and !$off.Count){return @{muted=$true;boton=$on[0]}}
  if($off.Count -eq 1 -and !$on.Count){return @{muted=$false;boton=$off[0]}}
  return $null
 }
 $e=Estado
 # Chromium puede tardar en publicar el árbol al primer cliente UIA.
 for($i=0;!$e -and $i -lt 8;$i++){Start-Sleep -Milliseconds 150;$e=Estado}
 if(!$e){@{ok=$false;codigo='control'}|ConvertTo-Json -Compress;exit 0}
 if($e.muted -eq $activar){@{ok=$true;confirmado=$true}|ConvertTo-Json -Compress;exit 0}
 if(!(Invocar $e.boton $true)){@{ok=$false;codigo='control'}|ConvertTo-Json -Compress;exit 0}
 for($i=0;$i -lt 15;$i++){
  Start-Sleep -Milliseconds 100;$e=Estado
  if($e -and $e.muted -eq $activar){@{ok=$true;confirmado=$true}|ConvertTo-Json -Compress;exit 0}
 }
 @{ok=$false;codigo='sin_confirmar'}|ConvertTo-Json -Compress
}catch{@{ok=$false;codigo='control'}|ConvertTo-Json -Compress}
'''


def ejecutar_discord(orden,correr=None):
    if orden.tipo=='discord_abrir':
        from aplicaciones import abrir
        return abrir('Discord')
    accion=orden.tipo.removeprefix('discord_')
    if accion not in ('mutear','desmutear','ensordecer','desensordecer','unir'):raise ValueError('Control Discord no disponible.')
    datos={'accion':accion}
    if accion=='unir':
        canal=json.loads(orden.valor)
        if set(canal)!={'canal','servidor'} or not all(isinstance(v,str) and len(v)<=120 for v in canal.values()) or not canal['canal']:raise ValueError('Indica un canal de voz.')
        datos.update(canal)
    try:
        r=(correr or subprocess.run)(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(DISCORD_UI.encode('utf-16le')).decode()],
            input=json.dumps(datos),text=True,encoding='utf8',errors='replace',capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        resultado=json.loads(r.stdout) if r.returncode==0 else {}
    except (OSError,ValueError,subprocess.TimeoutExpired):resultado={}
    if not isinstance(resultado,dict):resultado={}
    if resultado.get('ok') and (resultado.get('solicitado') if accion=='unir' else resultado.get('confirmado')):
        if accion=='unir':return 'Solicité entrar al canal de voz «'+datos['canal']+'» en Discord.'
        return {'mutear':'Tu micrófono está silenciado en Discord.','desmutear':'Tu micrófono está activado en Discord.',
                'ensordecer':'Tu audio está ensordecido en Discord.','desensordecer':'Tu audio está activado en Discord.'}[accion]
    return {'ventana':'Abre la ventana de Discord para que pueda acceder a sus controles.',
            'servidor':'Selecciona el servidor en Discord y vuelve a pedir el canal de voz.',
            'canal':'No identifiqué un único canal de voz con ese nombre en Discord. Abre el servidor y precisa el canal.',
            'sin_confirmar':'Discord recibió el clic, pero no pude confirmar el cambio. No lo repetí.'}.get(resultado.get('codigo'),
            'Discord no expuso un control inequívoco. No envié atajos a otras aplicaciones.')
