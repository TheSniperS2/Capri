"""Reproducción de despedida ilustrada; no abre ni graba ninguna cámara."""
from PIL import Image,ImageTk,ImageOps,ImageFilter,ImageEnhance,ImageChops
import io
from fuentes import FAMILIA

TRASLADO=1.1


def aspecto_grabacion(cuadro,tamano):
    """Señal de cámara SD cacheada; el atlas original permanece intacto."""
    im=ImageOps.fit(cuadro.convert('RGB'),(360,270),Image.Resampling.LANCZOS)
    im=ImageEnhance.Color(im).enhance(.78)
    im=ImageEnhance.Contrast(im).enhance(.90)
    rojo,verde,azul=im.split()
    im=Image.merge('RGB',(ImageChops.offset(rojo,1,0),verde,ImageChops.offset(azul,-1,0)))
    buffer=io.BytesIO();im.save(buffer,format='JPEG',quality=56,subsampling=2)
    buffer.seek(0)
    with Image.open(buffer) as comprimida:im=comprimida.convert('RGB').resize(tamano,Image.Resampling.BILINEAR)
    return im.filter(ImageFilter.GaussianBlur(.32)).convert('RGBA')


class GrabacionDespedida:
    def __init__(self,ruta,ancho_pantalla,alto_pantalla):
        self.w=min(620,max(180,ancho_pantalla-64),int((alto_pantalla-140)*4/3))
        self.h=round(self.w*3/4)
        self.fotos=[];self.indice=0
        with Image.open(ruta) as fuente:
            hoja=fuente.convert('RGBA');iw,ih=hoja.size
            for fila,col in ((0,0),(0,1),(1,0),(1,1)):
                cuadro=hoja.crop((col*iw//2,fila*ih//2,(col+1)*iw//2,(fila+1)*ih//2))
                cuadro=aspecto_grabacion(cuadro,(self.w,self.h))
                if not self.fotos:self.imagen=cuadro
                self.fotos.append(ImageTk.PhotoImage(cuadro))
        self.foto=self.fotos[0]
        import numpy as np
        self.grano=[]
        for indice in range(6):
            rng=np.random.default_rng(402+indice);capa=np.empty((self.h,self.w,4),dtype=np.uint8)
            color=np.where(rng.integers(0,2,(self.h,self.w)),230,12).astype(np.uint8)
            capa[:,:,:3]=color[:,:,None]
            capa[:,:,3]=rng.integers(4,19,(self.h,self.w),dtype=np.uint8)+np.where(np.arange(self.h)%3==0,5,0).astype(np.uint8)[:,None]
            self.grano.append(ImageTk.PhotoImage(Image.fromarray(capa)))
        self.centro=(ancho_pantalla/2,alto_pantalla/2-20)
        self.luz=(ancho_pantalla*.5,alto_pantalla*.09)

    def expresion(self,tiempo,hablando=False,boca=False,finalizada=False):
        if finalizada:return 3
        if hablando:return 2 if boca and int(tiempo*9)%3 else 1
        if tiempo>1.35:return 3
        return 0 if tiempo<.55 else 1

    def dibujar(self,c,tiempo,frase,hablando=False,boca=False,finalizada=False,fondo=None):
        x,y=self.centro;l=x-self.w/2;t=y-self.h/2;r=l+self.w;b=t+self.h
        c.delete('all')
        if fondo is not None:
            from despedida import estrella
            c.create_image(0,0,image=fondo,anchor='nw',tags='cielo_despedida')
            estrella(c,*self.luz,.78*.28)
        c.create_rectangle(l-2,t-27,r+2,b+43,fill='#0b1018',outline='#596572',tags='marco_grabacion')
        self.indice=self.expresion(tiempo,hablando,boca,finalizada)
        c.create_image(x,y,image=self.fotos[self.indice],tags='rostro_despedida')
        c.create_image(x,y,image=self.grano[int(max(0,tiempo)*12)%len(self.grano)],tags='grano_grabacion')
        # Un visor de reproducción discreto, separado del dibujo y de sus colores.
        c.create_polygon(l+12,t-20,l+12,t-10,l+20,t-15,fill='#ccd5dc',outline='',tags='reproduccion_despedida')
        c.create_text(l+28,t-15,text='CAPRI',anchor='w',fill='#ccd5dc',font=(FAMILIA,9),tags='reproduccion_despedida')
        c.create_text(r-12,t-15,text=f'00:{min(59,int(max(0,tiempo))):02}',anchor='e',fill='#a9b7c2',font=(FAMILIA,9),tags='reproduccion_despedida')
        for px,py,sx,sy in ((l+12,t+12,1,1),(r-12,t+12,-1,1),(l+12,b-12,1,-1),(r-12,b-12,-1,-1)):
            c.create_line(px,py+sy*13,px,py,px+sx*13,py,fill='#d0d7dc',width=1,tags='visor_despedida')
        c.create_text(x,b+21,text=frase,fill='#eef3f5',font=(FAMILIA,15),width=self.w-24,tags='frase_despedida')
