import json
import tkinter as nativo
from unittest.mock import patch,Mock
from test_capri import PruebasTk
import test_companera_control as fixtures
import tema_ui
from disenos_pantalla import DISENOS,superficie
from entrada import Entrada


class TemaYDisenos(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def tearDown(self):
        tema_ui.activar(tema_ui.PREDETERMINADO)
        super().tearDown()

    def test_color_actualiza_ventanas_existentes_nuevas_y_conserva_arte_y_efectos(self):
        original=tema_ui.tk.Toplevel
        class Oculta(original):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.withdraw()
            def deiconify(self):self.withdraw()
        with self.capri() as (c,carpeta),patch.object(tema_ui.tk,'Toplevel',Oculta),patch.object(c,'cargar_microfonos'),patch.object(c.ia,'modelos',return_value=[]):
            c.configurar();c.abrir_chat();c.abrir_aspectos()
            foto=c.avatar.fotos[0];imagen=c.avatar.estados[0].tobytes()
            e=c.entrada_compacta;e.poner('Borrador sin enviar')
            efecto=nativo.Canvas(c.root);item=efecto.create_line(0,0,5,5,fill='#ff4267')
            antes=c.marco_ajustes.cuerpo.cget('bg')
            c.guardar('color_interfaz','#40d9e6')
            self.assertNotEqual(c.marco_ajustes.cuerpo.cget('bg'),antes)
            self.assertEqual(c.marco_ajustes.cuerpo.cget('bg'),tema_ui.color('#10090d'))
            self.assertEqual(c.panel_ajustes.estilo.lookup('Capri.TCombobox','fieldbackground'),tema_ui.color('#211018'))
            self.assertEqual(c.campo_entrada.cget('bg'),tema_ui.color('#180d13'))
            self.assertEqual(c.chat.tag_cget('capri','foreground'),'#40d9e6')
            self.assertEqual(e.entrada.cget('insertbackground'),tema_ui.color('#ff9eaf'))
            self.assertEqual(e.entrada.get(),'Borrador sin enviar')
            self.assertIs(c.avatar.fotos[0],foto);self.assertEqual(c.avatar.estados[0].tobytes(),imagen)
            self.assertEqual(efecto.itemcget(item,'fill'),'#ff4267')
            c.conectar_opera=Mock()
            c.abrir_colores();p=c.panel_colores
            self.assertEqual(p.marco.cuerpo.cget('bg'),tema_ui.color('#10090d'))
            p.hex.set('#87aaff');p.aplicar_hex()
            self.assertEqual(c.cfg['color_interfaz'],'#87aaff')
            datos=json.loads((carpeta/'ajustes.json').read_text(encoding='utf8'))
            self.assertEqual(datos['color_interfaz'],'#87aaff')
            p.hex.set('invalido');p.aplicar_hex();self.assertEqual(c.cfg['color_interfaz'],'#87aaff')
            c.guardar('color_interfaz',tema_ui.PREDETERMINADO)
            self.assertEqual(c.marco_ajustes.cuerpo.cget('bg'),antes)
            self.assertEqual(e.entrada.get(),'Borrador sin enviar')

    def test_diseno_cambia_geometria_de_monitor_y_entrada_sin_cambiar_color_o_borrador(self):
        root=tema_ui.tk.Tk();root.withdraw()
        try:
            c=tema_ui.LienzoUI(root);e=Entrada(root,Mock(),Mock());e.poner('Hola')
            monitores=[];entradas=[]
            for clave in DISENOS:
                c.delete('all');superficie(c,clave,360,292)
                monitores.append(tuple((c.type(i),tuple(c.coords(i))) for i in c.find_all()))
                e.aplicar_aspecto(clave)
                entradas.append(tuple((e.type(i),tuple(e.coords(i))) for i in e.find_withtag('marco')))
                self.assertEqual(e.entrada.get(),'Hola');self.assertEqual(tema_ui.actual(),tema_ui.PREDETERMINADO)
            self.assertEqual(len(set(monitores)),6);self.assertEqual(len(set(entradas)),6)
        finally:root.destroy()

    def test_menu_sustituye_escribir_por_color_y_conserva_juegos_en_personaje(self):
        with self.capri() as (c,_),patch('menu_radial.MenuRadial') as menu:
            c.abrir_menu_radial(Mock(x_root=400,y_root=300))
            opciones=menu.call_args.args[3]
            self.assertIn('Color',[n for n,_ in opciones]);self.assertNotIn('Escribir',[n for n,_ in opciones])
            c.companera.redimensionar(1);c.cfg['modo_visual']='personaje';c.abrir_menu_radial(Mock(x_root=400,y_root=300))
            self.assertIn('Juegos',[n for n,_ in menu.call_args.args[3]])

    def test_color_y_diseno_se_recuperan_al_reabrir(self):
        import app
        with self.capri() as (c,_):
            c.guardar('color_interfaz','#689bff');c.guardar('aspecto_pantalla','terminal')
            c.cerrar_inmediato()
            nuevo=app.Capri(hotkeys=False);nuevo.root.withdraw()
            try:
                self.assertEqual(tema_ui.actual(),'#689bff')
                self.assertEqual(nuevo.avatar.aspecto,'terminal')
                self.assertEqual(nuevo.entrada_compacta.diseno,'terminal')
                self.assertEqual(nuevo.entrada_compacta.entrada.cget('bg'),tema_ui.color('#170c12'))
            finally:nuevo.cerrar_inmediato()

    def test_contornos_no_se_cruzan_en_chat_o_monitor(self):
        root=tema_ui.tk.Tk();root.withdraw()
        def cruz(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        try:
            c=tema_ui.LienzoUI(root)
            for diseno in DISENOS:
                for w,h,chat in ((360,292,False),(360,46,True),(200,46,True)):
                    c.delete('all');superficie(c,diseno,w,h,chat=chat)
                    for item in c.find_all():
                        if c.type(item)!='polygon' or c.itemcget(item,'smooth')=='true':continue
                        p=c.coords(item);p=list(zip(p[::2],p[1::2]));n=len(p)
                        for i in range(n):
                            a,b=p[i],p[(i+1)%n]
                            for j in range(i+2,n):
                                if i==0 and j==n-1:continue
                                u,v=p[j],p[(j+1)%n]
                                interseca=cruz(a,b,u)*cruz(a,b,v)<0 and cruz(u,v,a)*cruz(u,v,b)<0
                                self.assertFalse(interseca,(diseno,w,h,p))
        finally:root.destroy()

    def test_mas_no_repite_color_y_cerrar_se_pulsa_desde_el_sector_inferior(self):
        from menu_radial import MenuRadial
        from types import SimpleNamespace
        with self.capri() as (c,_),patch('menu_radial.MenuRadial') as menu:
            c.abrir_menu_radial(Mock(x_root=400,y_root=300))
            mas=dict(menu.call_args.args[3])['Más']
            self.assertNotIn('Color',[n for n,_ in mas])
        cerrar=Mock();m=MenuRadial.__new__(MenuRadial)
        m.centro=100;m.radio=90;m.pila=[[]];m.cerrado=False;m.cerrar=Mock()
        m.opciones=[('Llamada',Mock()),('Asomo',Mock()),('YouTube',Mock()),('LoL',Mock()),('Cerrar Capri',cerrar)]
        m.click(SimpleNamespace(x=100,y=170))
        cerrar.assert_called_once();m.cerrar.assert_called_once()

    def test_estudio_vector_separan_entry_de_envio_sin_dobles_bordes_al_hablar(self):
        root=tema_ui.tk.Tk();root.withdraw()
        try:
            for diseno in ('compacto','minimal'):
                enviar=Mock();e=Entrada(root,enviar,Mock(),aspecto=diseno);e.poner('Borrador')
                for ancho in (270,360,576):
                    e.configure(width=ancho);e.activa=True;e.dibujar()
                    fin=e.coords(e.ventana)[0]+float(e.itemcget(e.ventana,'width'))
                    limite=ancho-(44 if diseno=='compacto' else 48)
                    self.assertLessEqual(fin,limite-8)
                    for item in e.find_withtag('marco'):
                        if e.type(item)=='rectangle' and 'borde_entrada' not in e.gettags(item):
                            self.assertEqual(e.itemcget(item,'outline'),'')
                    self.assertEqual(e.entrada.get(),'Borrador')
                with patch.object(e,'winfo_width',return_value=360):e.clic(Mock(x=321))
                enviar.assert_called_once_with('Borrador')
                e.destroy()
        finally:root.destroy()

    def test_transicion_usa_el_panel_seleccionado_en_ambas_direcciones_y_separa_cache_color(self):
        with self.capri() as (c,_),patch('intro.Transformacion') as transformar:
            transformar.return_value.fotos=[]
            c.guardar('aspecto_pantalla','visor');c.guardar('color_interfaz','#689bff')
            c.guardar('modo_visual','personaje')
            ida=transformar.call_args.kwargs['panel'];self.assertFalse(transformar.call_args.kwargs['inversa'])
            self.assertEqual(ida.size,(1080,1014))
            self.assertIsNotNone(ida.crop((0,876,1080,1014)).getbbox())
            self.assertEqual(c.cache_morfosis[0][-2:],('visor','#689bff'))
            c.finalizar_transito();c.guardar('modo_visual','pantalla')
            vuelta=transformar.call_args.kwargs['panel'];self.assertTrue(transformar.call_args.kwargs['inversa'])
            self.assertEqual(ida.tobytes(),vuelta.tobytes())
            c.finalizar_transito();c.guardar('color_interfaz','#40d9e6')
            self.assertFalse(c.caches_morfosis)
            c.guardar('modo_visual','personaje');otro=transformar.call_args.kwargs['panel']
            self.assertNotEqual(ida.tobytes(),otro.tobytes())
            self.assertEqual(ida.crop((60,165,1020,795)).tobytes(),otro.crop((60,165,1020,795)).tobytes())
