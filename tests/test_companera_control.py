from contextlib import contextmanager
from pathlib import Path
import json
import shutil
import tempfile
import unittest
import time
from unittest.mock import patch
from test_capri import PruebasTk
from control_pc import ControlPC,validar
from intenciones import Interprete
from intenciones import Decision
from core import Orden
from companera import Companera
import app


class ControlArchivos(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.archivo=self.base/'foto.png';self.archivo.write_bytes(b'prueba')
        self.activo=True;self.reciclados=[];self.ahora=10
        self.pc=ControlPC(lambda:self.activo,[self.base],basura=self.reciclados.append,reloj=lambda:self.ahora)

    def test_desactivado_no_puede_operar_y_confirmar_no_lo_salta(self):
        self.activo=False
        with self.assertRaises(PermissionError):self.pc.ejecutar('archivo_borrar',str(self.archivo))
        self.assertIsNone(self.pc.confirmar('sí'));self.assertTrue(self.archivo.exists());self.assertFalse(self.reciclados)

    def test_borrado_pregunta_ruta_exacta_y_solo_confirma_una_vez(self):
        texto=self.pc.ejecutar('archivo_borrar','foto.png')
        # Windows puede expandir el alias temporal 8.3 (RUNNER~1) al resolver.
        self.assertIn(str(self.archivo.resolve()),texto);self.assertFalse(self.reciclados)
        self.pc.confirmar('sí, confirmo');self.assertEqual(self.reciclados,[self.archivo.resolve()])
        self.assertIsNone(self.pc.confirmar('sí'));self.assertEqual(len(self.reciclados),1)

    def test_negativa_cancela_y_otra_peticion_invalida_confirmacion_anterior(self):
        self.pc.ejecutar('archivo_borrar','foto.png');self.pc.confirmar('no')
        self.assertIsNone(self.pc.pendiente);self.pc.confirmar('sí');self.assertFalse(self.reciclados)
        self.pc.ejecutar('archivo_borrar','foto.png');self.assertIsNone(self.pc.confirmar('qué hora es'))
        self.pc.confirmar('sí');self.assertFalse(self.reciclados)

    def test_archivo_cambiado_caducidad_y_permiso_revocado_no_borran(self):
        self.pc.ejecutar('archivo_borrar','foto.png');self.archivo.write_bytes(b'nuevo contenido')
        self.assertIn('cambió',self.pc.confirmar('sí'));self.assertFalse(self.reciclados)
        self.pc.ejecutar('archivo_borrar','foto.png');self.ahora+=121
        self.assertIn('caducó',self.pc.confirmar('sí'));self.assertFalse(self.reciclados)
        self.pc.ejecutar('archivo_borrar','foto.png');self.activo=False
        self.pc.confirmar('sí');self.assertFalse(self.reciclados)

    def test_homonimos_no_se_eligen_y_mover_no_sobrescribe(self):
        sub=self.base/'otra';sub.mkdir();(sub/'foto.png').write_bytes(b'otra')
        with self.assertRaises(ValueError):self.pc.ejecutar('archivo_borrar','foto.png')
        destino=self.base/'destino.png';destino.write_bytes(b'existente')
        with self.assertRaises(ValueError):self.pc.ejecutar('archivo_mover',str(self.archivo)+' | '+str(destino))
        self.assertEqual(destino.read_bytes(),b'existente');self.assertFalse(self.reciclados)

    def test_renombrado_solo_tras_confirmacion_y_nunca_ejecuta_comandos(self):
        self.pc.ejecutar('archivo_renombrar',str(self.archivo)+' | nueva.png')
        self.assertTrue(self.archivo.exists());self.assertFalse((self.base/'nueva.png').exists())
        self.pc.confirmar('sí, confirmo');self.assertTrue((self.base/'nueva.png').exists())
        with self.assertRaises(ValueError):self.pc.ejecutar('powershell','Remove-Item algo')

    def test_router_exige_permiso_y_objetivo_literal(self):
        datos={'accion':'archivo_borrar','valor':'foto.png'};i=Interprete();contexto=i.contexto()
        self.assertIsNone(i.validar(datos,'borra foto.png',contexto).orden)
        self.assertEqual(i.validar(datos,'borra foto.png',contexto,True).orden.tipo,'archivo_borrar')
        self.assertIsNone(i.validar(datos,'borra otra.png',contexto,True).orden)
        self.assertIsNone(i.validar(datos,'no borres foto.png',contexto,True).orden)
        self.assertFalse(validar('archivo_borrar','seleccionado','borra algo'))


class ModoPersonaje(PruebasTk):
    @contextmanager
    def capri(self):
        with tempfile.TemporaryDirectory() as d,patch.object(app,'BASE',Path(d)),patch.object(app.Voz,'parar'),patch.object(app.Voz,'sonido_colgar'):
            assets=Path(d)/'assets';assets.mkdir();origen=Path(__file__).resolve().parents[1]/'assets'
            for n in ('capri-base-v2.png','capri-bocas-v2.png','capri-personaje-v1.png','capri-caminar-v1.png','capri-saludo-v1.png'):shutil.copy2(origen/n,assets/n)
            c=app.Capri(hotkeys=False);c.root.withdraw();c.cfg['voz']=False
            try:yield c,Path(d)
            finally:c.cerrar()

    def test_modos_excluyentes_entrada_al_pedir_y_permiso_desactivado(self):
        with self.capri() as (c,p),patch('companera.visibles',return_value=[]):
            self.assertFalse(c.cfg['control_ampliado']);c.guardar('modo_visual','personaje');c.animar()
            self.assertIsNotNone(c.transito);c.transito['inicio']-=c.transito['duracion']+.1;c.animar()
            self.assertTrue(c.canvas.find_withtag('personaje'));self.assertFalse(c.entrada_compacta.winfo_manager())
            self.assertEqual(len(c.canvas.find_withtag('personaje')),1)
            self.assertTrue(all(c.canvas.type(i)=='image' for i in c.canvas.find_all()))
            c.entrada_compacta.dar_foco();self.assertFalse(c.entrada_compacta.winfo_manager());self.assertTrue(c.ventana_entrada.winfo_exists())
            c.guardar('control_ampliado',True);f=p/'foto.png';f.write_bytes(b'prueba')
            c.control_pc.ejecutar('archivo_borrar',str(f));self.assertIsNotNone(c.control_pc.pendiente)
            c.guardar('control_ampliado',False);self.assertIsNone(c.control_pc.pendiente);self.assertTrue(f.exists())
            c.guardar('modo_visual','pantalla');self.assertIsNotNone(c.transito);c.transito['inicio']-=c.transito['duracion']+.1;c.animar();self.assertFalse(c.canvas.find_withtag('personaje'))
            self.assertEqual(c.entrada_compacta.winfo_manager(),'pack')
            self.assertEqual(json.loads((p/'ajustes.json').read_text())['modo_visual'],'pantalla')

    def test_se_sienta_sigue_ventana_y_cae_cuando_desaparece(self):
        with self.capri() as (c,_),patch('companera.area_trabajo',return_value=(0,0,1000,800)):
            p=c.companera;p.redimensionar(1);p.iniciar()
            ventana={'id':7,'titulo':'Prueba','rect':(100,400,800,700)}
            with patch('companera.visibles',return_value=[ventana]):p.posar(200,245)
            self.assertIsNotNone(p.salto)
            with patch('companera.visibles',return_value=[ventana]):p.tick(ahora=p.ultimo+2)
            self.assertEqual(p.soporte,7)
            movida=dict(ventana,rect=(250,450,950,750))
            with patch('companera.visibles',return_value=[movida]):p.tick(pausa=True,ahora=p.ultimo+1)
            self.assertIsNotNone(p.salto);self.assertEqual(p.salto['id'],7)
            self.assertAlmostEqual(p.salto['destino'][1],450-p.alto*.64)
            p.soporte=7;p.salto=None
            y=p.y;p.proxima_accion=p.ultimo+100
            with patch('companera.visibles',return_value=[]),patch('companera.random.random',return_value=1):p.tick(ahora=p.ultimo+1)
            self.assertIsNone(p.soporte);self.assertIsNone(p.salto);self.assertGreater(p.y,y)

    def test_confirmacion_en_chat_no_reconsulta_modelo_y_no_borra_antes(self):
        with self.capri() as (c,p):
            archivo=p/'imagen.png';archivo.write_bytes(b'archivo de prueba')
            c.cfg.update(ia=True,control_ampliado=True);reciclados=[];c.control_pc.basura=reciclados.append
            def esperar():
                fin=time.monotonic()+2
                while c.ocupada and time.monotonic()<fin:c.poll();time.sleep(.01)
                self.assertFalse(c.ocupada)
            with patch.object(c.interprete,'resolver',return_value=Decision(Orden('archivo_borrar',str(archivo)))) as modelo:
                c.enviar('borra '+str(archivo));esperar()
                self.assertTrue(archivo.exists());self.assertFalse(reciclados);self.assertIsNotNone(c.control_pc.pendiente)
                c.enviar('sí, confirmo');esperar()
                self.assertEqual(reciclados,[archivo.resolve()]);self.assertEqual(modelo.call_count,1)
