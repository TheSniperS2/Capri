import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'src'))
import core
import playlists
from intenciones import Interprete


class PlaylistContexto(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='win32','Tipos de accesibilidad Windows')
    def test_todos_los_tipos_uia_referenciados_existen_en_windows(self):
        script=r'''
Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
$t=$null;$e=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput([Console]::In.ReadToEnd(),[ref]$t,[ref]$e)
if($e.Count){throw 'Sintaxis PowerShell inválida'}
$tipos=$ast.FindAll({param($n) $n -is [System.Management.Automation.Language.TypeExpressionAst]},$true)
$faltantes=@($tipos|Where-Object {$_.TypeName.FullName -like 'Windows.Automation.*' -and -not $_.TypeName.GetReflectionType()}|ForEach-Object {$_.TypeName.FullName})
ConvertTo-Json -InputObject $faltantes -Compress
'''
        for codigo in (playlists.BIBLIOTECA_PS,playlists.CANCION_PLAYLIST_UI):
            r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16-le')).decode()],input=codigo,text=True,capture_output=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(r.stdout),[])

    def test_peticion_real_conserva_cancion_y_playlist_y_no_busca_global(self):
        for texto in ['Capri reproduce la canción High Forever de mis playlist "Capri"',
                      'pon High Forever en mi playlist Capri',
                      'reproduce High Forever de la lista de reproducción Capri en Spotify']:
            orden=core.interpretar(texto)
            self.assertEqual(orden.tipo,'spotify_playlist_cancion')
            self.assertEqual(json.loads(orden.valor),{'cancion':'High Forever','nombre':'Capri'})
            with patch.object(playlists,'reproducir_cancion_playlist',return_value='ok') as ejecutar:
                self.assertEqual(core.ejecutar(orden),'ok')
                ejecutar.assert_called_once_with(cancion='High Forever',nombre='Capri')
        self.assertIsNone(playlists.interpretar_cancion_playlist('no reproduzcas High Forever en mi playlist Capri'))
        self.assertEqual(core.interpretar('reproduce High Forever'),core.Orden('spotify','High Forever'))

    def test_error_del_modelo_no_pierde_restriccion_de_playlist(self):
        i=Interprete()
        d=i.validar({'accion':'spotify','valor':'High Forever'},'reproduce High Forever de mi playlist Capri',i.contexto())
        self.assertEqual(d.orden.tipo,'spotify_playlist_cancion')
        datos={'accion':'spotify_playlist_cancion','valor':json.dumps({'cancion':'High Forever','nombre':'Capri'})}
        d=i.validar(datos,'Me gustaría escuchar High Forever, pero desde mi playlist Capri',i.contexto())
        self.assertEqual(d.orden.tipo,'spotify_playlist_cancion')
        datos['valor']=json.dumps({'cancion':'Otra canción','nombre':'Capri'})
        self.assertIsNone(i.validar(datos,'Me gustaría escuchar High Forever, pero desde mi playlist Capri',i.contexto()).orden)

    def test_biblioteca_y_fila_usan_datos_separados_sin_abrir_spotify_uri(self):
        with tempfile.TemporaryDirectory() as carpeta:
            correr=Mock(return_value=types.SimpleNamespace(stdout='{"ok":true}',returncode=0))
            mensaje=playlists.reproducir_cancion_playlist('High Forever','Capri',Path(carpeta),correr)
            self.assertIn('dentro de tu playlist',mensaje)
            self.assertEqual(correr.call_count,2)
            datos=[json.loads(c.kwargs['input']) for c in correr.call_args_list]
            self.assertEqual(datos,[{'nombre':'Capri','uri':''},{'nombre':'Capri','cancion':'High Forever'}])
            correr.reset_mock();correr.return_value.stdout='{"ok":false}'
            self.assertIn('No pude consultar',playlists.reproducir_cancion_playlist('High Forever','Capri',Path(carpeta),correr))
            self.assertEqual(correr.call_count,1)

    def test_biblioteca_inaccesible_y_lista_ambigua_no_significan_inexistencia(self):
        with tempfile.TemporaryDirectory() as carpeta:
            for codigo,esperado in [('biblioteca_no_accesible','No pude leer Tu biblioteca'),
                                    ('listas_ambiguas','varias playlists'),
                                    ('controles_ambiguos','No pude identificar con seguridad'),
                                    ('lista_no_invocable','Encontré «Cyberpunk»'),
                                    ('sin_ventana','termine de abrirse')]:
                correr=Mock(return_value=types.SimpleNamespace(stdout=json.dumps({'ok':False,'codigo':codigo}),returncode=0))
                respuesta=playlists.reproducir_cancion_playlist('High Forever','Cyberpunk',Path(carpeta),correr)
                self.assertIn(esperado,respuesta)
                self.assertNotIn('No encontré',respuesta)
                self.assertEqual(correr.call_count,1)

    @unittest.skipUnless(sys.platform=='win32','Agrupador PowerShell')
    def test_controles_de_misma_uri_se_unifican_y_playlists_distintas_se_conservan(self):
        funcion='function Agrupar'+playlists.BIBLIOTECA_PS.split(' function Agrupar',1)[1].split(' $limite=',1)[0]
        script=funcion+'''
$d=[Console]::In.ReadToEnd()|ConvertFrom-Json
@($d|ForEach-Object {$g=Agrupar $_;@{cantidad=$g.Count;controles=@($g.Values|ForEach-Object {$_.controles.Count})}})|ConvertTo-Json -Compress -Depth 5
'''
        def entrada(fila,uri=''):
            return {'llave':fila,'uri':uri,'fila':fila,'control':'control-'+fila}
        uri='spotify:playlist:'+'A'*22
        casos=[
            [entrada('fila-1',uri),entrada('otra-representacion',uri)],
            [entrada('fila-1',uri),entrada('fila-2','spotify:playlist:'+'a'*22)],
            [entrada('fila-1'),entrada('fila-1'),entrada('fila-1')],
            [entrada('fila-1',uri),entrada('fila-1')],
            [entrada('fila-1',uri),entrada('fila-desconocida')]]
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16-le')).decode()],input=json.dumps(casos),text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        resultados=json.loads(r.stdout)
        self.assertEqual([x['cantidad'] for x in resultados],[1,2,1,1,2])
        self.assertEqual(resultados[0]['controles'],[2])
        self.assertEqual(resultados[2]['controles'],[3])

    @unittest.skipUnless(sys.platform=='win32','Selectores Windows')
    def test_nombres_accesibles_de_playlist_y_biblioteca(self):
        funciones=playlists.BIBLIOTECA_PS.split(' function N',1)[1].split(' function Invocar',1)[0]
        script='function N'+funciones+'''
$d=[Console]::In.ReadToEnd()|ConvertFrom-Json
@($d|ForEach-Object {NombreLista $_ 'cyberpunk'})|ConvertTo-Json -Compress
'''
        nombres=['cyberpunk','Cyberpunk Playlist de Franco','CYBERPUNK\nPlaylist • Franco',
                 'Cyberpunk • Playlist • Franco','Cyberpunk, Lista de reproducción de Franco',
                 'Cyberpunk remixes Playlist de Franco','Otra Cyberpunk','Cyberpunkplaylist',
                 'Cyberpunk 2077 Playlist de Franco']
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16-le')).decode()],input=json.dumps(nombres),text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),[True,True,True,True,True,False,False,False,False])

    @unittest.skipUnless(sys.platform=='win32','UIA Windows')
    def test_selectores_rechazan_otra_playlist_y_botones_globales(self):
        funciones=playlists.CANCION_PLAYLIST_UI.split(' function N',1)[1].split(' $limite=',1)[0]
        script='function N'+funciones+'''
@((TituloPagina 'Capri - playlist de Franco | Spotify' 'Capri'),
  (TituloPagina 'Otra - playlist de Franco | Spotify' 'Capri'),
  (BotonCancion 'Reproducir High Forever de Artista' 'High Forever' $false),
  (BotonCancion 'Reproducir' 'High Forever' $false),
  (BotonCancion 'Reproducir High Forever remix' 'High Forever' $false),
  (BotonCancion 'Pausar High Forever' 'High Forever' $true),
  (BotonCancion 'Reproducir High Forever, de Petite Meller' 'High Forever' $false),
  (BotonCancion 'Reproducir High Forever - Marlon Hoffstadt Remix, de Petite Meller' 'High Forever' $false))|ConvertTo-Json -Compress
'''
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16-le')).decode()],text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),[True,False,True,False,False,True,True,False])


class YoutubeFondo(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node requerido')
    def test_estado_no_confunde_silencio_con_pausa(self):
        codigo=r'''
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
let listener;const video={readyState:4,paused:false,ended:false,muted:true,volume:0};
const chrome={runtime:{id:'capri',onMessage:{addListener:l=>listener=l},sendMessage:async()=>({ok:true})}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{chrome,document:{querySelector:()=>video},location:{href:'https://www.youtube.com/watch?v=uno'},setInterval:()=>0});
function estado(){let r;listener({tipo:'capri_estado'},{id:'capri'},v=>r=v);return r}
assert.equal(estado().reproduciendo,true);video.paused=true;assert.equal(estado().reproduciendo,false);
video.readyState=0;assert.equal(estado().video,false);
let llamado=false;listener({tipo:'capri_estado'},{id:'otra'},()=>llamado=true);assert.equal(llamado,false);
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri/content.js')],text=True,capture_output=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)

    @unittest.skipUnless(shutil.which('node'),'Node requerido')
    def test_pausa_reanuda_silenciado_ambiguedad_y_cierre(self):
        codigo=r'''
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
let listener,activa=9,ultimoResultado,entregas=[],numero=0;
let tabs=[{id:1,url:'https://www.youtube.com/watch?v=uno'},{id:2,url:'https://www.youtube.com/watch?v=dos'},{id:9,url:'https://example.org'}];
let estados={1:{video:true,reproduciendo:true},2:{video:true,reproduciendo:false}};
const chrome={runtime:{id:'capri',onMessage:{addListener:l=>listener=l}},tabs:{
 query:async q=>q.active?tabs.filter(t=>t.id===activa):tabs,
 sendMessage:async(id,m)=>{
  if(m.tipo==='capri_estado')return estados[id];
  entregas.push(id);if(m.tarea.accion==='pausa')estados[id].reproduciendo=false;
  return {ok:true,estado:'Paused'};
 }
}};
let accion='pausa';
const fetch=async(url,op)=>{
 if(url.endsWith('/siguiente'))return {ok:true,json:async()=>({tarea:{id:String(++numero),accion,datos:{}}})};
 ultimoResultado=JSON.parse(op.body).resultado;return {ok:true};
};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{chrome,fetch,URL,AbortSignal});
const consultar=()=>new Promise(resolve=>listener({tipo:'capri_consultar'},{id:'capri',tab:{id:2},url:tabs[0].url},resolve));
(async()=>{
 await consultar();assert.deepEqual(entregas,[1]); // página ajena activa
 accion='reanudar';await consultar();assert.deepEqual(entregas,[1,1]); // recuerda el pausado
 estados[1].reproduciendo=true;estados[2].reproduciendo=true;
 await consultar();assert.equal(ultimoResultado.codigo,'varios_videos');assert.equal(entregas.length,2);
 activa=2;await consultar();assert.equal(entregas.at(-1),2);
 tabs=tabs.filter(t=>t.id!==2);activa=9;await consultar();assert.equal(entregas.at(-1),1);
 estados[1].reproduciendo=false;await consultar();assert.equal(entregas.at(-1),1);
 tabs=tabs.filter(t=>t.id!==1);await consultar();assert.equal(ultimoResultado.codigo,'sin_video');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri/worker.js')],text=True,capture_output=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
