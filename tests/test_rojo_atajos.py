import json
from PIL import Image
from unittest.mock import Mock,patch
from test_capri import PruebasTk
import test_companera_control as fixtures
from companera import con_sombra
from voz import tecla_virtual

class RojoYPreferencias(PruebasTk):
    capri=fixtures.ModoPersonaje.capri

    def test_guardar_aspecto_no_pisa_modelos_microfono_o_reconocimiento_guardados(self):
        with self.capri() as (c,carpeta):
            original={'modelo':'qwen-elegido','ia':True,'microfono':{'nombre':'USB','api':'Windows WASAPI'},
                      'reconocimiento':'mixto','modelo_whisper':'small','voz_perfil':'capri_latina'}
            archivo=carpeta/'ajustes.json';archivo.write_text(json.dumps(original),encoding='utf8')
            c.cfg.update(modelo='valor-antiguo',modelo_whisper='base',microfono=None)
            c.guardar('halo_personaje','rojo')
            datos=json.loads(archivo.read_text(encoding='utf8'))
            for k,v in original.items():self.assertEqual(datos[k],v)

    def test_marcos_propios_y_tecla_configurable_sin_cambiar_entrada(self):
        with self.capri() as (c,carpeta):
            c.configurar();c.ajustes.update_idletasks()
            self.assertTrue(c.ajustes.overrideredirect())
            self.assertTrue(c.marco_ajustes.canvas.find_withtag('chrome'))
            anterior=c.atajo=Mock()
            with patch('app.Atajo') as registro:
                c.guardar('tecla_hablar','F10')
                anterior.cerrar.assert_called_once()
                self.assertEqual(registro.call_args.args[2],'F10')
            self.assertEqual(json.loads((carpeta/'ajustes.json').read_text())['tecla_hablar'],'F10')
            self.assertEqual(tecla_virtual('F10'),0x79)
            self.assertEqual(tecla_virtual('desconocida'),0x77)
            c.abrir_chat();c.panel.update_idletasks()
            self.assertTrue(c.panel.overrideredirect());self.assertTrue(c.marco_chat.canvas.find_withtag('chrome'))

    def test_menu_voz_no_incluye_interrumpir(self):
        with self.capri() as (c,_):
            c.companera.redimensionar(1)
            c.abrir_menu_radial(Mock(x_root=500,y_root=400))
            opciones=next(a for n,a in c.radial.opciones if n=='Voz')
            self.assertNotIn('Interrumpir',[n for n,a in opciones])

    def test_sombra_viaja_en_mismo_bitmap_antes_de_llegar(self):
        with self.capri() as (c,_):
            c.companera.redimensionar(1);base=c.companera.lienzos[0]
            compuesta=con_sombra(base,'rojo')
            nuevos=sum(1 for a,b in zip(base.getchannel('A').get_flattened_data(),compuesta.getchannel('A').get_flattened_data()) if not a and b)
            self.assertGreater(nuevos,20)
            self.assertEqual(con_sombra(base,'ninguno').tobytes(),base.tobytes())
