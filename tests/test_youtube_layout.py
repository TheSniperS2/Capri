from types import SimpleNamespace
from unittest.mock import patch
import unittest
from tkinter.font import Font
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tema_ui import tk
from idiomas import activar,idioma_actual
import app


class YouTubeLayout(unittest.TestCase):
    def test_acciones_completas_con_ventana_reducida_y_dpi_alto(self):
        idioma=idioma_actual();activar('es')
        try:
            for escala in (1.333,2.,2.6):
                root=tk.Tk();root.withdraw();anterior=root.tk.call('tk','scaling');root.tk.call('tk','scaling',escala)
                original=tk.Toplevel;creadas=[]
                class Invisible(original):
                    def __init__(self,*a,**kw):
                        super().__init__(*a,**kw);self.attributes('-alpha',0);self.attributes('-disabled',True);creadas.append(self)
                try:
                    with patch.object(tk,'Toplevel',Invisible),patch('puente_opera.iniciar',return_value=SimpleNamespace(error='',conectado=lambda:False)):
                        app.Capri.conectar_opera(SimpleNamespace(root=root));root.update()
                    ventana=creadas[0];ventana.attributes('-topmost',False)
                    def hijos(w):
                        for child in w.winfo_children():yield child;yield from hijos(child)
                    widgets=list(hijos(ventana));botones=[w for w in widgets if w.__class__.__name__=='BotonCyber']
                    self.assertEqual(len(botones),3)
                    cuerpo=ventana.winfo_children()[0].winfo_children()[0]
                    instrucciones=next(w for w in widgets if w.winfo_name()=='instrucciones')
                    for ancho,alto in ((740,620),(640,430)):
                        ventana.geometry(f'{ancho}x{alto}');root.update();root.update_idletasks()
                        for boton in botones:
                            self.assertGreaterEqual(boton.winfo_height(),Font(root=boton,font=boton.fuente).metrics('linespace')+12)
                            self.assertEqual(boton.winfo_height(),boton.winfo_reqheight())
                            self.assertLessEqual(boton.winfo_rooty()+boton.winfo_height(),cuerpo.winfo_rooty()+cuerpo.winfo_height())
                            self.assertLessEqual(boton.winfo_rootx()+boton.winfo_width(),cuerpo.winfo_rootx()+cuerpo.winfo_width())
                        self.assertGreater(instrucciones.winfo_height(),10)
                finally:
                    root.tk.call('tk','scaling',anterior);root.destroy()
        finally:activar(idioma)
