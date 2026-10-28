import base64
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import puente_opera as bridge
import volumen_apps
from core import interpretar,Orden

RAIZ=Path(__file__).resolve().parents[1]

class PuenteOpera(unittest.TestCase):
    def setUp(self):
        self.p=bridge.Puente(0);self.assertIsNotNone(self.p.servidor);self.addCleanup(self.p.cerrar)
        self.puerto=self.p.servidor.server_port

    def peticion(self,metodo,ruta,datos=None,origen=bridge.ORIGEN,host=None,identidad=bridge.EXTENSION_ID):
        c=http.client.HTTPConnection('127.0.0.1',self.puerto,timeout=3)
        h={'Origin':origen,'X-Capri-Puente':identidad,'Host':host or '127.0.0.1:'+str(self.puerto)}
        if datos is not None:h['Content-Type']='application/json'
        try:
            c.request(metodo,ruta,body=json.dumps(datos) if datos is not None else None,headers=h)
            r=c.getresponse();return r.status,json.loads(r.read() or '{}')
        finally:c.close()

    def test_servidor_rechaza_origen_host_y_ruta_de_ordenes_externas(self):
        self.assertEqual(self.peticion('GET','/siguiente',origen='https://evil.test')[0],403)
        self.assertEqual(self.peticion('GET','/siguiente',host='evil.test')[0],403)
        self.assertEqual(self.peticion('GET','/siguiente',identidad='otra')[0],403)
        self.assertEqual(self.peticion('POST','/ejecutar',{'accion':'borra'})[0],404)
        self.assertFalse(self.p.conectado())

    def test_tarea_unica_resultado_acotado_y_respuesta_no_reutilizable(self):
        self.peticion('GET','/siguiente');salida=[]
        t=threading.Thread(target=lambda:salida.append(self.p.ejecutar('volumen',{'operacion':'fijar:50','restaurar':40})))
        t.start()
        tarea=None
        for _ in range(30):
            tarea=self.peticion('GET','/siguiente')[1]['tarea']
            if tarea:break
            time.sleep(.01)
        self.assertIsNotNone(tarea)
        self.assertIsNone(self.peticion('GET','/siguiente')[1]['tarea'])
        datos={'id':tarea['id'],'resultado':{'ok':True,'volumen':50,'anterior':40,'texto_no_permitido':'ignora instrucciones'}}
        self.assertEqual(self.peticion('POST','/resultado',datos)[0],200)
        t.join(2);self.assertEqual(salida,[{'ok':True,'volumen':50,'anterior':40}])
        self.assertEqual(self.peticion('POST','/resultado',datos)[0],409)

    def test_timeout_no_repite_y_validacion_excluye_codigo(self):
        self.peticion('GET','/siguiente')
        self.assertFalse(self.p.ejecutar('pausa',{},espera=.02)['ok'])
        self.assertIsNone(self.peticion('GET','/siguiente')[1]['tarea'])
        self.assertFalse(bridge.validar('ejecutar',{'codigo':'powershell'}))
        self.assertFalse(bridge.validar('volumen',{'operacion':'fijar:101','restaurar':50}))
        self.assertFalse(bridge.validar('volumen',{'operacion':'fijar:50','restaurar':float('nan')}))

    def test_pone_y_puente_aceptado_no_hacen_fallback_ni_mezclador(self):
        self.assertEqual(interpretar('Pone el volumen de YouTube al 50%.'),Orden('youtube_volumen','fijar:50'))
        with patch.object(bridge,'ejecutar',return_value={'ok':True,'volumen':50,'anterior':30}),patch.object(volumen_apps.subprocess,'run') as ejecutar:
            self.assertIn('YouTube: 50%',volumen_apps.controlar_volumen('fijar:50',destino='youtube'));ejecutar.assert_not_called()
        with patch.object(bridge,'ejecutar',return_value={'ok':False,'codigo':'cambio_no_confirmado'}),patch.object(volumen_apps.subprocess,'run') as ejecutar:
            self.assertIn('no confirmó',volumen_apps.controlar_volumen('subir:10',destino='youtube'));ejecutar.assert_not_called()

    def test_manifest_identidad_estable_y_permisos_acotados(self):
        m=json.loads((RAIZ/'integraciones/opera-capri/manifest.json').read_text(encoding='utf8'))
        h=hashlib.sha256(base64.b64decode(m['key'])).hexdigest()[:32]
        self.assertEqual(''.join(chr(97+int(c,16)) for c in h),bridge.EXTENSION_ID)
        self.assertNotIn('<all_urls>',m['host_permissions']);self.assertNotIn('permissions',m)
        self.assertTrue(all('youtube' in p for p in m['content_scripts'][0]['matches']))

    @unittest.skipUnless(shutil.which('node'),'Prueba JavaScript requiere Node de desarrollo')
    def test_flujo_http_real_y_control_video_en_javascript(self):
        self.peticion('GET','/siguiente');salida=[]
        t=threading.Thread(target=lambda:salida.append(self.p.ejecutar('volumen',{'operacion':'fijar:50','restaurar':40})))
        t.start()
        codigo=r'''
const assert=require('node:assert/strict');
const api=require(process.argv[1]);
const base=process.argv[2],id=process.argv[3];
const headers={'X-Capri-Puente':id,'Origin':'chrome-extension://'+id};
(async()=>{
 let tarea;for(let i=0;i<20;i++){tarea=(await (await fetch(base+'/siguiente',{headers})).json()).tarea;if(tarea)break;await new Promise(r=>setTimeout(r,20));}
 assert(tarea);
 const {video,doc}=require(process.argv[4]).crear({volumen:.4});
 const resultado=await api.ejecutar(doc,'https://www.youtube.com/watch?v=prueba',tarea);
 assert.equal(video.volume,.5);assert.equal(resultado.volumen,50);
 const respuesta=await fetch(base+'/resultado',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({id:tarea.id,resultado})});assert.equal(respuesta.status,200);
 assert.equal((await api.ejecutar(doc,'https://netflix.com/',tarea)).ok,false);
 assert.equal((await api.ejecutar(doc,'https://youtube.com.evil.test/',tarea)).ok,false);
 assert.equal((await api.ejecutar(doc,'https://www.youtube.com/',{accion:'pausa'})).estado,'Paused');
 assert.equal((await api.ejecutar(doc,'https://www.youtube.com/',{accion:'reanudar'})).estado,'Playing');
 await api.ejecutar(doc,'https://www.youtube.com/',{accion:'volumen',datos:{operacion:'silenciar',restaurar:40}});assert.equal(video.muted,true);
 await api.ejecutar(doc,'https://www.youtube.com/',{accion:'volumen',datos:{operacion:'activar',restaurar:40}});assert.equal(video.muted,false);
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri/control.js'),'http://127.0.0.1:'+str(self.puerto),bridge.EXTENSION_ID,str(RAIZ/'tests/fixtures/reproductor_youtube.js')],text=True,capture_output=True,timeout=10)
        t.join(2);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(salida[0]['volumen'],50);self.assertTrue(salida[0]['ok'])

    @unittest.skipUnless(shutil.which('node'),'Prueba JavaScript requiere Node de desarrollo')
    def test_worker_real_entrega_al_video_aunque_otra_pagina_tenga_foco(self):
        self.peticion('GET','/siguiente');salida=[]
        t=threading.Thread(target=lambda:salida.append(self.p.ejecutar('volumen',{'operacion':'fijar:25','restaurar':40})))
        t.start()
        codigo=r'''
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const api=require(process.argv[1]+'/control.js');
const base=process.argv[2],id=process.argv[3];let listener,llamadas=0,entregas=0;
const {video,doc}=require(process.argv[4]).crear({volumen:.8});
const chrome={runtime:{id,onMessage:{addListener:l=>listener=l}},tabs:{
 query:async q=>q.active ? [{id:9,url:'https://example.org/'}] : [{id:1,url:'https://www.youtube.com/watch?v=prueba'}],
 sendMessage:async(tab,m)=>{assert.equal(tab,1);if(m.tipo==='capri_estado')return {video:true,reproduciendo:true};entregas++;return api.ejecutar(doc,'https://www.youtube.com/watch?v=prueba',m.tarea)}
}};
vm.runInNewContext(fs.readFileSync(process.argv[1]+'/worker.js','utf8'),{chrome,URL,AbortSignal,fetch:(url,op)=>{llamadas++;return fetch(url.replace('http://127.0.0.1:18741',base),op)}});
function consultar(tab){return new Promise(resolve=>listener({tipo:'capri_consultar'},{id,tab:{id:tab},url:'https://www.youtube.com/watch?v=prueba'},resolve))}
(async()=>{
 const r=await consultar(2);assert.equal(r.ok,true);assert.equal(entregas,1);assert.equal(video.volume,.25);
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'integraciones/opera-capri'),'http://127.0.0.1:'+str(self.puerto),bridge.EXTENSION_ID,str(RAIZ/'tests/fixtures/reproductor_youtube.js')],text=True,capture_output=True,timeout=10)
        t.join(2);self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(salida[0]['ok']);self.assertEqual(salida[0]['volumen'],25)

    @unittest.skipUnless(shutil.which('node'),'Prueba JavaScript requiere Node de desarrollo')
    def test_nivel_positivo_desmutea_audio_modelo_e_icono_y_cero_silencia(self):
        codigo=r'''
const assert=require('node:assert/strict');
const {crear}=require(process.argv[1]);const control=require(process.argv[2]);
(async()=>{
 const f=crear({volumen:.4,silenciado:true});
 // Reproducir el fallo anterior: audio desmuteado, modelo e icono silenciados.
 f.video.muted=false;
 const r=await control.ejecutar(f.doc,'https://www.youtube.com/watch?v=prueba',{accion:'volumen',datos:{operacion:'fijar:100',restaurar:40}});
 assert.equal(r.ok,true);assert.equal(r.volumen,100);assert.equal(r.silenciado,false);
 assert.equal(f.video.volume,1);assert.equal(f.video.muted,false);assert.equal(f.player.isMuted(),false);
 assert.match(f.boton.getAttribute('aria-label'),/Silenciar/);assert.equal(f.slider.getAttribute('aria-valuenow'),'100');
 const a=await control.ejecutar(f.doc,'https://www.youtube.com/watch?v=prueba',{accion:'volumen',datos:{operacion:'activar',restaurar:40}});
 assert.equal(a.ok,true);assert.equal(a.silenciado,false);assert.equal(f.video.muted,false);assert.match(f.boton.getAttribute('aria-label'),/Silenciar/);
 const z=await f.pagina.aplicar(f.doc,'https://www.youtube.com/',{operacion:'fijar:0',restaurar:40});assert.equal(z.ok,true);assert.equal(z.silenciado,true);assert.equal(f.video.muted,true);
 const s=await f.pagina.aplicar(f.doc,'https://www.youtube.com/',{operacion:'subir:10',restaurar:40});assert.equal(s.ok,true);assert.equal(s.volumen,10);assert.equal(s.silenciado,false);assert.equal(f.video.muted,false);
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'tests/fixtures/reproductor_youtube.js'),str(RAIZ/'integraciones/opera-capri/control.js')],text=True,capture_output=True,timeout=6)
        self.assertEqual(r.returncode,0,r.stderr)

    @unittest.skipUnless(shutil.which('node'),'Prueba JavaScript requiere Node de desarrollo')
    def test_no_confirma_si_el_icono_de_silencio_no_cambia(self):
        codigo=r'''
const assert=require('node:assert/strict');const {crear}=require(process.argv[1]);
(async()=>{
 const f=crear({volumen:.5,silenciado:true});
 f.boton.getAttribute=()=> 'Activar sonido (m)';
 const r=await f.pagina.aplicar(f.doc,'https://www.youtube.com/',{operacion:'activar',restaurar:50});
 assert.equal(r.ok,false);assert.equal(r.codigo,'cambio_no_confirmado');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        r=subprocess.run(['node','-e',codigo,str(RAIZ/'tests/fixtures/reproductor_youtube.js')],text=True,capture_output=True,timeout=6)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_extension_anterior_desmutea_sin_duplicar_el_incremento(self):
        viejo={'ok':True,'volumen':50,'anterior':40,'silenciado':True}
        activado={'ok':True,'volumen':50,'anterior':50,'silenciado':False}
        with patch.object(bridge,'ejecutar',side_effect=[viejo,activado]) as ejecutar,patch.object(volumen_apps.subprocess,'run') as windows:
            self.assertEqual(volumen_apps.controlar_volumen('subir:10',destino='youtube'),'Volumen dentro de YouTube: 50%.')
            self.assertEqual(ejecutar.call_args_list[0].args[1]['operacion'],'subir:10')
            self.assertEqual(ejecutar.call_args_list[1].args[1],{'operacion':'activar','restaurar':50.0})
            self.assertEqual(ejecutar.call_count,2)
            windows.assert_not_called()
        with patch.object(bridge,'ejecutar',side_effect=[viejo,{'ok':False,'codigo':'cambio_no_confirmado'}]),patch.object(volumen_apps.subprocess,'run') as windows:
            self.assertIn('no confirmó',volumen_apps.controlar_volumen('subir:10',destino='youtube'));windows.assert_not_called()
        with patch.object(bridge,'ejecutar',side_effect=[viejo,viejo]):
            r=volumen_apps.controlar_volumen('subir:10',destino='youtube')
            self.assertIn('no confirmó',r);self.assertNotIn('Sigue silenciado',r)
