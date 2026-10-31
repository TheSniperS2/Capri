"""Reproducción de despedida ilustrada; no abre ni graba ninguna cámara."""
from PIL import Image,ImageTk,ImageOps,ImageEnhance,ImageDraw,ImageFont,ImageFilter
import math
import queue
import threading
from pathlib import Path
from fuentes import FAMILIA

TRASLADO=1.1


def aspecto_grabacion(cuadro,tamano):
    """Encuadre nítido: la textura de cámara vive en una capa independiente."""
    im=ImageOps.fit(cuadro.convert('RGB'),tamano,Image.Resampling.LANCZOS)
    # La cinta conserva el detalle de luminancia y deja que el color se
    # extienda levemente: señal analógica, sin ampliar una imagen SD borrosa.
    im=ImageEnhance.Color(im).enhance(.90)
    im=ImageEnhance.Contrast(im).enhance(.94)
    y,cb,cr=im.convert('YCbCr').split()
    radio=max(.5,min(1.4,max(tamano)/1500))
    im=Image.merge('YCbCr',(y,cb.filter(ImageFilter.GaussianBlur(radio)),cr.filter(ImageFilter.GaussianBlur(radio)))).convert('RGB')
    return im.convert('RGBA')


def optica_grabacion(tamano):
    """Velo cálido, viñeta y trama de vídeo; sin reducir detalle del retrato."""
    import numpy as np
    w,h=tamano;y,x=np.ogrid[:h,:w]
    radio=np.sqrt(((x-w*.5)/(w*.68))**2+((y-h*.48)/(h*.75))**2)
    borde=np.clip((radio-.18)/.82,0,1)
    capa=np.empty((h,w,4),dtype=np.uint8)
    for canal,(centro,extremo) in enumerate(((181,8),(166,14),(139,22))):
        capa[:,:,canal]=np.rint(centro+(extremo-centro)*borde)
    capa[:,:,3]=np.rint(20+82*borde**1.8+np.where(y%3==0,9,0))
    im=Image.fromarray(capa);d=ImageDraw.Draw(im)
    margen=max(2,round(min(w,h)*.006));ancho=max(2,round(min(w,h)*.006))
    d.rounded_rectangle((margen,margen,w-margen-1,h-margen-1),radius=max(6,round(min(w,h)*.018)),
                        outline=(5,9,15,215),width=ancho)
    return im


class GrabacionDespedida:
    def __init__(self,ruta,ancho_pantalla,alto_pantalla):
        self.w=ancho_pantalla;self.h=alto_pantalla
        self.margen_sensor=max(2,round(max(self.w,self.h)/640))
        self.fotos=[];self.indice=0
        with Image.open(ruta) as fuente:
            hoja=fuente.convert('RGBA');iw,ih=hoja.size
            for fila,col in ((0,0),(0,1),(1,0),(1,1)):
                cuadro=hoja.crop((col*iw//2,fila*ih//2,(col+1)*iw//2,(fila+1)*ih//2))
                cuadro=aspecto_grabacion(cuadro,(self.w,self.h))
                if not self.fotos:self.imagen=cuadro
                m=self.margen_sensor
                # Margen oscuro de cinta: no volver a remuestrear todo el
                # retrato sólo para obtener unos píxeles de protección.
                self.fotos.append(ImageTk.PhotoImage(ImageOps.expand(cuadro.convert('RGB'),border=m,fill='#080b10')))
        self.foto=self.fotos[0]
        self.optica_pil=optica_grabacion((self.w,self.h))
        self.optica=ImageTk.PhotoImage(self.optica_pil)
        import numpy as np
        self.grano=[]
        for indice in range(6):
            rng=np.random.default_rng(402+indice);capa=np.empty((self.h,self.w,4),dtype=np.uint8)
            color=np.where(rng.integers(0,2,(self.h,self.w)),230,12).astype(np.uint8)
            capa[:,:,:3]=color[:,:,None]
            # Evitar píxeles alfa cero dispersos: Tk convierte cada isla
            # transparente en una región y el ruido aleatorio puede bloquearlo.
            capa[:,:,3]=rng.integers(4,14,(self.h,self.w),dtype=np.uint8)
            self.grano.append(ImageTk.PhotoImage(Image.fromarray(capa)))
        self.centro=(ancho_pantalla/2,alto_pantalla/2)
        self.luz=(ancho_pantalla*.5,alto_pantalla*.09)
        self.hud=None;self.hud_frase=None

    def preparar_hud(self,frase):
        if self.hud_frase==frase:return
        capa=Image.new('RGBA',(self.w,self.h));d=ImageDraw.Draw(capa)
        margen=max(18,round(min(self.w,self.h)*.035))
        def fuente(tamano):
            ruta=Path(__file__).parent/'assets/fonts/ChakraPetch-Regular.ttf'
            if not ruta.exists():ruta=Path(__file__).parents[1]/'assets/fonts/ChakraPetch-Regular.ttf'
            from idiomas import idioma_actual
            if idioma_actual()=='ja':ruta=Path('YuGothR.ttc')
            try:return ImageFont.truetype(str(ruta),tamano)
            except OSError:return ImageFont.load_default()
        pequena=fuente(max(12,round(self.h*.019)))
        subtitulo=fuente(max(18,round(self.h*.032)))
        d.polygon(((margen,margen),(margen,margen+10),(margen+8,margen+5)),fill='#d0d7dc')
        d.text((margen+18,margen-3),'CAPRI',font=pequena,fill=(208,215,220,170))
        for x,y,sx,sy in ((margen,margen*2+25,1,1),(self.w-margen,margen*2+25,-1,1),
                          (margen,self.h-margen*3,1,-1),(self.w-margen,self.h-margen*3,-1,-1)):
            d.line((x,y+sy*18,x,y,x+sx*18,y),fill=(215,224,229,125),width=1)
        caja=d.textbbox((0,0),frase,font=subtitulo);ancho=caja[2]-caja[0]
        # Ajustar también frases japonesas y pantallas estrechas, sin recortarlas.
        if ancho>self.w-2*margen:
            subtitulo=fuente(max(10,round(subtitulo.size*(self.w-2*margen)/ancho)))
        y=self.h-margen-10
        d.rectangle((0,y-round(self.h*.05),self.w,self.h),fill=(4,8,14,175))
        d.text((self.w/2,y),frase,font=subtitulo,anchor='ms',fill='#eef3f5',stroke_width=1,stroke_fill='#10151d')
        self.hud_pil=capa;self.hud=ImageTk.PhotoImage(capa);self.hud_frase=frase

    def fotograma_final(self,frase):
        self.preparar_hud(frase)
        m=self.margen_sensor
        im=ImageTk.getimage(self.fotos[3]).crop((m,m,m+self.w,m+self.h)).convert('RGBA')
        im=Image.alpha_composite(im,self.optica_pil)
        im=Image.alpha_composite(im,ImageTk.getimage(self.grano[0]))
        return Image.alpha_composite(im,self.hud_pil)

    def expresion(self,tiempo,hablando=False,boca=False,finalizada=False):
        if finalizada:return 3
        if hablando:return 2 if boca and int(tiempo*9)%3 else 1
        if tiempo>1.35:return 3
        return 0 if tiempo<.55 else 1

    def dibujar(self,c,tiempo,frase,hablando=False,boca=False,finalizada=False,fondo=None):
        x,y=self.centro
        c.delete('all')
        if fondo is not None:
            from despedida import estrella
            c.create_image(0,0,image=fondo,anchor='nw',tags='cielo_despedida')
            estrella(c,*self.luz,.78*.28)
        self.indice=self.expresion(tiempo,hablando,boca,finalizada)
        dx,dy=self.oscilacion(tiempo)
        c.create_image(x+dx,y+dy,image=self.fotos[self.indice],tags='rostro_despedida')
        c.create_image(x,y,image=self.optica,tags='optica_grabacion')
        c.create_image(x,y,image=self.grano[int(max(0,tiempo)*12)%len(self.grano)],tags='grano_grabacion')
        self.preparar_hud(frase)
        c.create_image(0,0,image=self.hud,anchor='nw',tags=('visor_despedida','frase_despedida'))
        margen=max(18,round(min(self.w,self.h)*.035))
        c.create_text(self.w-margen,margen+5,text=f'00:{min(59,int(max(0,tiempo))):02}',anchor='e',fill='#a9b7c2',font=(FAMILIA,10),tags='reproduccion_despedida')
        if int(max(0,tiempo)*2)%2==0:
            c.create_oval(self.w-margen-98,margen+1,self.w-margen-92,margen+7,
                          fill='#d86c68',outline='',tags='indicador_cinta')
        c.create_text(self.w-margen-84,margen+5,text='REC',anchor='w',fill='#c4b6aa',font=(FAMILIA,9),tags='indicador_cinta')

    def oscilacion(self,tiempo):
        m=self.margen_sensor
        return m*.38*math.sin(tiempo*3.7)+.18*math.sin(tiempo*13),m*.24*math.sin(tiempo*2.6)


class ContraccionCamara:
    """La señal completa se estrecha hasta el mismo contorno de la mano.

    El hilo sólo maneja Pillow; Tk consume imágenes en una cola acotada.
    No hay teselas separadas ni un cambio de sprite al empezar la contracción.
    """
    CUADROS=49

    def __init__(self,fotograma,mano,ancho,alto):
        self.ancho=ancho;self.alto=alto;self.cola=queue.Queue(maxsize=6)
        self.cancelar=threading.Event();self.pendiente=None;self.indice=-1
        self.foto=ImageTk.PhotoImage(fotograma);self.esquina=(0,0)
        perfil=self.perfil(mano,alto,180)
        self.worker=threading.Thread(target=self.preparar,args=(self.cola,self.cancelar,fotograma.convert('RGB'),perfil),daemon=True,name='CapriCamaraMano')
        self.worker.start()

    @staticmethod
    def perfil(mano,alto,bandas):
        arriba=min(y for x,y in mano);perfil=[]
        for i in range(bandas+1):
            y=arriba+(alto-arriba)*i/bandas
            cruces=[]
            for (ax,ay),(bx,by) in zip(mano,mano[1:]+mano[:1]):
                if min(ay,by)<=y<=max(ay,by) and abs(by-ay)>.0001:
                    cruces.append(ax+(bx-ax)*(y-ay)/(by-ay))
            if cruces:perfil.append((min(cruces),max(cruces),y))
            else:
                x=min(mano,key=lambda p:abs(p[1]-y))[0];perfil.append((x,x,y))
        return perfil

    @staticmethod
    def renderizar(original,perfil,q):
        from intro import suave
        from despedida import COLOR_MANO
        w,h=original.size;t=suave(q);n=len(perfil)-1
        bordes=[(l*t,(1-t)*w+r*t,(1-t)*h*i/n+y*t) for i,(l,r,y) in enumerate(perfil)]
        izquierda=max(0,math.floor(min(l for l,r,y in bordes)));derecha=min(w,math.ceil(max(r for l,r,y in bordes)))
        arriba=max(0,math.floor(bordes[0][2]));abajo=h
        tam=(max(1,derecha-izquierda),max(1,abajo-arriba));malla=[]
        # Cada banda de la grabación conserva sus píxeles mientras sus dos
        # bordes convergen; la máscara continua elimina juntas y escalones.
        for i,((l0,r0,y0),(l1,r1,y1)) in enumerate(zip(bordes,bordes[1:])):
            a=max(arriba,round(y0));b=min(abajo,round(y1))
            if b<=a:continue
            def origen(x,l,r):return (x-l)*w/max(.1,r-l)
            malla.append(((0,a-arriba,tam[0],b-arriba),
                          (origen(izquierda,l0,r0),h*i/n,origen(izquierda,l1,r1),h*(i+1)/n,
                           origen(derecha,l1,r1),h*(i+1)/n,origen(derecha,l0,r0),h*i/n)))
        im=original.transform(tam,Image.Transform.MESH,malla,Image.Resampling.BILINEAR)
        rojo=suave((q-.18)/.76)
        if rojo:im=Image.blend(im,Image.new('RGB',tam,COLOR_MANO),rojo)
        mascara=Image.new('L',(tam[0]*2,tam[1]*2));d=ImageDraw.Draw(mascara)
        puntos=[((l-izquierda)*2,(y-arriba)*2) for l,r,y in bordes]
        puntos += [((r-izquierda)*2,(y-arriba)*2) for l,r,y in reversed(bordes)]
        d.polygon(puntos,fill=255)
        im.putalpha(mascara.resize(tam,Image.Resampling.LANCZOS))
        return im,(izquierda,arriba)

    @staticmethod
    def preparar(cola,cancelar,original,perfil):
        # Más resolución mientras se distingue el retrato, menos al estrecharse
        # y teñirse de rojo. Las tres fuentes se reutilizan, sin JPEG ni desenfoque.
        w,h=original.size;fuentes={}
        for i in range(1,ContraccionCamara.CUADROS):
            if cancelar.is_set():return
            q=i/(ContraccionCamara.CUADROS-1);limite=1280 if q<.3 else (960 if q<.65 else 800)
            escala=min(1,limite/max(w,h))
            if limite not in fuentes:
                trabajo=original.resize((max(1,round(w*escala)),max(1,round(h*escala))),Image.Resampling.LANCZOS)
                fuentes[limite]=(trabajo,[(l*escala,r*escala,y*escala) for l,r,y in perfil])
            trabajo,contorno=fuentes[limite]
            im,esquina=ContraccionCamara.renderizar(trabajo,contorno,q)
            izquierda,arriba=(round(v/escala) for v in esquina)
            ancho=min(w-izquierda,max(1,round(im.width/escala)))
            im=im.resize((ancho,h-arriba),Image.Resampling.BILINEAR)
            esquina=(izquierda,arriba)
            while not cancelar.is_set():
                try:cola.put((i,im,esquina),timeout=.05);break
                except queue.Full:pass

    def dibujar(self,c,q):
        objetivo=round(max(0,min(1,q))*(self.CUADROS-1));ultimo=None
        while True:
            dato=self.pendiente;self.pendiente=None
            if dato is None:
                try:dato=self.cola.get_nowait()
                except queue.Empty:break
            if dato[0]>objetivo:self.pendiente=dato;break
            ultimo=dato
        if ultimo is not None:
            self.indice,im,self.esquina=ultimo;self.foto=ImageTk.PhotoImage(im)
        c.create_image(*self.esquina,image=self.foto,anchor='nw',tags='camara_a_mano')

    def detener(self):self.cancelar.set()
