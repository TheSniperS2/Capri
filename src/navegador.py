"""Destinos web explícitos y controles accesibles de YouTube en Opera."""
import base64
import json
import re
import subprocess
from urllib.parse import urlencode

def interpretar_web(texto):
    from core import Orden,normalizar,url_solicitada,ABRIR,BUSCAR,APPS
    n=normalizar(texto).strip(' .!')
    # Nombre exacto de un sitio significa navegar; Google explícito conserva búsqueda.
    sitio_buscado=re.fullmatch(BUSCAR+r'\s+(?:la\s+p[aá]gina\s+(?:de\s+)?)?(.+?)[.!]?',texto,re.I)
    if sitio_buscado:
        sitio=url_solicitada(sitio_buscado[1])
        if sitio:return Orden('pestana',sitio)
    paso=re.fullmatch(r'(?:(?:pon|pasa|cambia|salta|ve)\s+(?:a\s+)?)?(?:el\s+|al\s+)?(siguiente|anterior)(?:\s+video)(?:\s+(?:en|de)\s+youtube)?',n)
    if paso:return Orden('youtube_'+paso[1])
    control=re.fullmatch(r'(pausa(?:r)?|deten(?:er)?|para(?:r)?|reanuda(?:r)?|continua(?:r)?|reproduce|reproducir)\s+(?:(?:el|un|este|ese)\s+)?(?:video|youtube)(?:\s+(?:en|de)\s+youtube)?',n)
    if control:return Orden('youtube_'+('pausa' if control[1].startswith(('paus','deten','para')) else 'reanudar'))
    consulta=re.fullmatch(r'('+BUSCAR+r'|pon|ponme|reproduce|abre)\s+(?:un\s+|el\s+)?(?:video\s+(?:de\s+)?)?(.+?)\s+en\s+youtube[.!]?',texto,re.I)
    if consulta:
        if re.search(r'\bpesta[nñ]a\b',consulta[2],re.I):return None
        return Orden('youtube_buscar' if re.fullmatch(BUSCAR,consulta[1],re.I) else 'youtube_video',consulta[2].strip())
    consulta=re.fullmatch(BUSCAR+r'\s+en\s+youtube\s+(.+?)[.!]?',texto,re.I)
    if consulta:return Orden('youtube_buscar',consulta[1])
    consulta=re.fullmatch(r'(?:pon|reproduce|abre)\s+(?:un\s+|el\s+)video\s+(?:de\s+)?(.+?)[.!]?',texto,re.I)
    if consulta:return Orden('youtube_video',consulta[1])
    entrada=re.fullmatch(r'(?:'+ABRIR+r'|entra(?:r)?(?:te)?(?:\s+a)?|(?:m[eé]tete|meterte|(?:te\s+)?metas)(?:\s+a)?|ve(?:\s+a)?|navega(?:\s+a)?)\s+(?:la\s+p[aá]gina\s+(?:de\s+)?|a\s+)?(.+?)(?:\s+en\s+(?:el\s+)?opera(?:\s+gx)?)?[.!]?',texto,re.I)
    if entrada:
        if re.match(r'^'+ABRIR+r'\b',texto,re.I) and normalizar(entrada[1]) in APPS:return None
        sitio=url_solicitada(entrada[1])
        # Conservar alias históricos de apertura; también van a Opera.
        if sitio and not (n in ('abre youtube','abrir youtube','abreme youtube')):return Orden('pestana',sitio)
    return None

# Solo documentos YouTube de procesos Opera. No teclas globales ni SetFocus.
YOUTUBE_UI=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $d=[Console]::In.ReadToEnd()|ConvertFrom-Json
 function Valor($e){
  $p=$null
  if($e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p)){return $p.Current.Value}
  if($e.TryGetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$p)){return $p.Current.Value}
  return ''
 }
 function Invocar($e){
  $p=$null
  if($e.Current.IsEnabled -and $e.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke();return $true}
  if($e.Current.IsEnabled -and $e.Current.ControlType -in @([Windows.Automation.ControlType]::Hyperlink,[Windows.Automation.ControlType]::Button) -and $e.TryGetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$p)){$p.DoDefaultAction();return $true}
  return $false
 }
 $limite=[DateTime]::UtcNow.AddSeconds(9)
 while([DateTime]::UtcNow -lt $limite){
  $ids=@(Get-Process -Name opera -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $raices=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
  $docs=@()
  foreach($r in $raices){
   if($r.Current.ProcessId -notin $ids){continue}
   $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Document)
   foreach($doc in $r.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)){
    $url=Valor $doc
    if($url -match '^https://(www\.)?youtube\.(com|cl)/' -or $doc.Current.Name -match ' - YouTube$' -or ($r.Current.Name -match '(?i)YouTube' -and $doc.Current.Name -and $r.Current.Name.Contains($doc.Current.Name))){$docs+=,$doc}
   }
  }
  if($docs.Count -gt 1){throw 'Hay varias páginas YouTube visibles; selecciona una sola.'}
  if($docs.Count -eq 1){
   $items=$docs[0].FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   foreach($e in $items){
    $n=$e.Current.Name;$elegido=$false
    if($d.accion -eq 'video' -and $e.Current.ControlType -eq [Windows.Automation.ControlType]::Hyperlink){
     $url=Valor $e
     $elegido=$url -match '^https://(www\.)?youtube\.com/watch\?v=[\w-]+'
    }
    if($e.Current.ControlType -eq [Windows.Automation.ControlType]::Button){
     switch($d.accion){
      'siguiente' {$elegido=$n -match '^(Siguiente|Next)(\s*\(|$)'}
      'anterior' {$elegido=$n -match '^(Anterior|Previous)(\s*\(|$)'}
      'pausa' {$elegido=$n -match '^(Pausa|Pausar|Pause)(\s*\(|$)'}
      'reanudar' {$elegido=$n -match '^(Reproducir|Play)(\s*\(|$)'}
     }
    }
    if($elegido -and (Invocar $e)){@{ok=$true}|ConvertTo-Json -Compress;exit 0}
   }
  }
  Start-Sleep -Milliseconds 300
 }
 @{ok=$false;error='YouTube no expuso ese control. Deja la pestaña de YouTube seleccionada en Opera GX.'}|ConvertTo-Json -Compress
}catch{@{ok=$false;error=$_.Exception.Message}|ConvertTo-Json -Compress}
'''

def ejecutar_youtube(orden,spawn=None,correr=None):
    from core import abrir_opera
    accion=orden.tipo.removeprefix('youtube_')
    if accion in ('buscar','video'):
        if not orden.valor.strip():raise ValueError('Falta el nombre del vídeo.')
        pagina='https://www.youtube.com/results?'+urlencode({'search_query':orden.valor})
        kwargs={'pagina':pagina}
        if spawn is not None:kwargs['spawn']=spawn
        abrir_opera(**kwargs)
        if accion=='buscar':return 'Busqué «'+orden.valor+'» dentro de YouTube en Opera GX.'
    if accion not in ('video','siguiente','anterior','pausa','reanudar'):raise ValueError('Control YouTube desconocido.')
    if correr is None and accion!='video':
        from puente_opera import ejecutar,mensaje_error
        directo=ejecutar(accion)
        if directo is not None:
            if not directo.get('ok'):return mensaje_error(directo)
            return {'pausa':'Pausé el vídeo de YouTube.','reanudar':'Reanudé el vídeo de YouTube.',
                    'siguiente':'Solicité el siguiente vídeo de YouTube.','anterior':'Solicité el vídeo anterior de YouTube.',
                    'video':'Solicité reproducir el primer vídeo de los resultados de YouTube.'}[accion]
    fallo_sesion=''
    if accion!='video':
        from multimedia import sesion_youtube
        estado=sesion_youtube(accion,correr=correr)
        if estado.get('ok'):
            if accion=='pausa':return 'Pausé el vídeo de YouTube.' if estado.get('estado')=='Paused' else 'YouTube recibió la pausa; el estado todavía no está confirmado.'
            if accion=='reanudar':return 'Reanudé el vídeo de YouTube.' if estado.get('estado')=='Playing' else 'YouTube recibió la orden de continuar; el estado todavía no está confirmado.'
            return 'Solicité el vídeo '+accion+' de YouTube mediante su sesión multimedia.'
        fallo_sesion=estado.get('error','')
    codigo=base64.b64encode(YOUTUBE_UI.encode('utf-16le')).decode()
    r=(correr or subprocess.run)(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',codigo],
             input=json.dumps({'accion':accion}),text=True,encoding='utf8',errors='replace',capture_output=True,timeout=14,
             creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:datos=json.loads(r.stdout)
    except ValueError:datos={}
    if r.returncode==0 and datos.get('ok'):
        return {'video':'Solicité reproducir el primer vídeo de los resultados de YouTube.',
                'siguiente':'Solicité el siguiente vídeo de YouTube.','anterior':'Solicité el vídeo anterior de YouTube.',
                'pausa':'Solicité pausar YouTube.','reanudar':'Solicité continuar el vídeo de YouTube.'}[accion]
    return ('No pude controlar YouTube. '+fallo_sesion+' También falló el control accesible de la página.') if fallo_sesion else (datos.get('error') or 'YouTube no confirmó el control. No envié teclas a otras aplicaciones.')
