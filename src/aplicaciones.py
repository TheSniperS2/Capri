"""Aplicaciones instaladas y procesos identificados; nunca ejecuta texto del modelo."""
from pathlib import Path
import base64
import json
import os
import subprocess
from core import normalizar

HIDDEN=getattr(subprocess,'CREATE_NO_WINDOW',0)
ALIASES={'lol':'league of legends','league':'league of legends','riot':'cliente de riot','riot client':'cliente de riot'}

def clave(nombre):
    n=normalizar(nombre).strip()
    return ALIASES.get(n,n)

def powershell(script,datos=None):
    codigo=base64.b64encode(("$ErrorActionPreference='Stop';[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false);"+script).encode('utf-16le')).decode()
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',codigo],
                     input=json.dumps(datos or {}),capture_output=True,text=True,encoding='utf8',errors='replace',timeout=15,creationflags=HIDDEN)
    if r.returncode:raise OSError('Windows no pudo completar la operación con las aplicaciones.')
    return json.loads(r.stdout or '[]')

CATALOGO=r'''
$apps=@(Get-StartApps|ForEach-Object {@{nombre=$_.Name;tipo='app';destino=$_.AppID}})
$rutas=@([Environment]::GetFolderPath('StartMenu'),[Environment]::GetFolderPath('CommonStartMenu'),[Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('CommonDesktopDirectory'))
foreach($r in $rutas){if($r){Get-ChildItem -LiteralPath $r -Filter *.lnk -Recurse -ErrorAction SilentlyContinue|ForEach-Object {$apps+=@{nombre=$_.BaseName;tipo='enlace';destino=$_.FullName}}}}
ConvertTo-Json -InputObject @($apps) -Compress
'''

def catalogo():
    salida={}
    for a in powershell(CATALOGO):
        if not all(isinstance(a.get(k),str) and a[k] for k in ('nombre','tipo','destino')):continue
        k=clave(a['nombre'])
        if k not in salida or a['tipo']=='enlace':salida[k]=a
    return list(salida.values())

def abrir(nombre):
    apps=catalogo();n=clave(nombre)
    opciones=[a for a in apps if clave(a['nombre'])==n]
    if not opciones:opciones=[a for a in apps if n and n in clave(a['nombre'])]
    if len(opciones)!=1:return 'Necesito un nombre más preciso. Coincidencias: '+('; '.join(a['nombre'] for a in opciones[:8]) or 'ninguna')
    a=opciones[0]
    if a['tipo']=='enlace':os.startfile(a['destino'])
    elif Path(a['destino']).is_file():subprocess.Popen([a['destino']],shell=False,creationflags=HIDDEN)
    else:subprocess.Popen(['explorer.exe','shell:AppsFolder\\'+a['destino']],shell=False,creationflags=HIDDEN)
    return 'Solicité abrir '+a['nombre']+'.'

PROCESOS=r'''
$datos=[Console]::In.ReadToEnd()|ConvertFrom-Json
if($datos.cerrar){
 $seleccion=@();foreach($x in $datos.procesos){
  $p=Get-Process -Id $x.id -ErrorAction SilentlyContinue
  if(-not $p){continue}
  if($p.ProcessName -ne $x.nombre -or [string]$p.StartTime.ToUniversalTime().Ticks -ne $x.inicio){throw 'El proceso cambió; vuelve a solicitarlo.'}
  $seleccion+=,$p
 }
 foreach($p in $seleccion){Stop-Process -InputObject $p -ErrorAction Stop}
 foreach($p in $seleccion){if(-not $p.WaitForExit(3000)){throw 'El programa no confirmó el cierre.'}}
 @{ok=$true}|ConvertTo-Json -Compress
}else{
 $r=@();foreach($p in Get-Process){try{$r+=@{id=$p.Id;nombre=$p.ProcessName;inicio=[string]$p.StartTime.ToUniversalTime().Ticks}}catch{}}
 ConvertTo-Json -InputObject @($r) -Compress
}
'''

def procesos(nombre):
    n=clave(nombre)
    nombres={'spotify':('spotify',),'league of legends':('leagueclient','leagueclientux','leagueclientuxrender','league of legends'),
             'cliente de riot':('riotclientservices','riotclientux','riotclientuxrender')}.get(n,(n,))
    def compacta(s):return normalizar(s).replace(' ','').removesuffix('.exe')
    permitidos={compacta(s) for s in nombres}
    return [p for p in powershell(PROCESOS) if compacta(p['nombre']) in permitidos]

def cerrar(seleccion):
    if not seleccion:raise ValueError('No hay procesos seleccionados.')
    r=powershell(PROCESOS,{'cerrar':True,'procesos':seleccion})
    if not r.get('ok'):raise OSError('Windows no confirmó el cierre del programa.')
    return 'Cerré la aplicación confirmada.'
