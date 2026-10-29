import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import Orden
import navegador
import puente_opera as puente

RAIZ=Path(__file__).resolve().parents[1]


class ResultadosYouTube(unittest.TestCase):
    def test_resultado_pasa_por_puente_sin_abrir_busqueda_ni_uia(self):
        with patch('puente_opera.ejecutar',return_value={'ok':True,'estado':'Solicitado'}) as ejecutar,patch('navegador.subprocess.run') as proceso,patch('core.abrir_opera') as abrir:
            respuesta=navegador.ejecutar_youtube(Orden('youtube_resultado','1'))
            self.assertIn('resultado 1',respuesta)
            ejecutar.assert_called_once_with('resultado',{'indice':1})
            proceso.assert_not_called();abrir.assert_not_called()

    def test_respuesta_incierta_o_resultado_inexistente_no_repite_clic(self):
        for codigo in ('cambio_no_confirmado','resultado_no_disponible','varios_resultados'):
            with self.subTest(codigo=codigo),patch('puente_opera.ejecutar',return_value={'ok':False,'codigo':codigo}),patch('navegador.subprocess.run') as proceso:
                self.assertTrue(navegador.ejecutar_youtube(Orden('youtube_resultado','2')))
                proceso.assert_not_called()

    def test_indice_acotado_sin_parametros_adicionales(self):
        self.assertTrue(puente.validar('resultado',{'indice':1}))
        for datos in ({'indice':True},{'indice':0},{'indice':11},{'indice':'1'},{'indice':1,'url':'https://example.org'}):
            self.assertFalse(puente.validar('resultado',datos))

    @unittest.skipUnless(shutil.which('node'),'Node requerido')
    def test_dom_sin_reproductor_elige_video_excluye_anuncios_shorts_y_duplicados(self):
        codigo=r'''
const assert=require('node:assert/strict');
const api=require(process.argv[1]);
let pulsados=[],timers=[];global.setTimeout=f=>{timers.push(f)};
const enlace=href=>({href,click:()=>pulsados.push(href)});
const tarjeta=(urls,omitida=false)=>({closest:()=>omitida?{}:null,querySelectorAll:()=>urls.map(enlace)});
let tarjetas=[tarjeta(['https://www.youtube.com/watch?v=anuncio'],true),
 tarjeta(['https://example.org/watch?v=fuera']),tarjeta(['https://www.youtube.com/shorts/short']),
 tarjeta(['https://www.youtube.com/watch?v=uno','https://www.youtube.com/watch?v=uno&t=3']),
 tarjeta(['https://www.youtube.com/watch?v=uno']),tarjeta(['https://www.youtube.com/watch?v=dos'])];
const doc={querySelector:s=>s==='ytd-search'?{querySelectorAll:()=>tarjetas}:null};
(async()=>{
 let r=await api.ejecutar(doc,'https://www.youtube.com/results?search_query=High+Forever',{accion:'resultado',datos:{indice:1}});
 assert.equal(r.ok,true);assert.equal(pulsados.length,0);timers.shift()();
 assert.deepEqual(pulsados,['https://www.youtube.com/watch?v=uno']);
 r=await api.ejecutar(doc,'https://www.youtube.com/results?search_query=x',{accion:'resultado',datos:{indice:2}});
 assert.equal(r.ok,true);timers.shift()();assert.equal(pulsados[1],'https://www.youtube.com/watch?v=dos');
 r=await api.ejecutar(doc,'https://www.youtube.com/results?search_query=x',{accion:'resultado',datos:{indice:3}});
 assert.equal(r.codigo,'resultado_no_disponible');assert.equal(timers.length,0);
 for(const indice of [0,11,'1'])assert.equal((await api.ejecutar(doc,'https://www.youtube.com/results?search_query=x',{accion:'resultado',datos:{indice}})).codigo,'operacion_invalida');
 assert.equal((await api.ejecutar(doc,'https://example.org/results',{accion:'resultado',datos:{indice:1}})).codigo,'pagina_invalida');
 assert.equal((await api.ejecutar(doc,'https://www.youtube.com/watch?v=uno',{accion:'resultado',datos:{indice:1}})).codigo,'sin_resultados');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri/control.js')],capture_output=True,text=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)

    @unittest.skipUnless(shutil.which('node'),'Node requerido')
    def test_worker_elige_resultados_sin_video_no_el_otro_video_que_suena(self):
        codigo=r'''
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
let listener,activa=9,salida,entregas=[];
let tabs=[{id:1,url:'https://www.youtube.com/watch?v=musica'},{id:2,url:'https://www.youtube.com/results?search_query=x'},{id:9,url:'https://example.org'}];
const estados={1:{video:true,reproduciendo:true,resultados:false},2:{video:false,reproduciendo:false,resultados:true},3:{video:false,resultados:true}};
const chrome={runtime:{id:'capri',onMessage:{addListener:l=>listener=l}},tabs:{query:async q=>q.active?tabs.filter(t=>t.id===activa):tabs,
 sendMessage:async(id,m)=>{if(m.tipo==='capri_estado')return estados[id];entregas.push(id);assert.equal(m.tarea.datos.indice,1);return{ok:true,estado:'Solicitado'}}}};
const fetch=async(url,op)=>{if(url.endsWith('/siguiente'))return{ok:true,json:async()=>({tarea:{id:'tarea',accion:'resultado',datos:{indice:1}}})};salida=JSON.parse(op.body).resultado;return{ok:true}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{chrome,fetch,URL,AbortSignal});
const consultar=()=>new Promise(resolve=>listener({tipo:'capri_consultar'},{id:'capri',tab:{id:2},url:tabs[1].url},resolve));
(async()=>{
 await consultar();assert.deepEqual(entregas,[2]);assert.equal(salida.ok,true);
 tabs.push({id:3,url:'https://www.youtube.com/results?search_query=y'});
 await consultar();assert.equal(salida.codigo,'varios_resultados');assert.deepEqual(entregas,[2]);
 activa=3;await consultar();assert.deepEqual(entregas,[2,3]);
 tabs=tabs.filter(t=>![2,3].includes(t.id));await consultar();assert.equal(salida.codigo,'sin_resultados');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri/worker.js')],capture_output=True,text=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
