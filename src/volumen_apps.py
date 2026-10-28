"""Deslizadores internos de Spotify y YouTube; nunca utiliza el mezclador."""
import re
import base64
import json
import subprocess
import threading
from core import normalizar,Orden,limpiar_peticion

def interpretar_volumen(texto,contexto=False):
    n=normalizar(limpiar_peticion(texto)).strip(' .!¡¿?')
    n=re.sub(r'^que\s+(?=le\s+sub|le\s+baj|sub|baj)','',n)
    spotify=bool(re.search(r'\bspotify\b',n));youtube=bool(re.search(r'\b(?:youtube|video)\b',n))
    if spotify and youtube:return None
    destino='spotify' if spotify else 'youtube' if youtube else ('spotify' if contexto is True else contexto)
    if destino not in ('spotify','youtube'):return None
    if not spotify and not youtube and re.search(r'\b(?:capri|windows|sistema|opera)\b',n):return None
    tipo=destino+'_volumen'
    if not re.match(r'^(?:(?:le\s+)?(?:sub(?:e(?:le)?|ir(?:le)?|a[sn]?|iera[sn]?)|aumenta(?:le|r)?|baj(?:a(?:le)?|ar(?:le)?|e[sn]?|ara[sn]?)|disminuye|reduce|pon(?:e|le|er)?|ajusta|fija|silencia|activa|quita|dime|que|cuanto)\b)',n):return None
    if not re.search(r'\b(?:volumen|audio|sonido|musica|silencia|silencio|silenciado)\b',n):return None
    if not re.search(r'\b(?:volumen|audio|sonido|silencia|silencio|silenciado)\b',n) and not re.match(r'^(?:le\s+)?(?:sub|baj|aumenta|disminuye|reduce)',n):return None
    if re.search(r'\b(?:quita|desactiva)\b.*\bsilencio\b',n):return Orden(tipo,'activar')
    if re.match(r'^silencia\b',n):return Orden(tipo,'silenciar')
    if re.match(r'^(?:dime|que|cuanto)\b',n):return Orden(tipo,'consultar')
    numeros={'cero':0,'cinco':5,'diez':10,'quince':15,'veinte':20,'treinta':30,'cuarenta':40,'cincuenta':50,
             'sesenta':60,'setenta':70,'ochenta':80,'noventa':90,'cien':100,'mitad':50,'maximo':100,'minimo':0}
    for palabra,numero in numeros.items():n=re.sub(r'\b'+palabra+r'\b',str(numero),n)
    valor=re.search(r'\b(\d{1,3})\b',n)
    cantidad=int(valor[1]) if valor else 10
    if cantidad>100:return None
    accion='subir' if re.match(r'^(?:le\s+)?(?:sub|aumenta)',n) else 'bajar'
    if re.match(r'^(?:pon|poner|ajusta|fija)',n) or (valor and re.search(r'\b(?:a|al|en)\s+(?:un\s+|el\s+)?'+valor[1]+r'\b',n)):accion='fijar'
    if accion=='fijar' and not valor:return None
    return Orden(tipo,accion+':'+str(cantidad))


VOLUMEN_UI=r'''
$ErrorActionPreference='Stop'
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
function DestinoVolumen([string]$operacion,[double]$actual,[double]$restaurar){
 if($operacion -eq 'silenciar'){return 0}
 if($operacion -eq 'activar'){if($actual -gt 0){return $actual};return $restaurar}
 if($operacion -eq 'consultar'){return $actual}
 $p=$operacion -split ':';$numero=[double]$p[1]
 switch($p[0]){
  'fijar' {return $numero}
  'subir' {return [Math]::Min(100,$actual+$numero)}
  'bajar' {return [Math]::Max(0,$actual-$numero)}
 }
 throw 'Operación de volumen no válida.'
}
function EsYouTube([string]$url,[string]$documento,[string]$ventana){
 if($url -match '^https?://'){return $url -match '^https://(www\.|m\.)?youtube\.(com|cl)/'}
 return $url -match '^https://(www\.|m\.)?youtube\.(com|cl)/' -or $documento -match ' - YouTube$' -or ($ventana -match '(?i)YouTube' -and $documento -and $ventana.Contains($documento))
}
$nombreApp='reproductor'
try{
 Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
 $d=[Console]::In.ReadToEnd()|ConvertFrom-Json
 $nombreApp=if($d.destino -eq 'youtube'){'YouTube'}else{'Spotify'}
 $proceso=if($d.destino -eq 'youtube'){'opera'}else{'Spotify'}
 $ids=@(Get-Process -Name $proceso -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
 $raices=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Slider)
 $controles=@()
 foreach($r in $raices){
  if($r.Current.ProcessId -notin $ids){continue}
  $zonas=@($r)
  if($d.destino -eq 'youtube'){
   $zonas=@()
   $docCond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Document)
   foreach($doc in $r.FindAll([Windows.Automation.TreeScope]::Descendants,$docCond)){
    $vp=$null;$url=''
    if($doc.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){$url=$vp.Current.Value}
    elseif($doc.TryGetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern,[ref]$vp)){$url=$vp.Current.Value}
    if(EsYouTube $url $doc.Current.Name $r.Current.Name){$zonas+=,$doc}
   }
  }
  foreach($zona in $zonas){
   foreach($e in $zona.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)){
   # No confundir la posición de la canción con el volumen.
   if($e.Current.Name -match '(?i)(volumen|volume)' -or $e.Current.AutomationId -match '(?i)volume'){
    $patron=$null
    if($e.TryGetCurrentPattern([Windows.Automation.RangeValuePattern]::Pattern,[ref]$patron)){
     $controles+=,@{elemento=$e;patron=$patron;zona=$zona}
    }
   }
  }
  }
 }
 if($controles.Count -ne 1){@{ok=$false;error=('No pude identificar un único deslizador de volumen dentro de '+$nombreApp+'. Su interfaz debe estar disponible; no cambié el mezclador de Windows.')}|ConvertTo-Json -Compress;exit 0}
 $p=$controles[0].patron;$min=$p.Current.Minimum;$max=$p.Current.Maximum
 if($max -le $min){throw 'El reproductor comunicó un rango de volumen inválido.'}
 $actual=100*($p.Current.Value-$min)/($max-$min)
 $destino=DestinoVolumen $d.operacion $actual ([double]$d.restaurar)
 if($d.destino -eq 'youtube' -and $d.operacion -match '^(subir|bajar|fijar):'){
  $botones=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
  foreach($b in $controles[0].zona.FindAll([Windows.Automation.TreeScope]::Descendants,$botones)){
   if($b.Current.Name -match '^(?i)(Unmute|Activar (el )?(sonido|audio)|Quitar (el )?silencio|Desactivar (el )?silencio)\b'){
    @{ok=$false;error='YouTube está silenciado. Para cambiar su nivel sin quitar el silencio, usa la conexión directa de Capri con Opera.'}|ConvertTo-Json -Compress;exit 0
   }
  }
 }
 if($d.operacion -ne 'consultar' -and [Math]::Abs($destino-$actual) -gt 0.1){
  if($p.Current.IsReadOnly){throw 'El deslizador de volumen es de solo lectura.'}
  $p.SetValue($min+($destino/100)*($max-$min))
 }
 $resultado=$actual
 for($i=0;$i -lt 12;$i++){
  $resultado=100*($p.Current.Value-$min)/($max-$min)
  if([Math]::Abs($resultado-$destino) -le 1){break}
  Start-Sleep -Milliseconds 50
 }
 @{ok=([Math]::Abs($resultado-$destino) -le 1);volumen=$resultado;anterior=$actual}|ConvertTo-Json -Compress
}catch{@{ok=$false;error=('No pude ajustar el deslizador interno de '+$nombreApp+'. No cambié el mezclador de Windows.')}|ConvertTo-Json -Compress}
'''

_ultimo_volumen=50
_ultimo_youtube=50
_lock=threading.Lock()

def controlar_volumen(operacion,correr=None,destino='spotify'):
    if destino not in ('spotify','youtube'):raise ValueError('Reproductor no válido.')
    m=re.fullmatch(r'(subir|bajar|fijar):(\d{1,3})',operacion)
    if (not m and operacion not in ('silenciar','activar','consultar')) or (m and int(m[2])>100):
        raise ValueError('El volumen debe estar entre 0 y 100.')
    global _ultimo_volumen,_ultimo_youtube
    nombre='YouTube' if destino=='youtube' else 'Spotify'
    with _lock:
        restaurar=_ultimo_youtube if destino=='youtube' else _ultimo_volumen
        codigo=base64.b64encode(VOLUMEN_UI.encode('utf-16le')).decode()
        try:
            datos=None;salida=0
            if destino=='youtube' and correr is None:
                from puente_opera import ejecutar,mensaje_error
                datos=ejecutar('volumen',{'operacion':operacion,'restaurar':restaurar})
                if datos is not None and datos.get('ok') and m and float(datos.get('volumen',0))>0 and datos.get('silenciado') is True:
                    # Compatibilidad con la extensión 1.0.1 ya cargada: activar
                    # sonido sin repetir el incremento de volumen que ya aplicó.
                    datos=ejecutar('volumen',{'operacion':'activar','restaurar':float(datos['volumen'])})
                    if datos is None:return 'YouTube cambió el nivel, pero se perdió la conexión antes de activar el sonido.'
                if datos is not None and not datos.get('ok'):return mensaje_error(datos)
            if datos is None:
                r=(correr or subprocess.run)(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',codigo],
                         input=json.dumps({'operacion':operacion,'restaurar':restaurar,'destino':destino}),text=True,encoding='utf8',errors='replace',
                         capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                datos=json.loads(r.stdout);salida=r.returncode
            if salida==0 and isinstance(datos,dict) and datos.get('ok'):
                nivel=float(datos['volumen']);anterior=float(datos['anterior'])
                if not 0<=nivel<=100 or not 0<=anterior<=100:raise ValueError('Nivel no válido.')
                if destino=='youtube' and m and nivel>0 and datos.get('silenciado') is True:
                    return 'YouTube cambió el nivel, pero no confirmó que el sonido estuviera activado.'
                previo=nivel if nivel>0 else anterior if anterior>0 else restaurar
                if destino=='youtube':_ultimo_youtube=previo
                else:_ultimo_volumen=previo
                if datos.get('silenciado') is True and operacion=='silenciar':return 'Silencié YouTube.'
                return 'Volumen dentro de '+nombre+': '+str(round(nivel))+'%.'+(' Sigue silenciado.' if datos.get('silenciado') is True else '')
            if destino=='youtube':return 'Para controlar el vídeo directamente, conecta la extensión local: clic derecho sobre Capri → Conectar YouTube con Opera. El control accesible de Opera no está disponible.'
            if isinstance(datos,dict) and datos.get('error'):return datos['error']
        except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired):pass
    return nombre+' no confirmó el cambio de su volumen interno. No cambié el mezclador de Windows.'
