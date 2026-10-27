"""Ilustración original intacta y tres estados de boca, con efectos de pantalla."""
import random
import time
from PIL import Image,ImageTk,ImageDraw

BOCA=(103,64,141,86)

def estados_originales(ruta,bocas):
    with Image.open(ruta) as im:base=im.convert('RGBA')
    estados=[base.copy()]
    with Image.open(bocas) as atlas:
        w,h=atlas.size
        for i in (1,2):
            boca=atlas.crop((i*w//3,0,(i+1)*w//3,h)).convert('RGBA')
            caja=boca.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
            if caja:boca=boca.crop(caja)
            boca=boca.resize((BOCA[2]-BOCA[0],BOCA[3]-BOCA[1]),Image.Resampling.LANCZOS)
            estado=base.copy();estado.alpha_composite(boca,BOCA[:2]);estados.append(estado)
    return estados

def vista_pantalla(estado):
    # Recorte de cámara, no redibujo: la misma silueta y pose en los tres estados.
    vista=estado.crop((0,0,225,148)).resize((320,210),Image.Resampling.BILINEAR)
    lineas=Image.new('RGBA',vista.size);d=ImageDraw.Draw(lineas)
    for y in range(1,vista.height,3):d.line((0,y,vista.width,y),fill=(0,5,14,56))
    return Image.alpha_composite(vista,lineas)

def interferencia(vista,variante):
    rng=random.Random(70+variante);salida=vista.copy();d=ImageDraw.Draw(salida)
    for y,h,dx in [(34,9,8),(87,15,-11),(151,6,12)]:
        y+=rng.randint(-12,12);banda=vista.crop((0,y,320,y+h));salida.paste(banda,(dx,y))
        d.line((max(0,dx),y,290,y),fill=(62,227,223,180),width=2)
        d.line((27,y+h,314,y+h),fill=(235,39,93,155),width=1)
    return salida

class Avatar:
    def __init__(self,ruta,bocas=None):
        self.fotos=[];self.glitches=[];self.estados=[];self.glitch_activo=False
        self.proximo_glitch=time.monotonic()+random.uniform(3,6);self.glitch_hasta=0;self.sonrisa_hasta=0
        try:
            self.estados=estados_originales(ruta,bocas or ruta.with_name('capri-bocas-v2.png'))
            for estado in self.estados:
                vista=vista_pantalla(estado);self.fotos.append(ImageTk.PhotoImage(vista))
                self.glitches.append([ImageTk.PhotoImage(interferencia(vista,i)) for i in range(2)])
        except (OSError,ValueError):pass

    def indice(self,hablando=False,feliz=False,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora
        if hablando:return (0,1,1,0,1,0)[int(ahora*7)%6]
        return 2 if feliz or ahora<self.sonrisa_hasta else 0

    def sonreir(self):self.sonrisa_hasta=time.monotonic()+1.8

    def imagen(self,hablando=False,glitch=True,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora
        indice=self.indice(hablando,ahora=ahora)
        if glitch and ahora>=self.proximo_glitch:
            self.glitch_hasta=ahora+.16
            self.proximo_glitch=ahora+random.uniform(1.8,3.5) if hablando else ahora+random.uniform(4,8)
        self.glitch_activo=glitch and ahora<self.glitch_hasta
        return self.glitches[indice][int(ahora*18)%2] if self.glitch_activo else self.fotos[indice]

def dibujar_marco(c,fase,color,estado,nivel=0,glitch=False):
    c.create_polygon(13,11,343,11,352,20,352,284,342,293,8,293,8,20,fill='#080d17',outline='#45616d',width=1)
    c.create_line(23,43,339,43,fill='#273a49')
    c.create_text(25,28,text='CAPRI',anchor='w',fill='#edf6f6',font=('Segoe UI',11,'bold'))
    c.create_text(92,29,text='// ENLACE PERSONAL',anchor='w',fill='#79909e',font=('Consolas',8))
    c.create_oval(327,24,333,30,fill=color,outline='')
    for x,y,sx,sy in [(16,51,1,1),(344,51,-1,1),(16,269,1,-1),(344,269,-1,-1)]:
        c.create_line(x,y,x+sx*28,y,fill=color,width=2)
        c.create_line(x,y,x,y+sy*18,fill=color,width=2)
    c.create_text(24,282,text=estado[:39],anchor='w',fill=color,font=('Consolas',8))
    if glitch:
        c.create_line(17,49,135,49,fill='#ff3c72',width=3)
        c.create_line(170,271,337,271,fill='#6df4e8',width=3)
