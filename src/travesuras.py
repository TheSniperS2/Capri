"""Juegos ligeros: solo eventos visuales o aperturas básicas autorizadas."""
import random
import time


class Travesuras:
    def __init__(self,reloj=None):
        self.reloj=reloj or time.monotonic;self.proxima=self.reloj()+100;self.ultima_app=-1000
        self.atrapame=False;self.aciertos=0

    def elegir(self,permitir_apps=False):
        opciones=['asomar','salto','salto']
        if permitir_apps and self.reloj()-self.ultima_app>=300:opciones+=['pestana','carpeta']
        evento=random.choice(opciones)
        if evento in ('pestana','carpeta'):self.ultima_app=self.reloj()
        return evento

    def tick(self,activo,ocupada,permitir_apps=False):
        if not activo or ocupada or self.atrapame or self.reloj()<self.proxima:return None
        self.proxima=self.reloj()+random.uniform(100,180)
        return self.elegir(permitir_apps)

    def comenzar(self):self.atrapame=True;self.aciertos=0

    def tocar(self):
        if not self.atrapame:return None
        self.aciertos+=1
        if self.aciertos>=3:self.atrapame=False;return 'ganaste'
        return 'escapar'
