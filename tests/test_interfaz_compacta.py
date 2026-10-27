import threading
import time
from unittest.mock import patch
from test_capri import PruebasTk
import app
from avatar import Avatar

class Compacta(PruebasTk):
    def test_dictado_y_streaming_completos_no_abren_historial(self):
        continuar=threading.Event()
        def respuesta(texto,modelo,al_texto,cancelar,origen):
            al_texto('Aquí está');continuar.wait(2)
            return 'Aquí está la respuesta completa.'
        with patch.object(app.IA,'conversar',side_effect=respuesta),patch.object(app.Voz,'parar'):
            capri=app.Capri(hotkeys=False)
            capri.root.withdraw();capri.cfg['voz']=False
            try:
                self.assertIsNone(capri.panel)
                self.assertEqual(len(capri.avatar.fotos),3)
                capri.micro.confianza_baja=False;capri.recibir_dictado('Capri, hablemos un rato')
                limite=time.monotonic()+2
                while not capri.stream_ticket and time.monotonic()<limite:capri.root.update();time.sleep(.01)
                self.assertIsNone(capri.panel);continuar.set()
                while capri.ocupada and time.monotonic()<limite:capri.root.update();time.sleep(.01)
                self.assertFalse(capri.ocupada);self.assertIsNone(capri.panel)
                self.assertEqual(capri.historial[-1],('Capri','Aquí está la respuesta completa.'))
                capri.abrir_chat();capri.panel.withdraw()
                self.assertEqual(capri.chat.get('1.0','end').count('Aquí está la respuesta completa.'),1)
            finally:continuar.set();capri.cerrar()

    def test_dictado_dudoso_se_revisa_en_panel_pequeno(self):
        with patch.object(app.Voz,'parar'):
            capri=app.Capri(hotkeys=False)
            capri.root.withdraw()
            try:
                capri.micro.confianza_baja=True;capri.recibir_dictado('Capri abre Spotify')
                self.assertIsNone(capri.panel)
                self.assertEqual(capri.dialogo.entrada.get(),'abre Spotify')
                self.assertEqual(capri.historial,[])
            finally:capri.cerrar()

    def test_listo_solo_despues_de_evento_actual_de_entrada_preparada(self):
        with patch.object(app.Voz,'parar'):
            capri=app.Capri(hotkeys=False)
            capri.root.withdraw()
            try:
                capri.activacion_ticket=10
                capri.eventos.put(('activacion_lista',9));capri.poll();self.assertFalse(capri.activacion_lista)
                capri.eventos.put(('activacion_lista',10));capri.poll();self.assertTrue(capri.activacion_lista)
                capri.detener_activacion();self.assertFalse(capri.activacion_lista)
            finally:capri.cerrar()

    def test_tres_estados_situacionales_sin_saltos_de_pose(self):
        avatar=Avatar.__new__(Avatar);avatar.sonrisa_hasta=0
        self.assertEqual(avatar.indice(ahora=100),0)
        self.assertIn(avatar.indice(hablando=True,ahora=101),[0,1])
        self.assertEqual(avatar.indice(feliz=True,ahora=101.1),2)
        self.assertEqual(avatar.indice(ahora=101.2),0)
