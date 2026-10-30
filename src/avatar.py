"""Ilustración original intacta y tres estados de boca, con efectos de pantalla."""
import random
import time
from PIL import Image,ImageTk,ImageDraw,ImageChops,ImageFilter,ImageEnhance,ImageOps
from fuentes import FAMILIA

BOCA=(111,64,142,89)

def estados_originales(ruta,bocas):
    with Image.open(ruta) as im:base=im.convert('RGBA')
    caja_boca=tuple(round(v*(base.width/225 if j%2==0 else base.height/350)) for j,v in enumerate(BOCA))
    estados=[base.copy()]
    with Image.open(bocas) as atlas:
        w,h=atlas.size
        for i in (1,2):
            boca=atlas.crop((i*w//3,0,(i+1)*w//3,h)).convert('RGBA')
            caja=boca.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
            if caja:boca=boca.crop(caja)
            boca=boca.resize((caja_boca[2]-caja_boca[0],caja_boca[3]-caja_boca[1]),Image.Resampling.LANCZOS)
            # Recortar la pintura al plano neutro de la boca: ni siquiera los
            # píxeles de antialias pueden invadir piel verde, ojos o contornos.
            alfa=boca.getchannel('A');region=base.crop(caja_boca)
            for y in range(boca.height):
                for x in range(boca.width):
                    r,g,b,_=region.getpixel((x,y))
                    if max(r,g,b)-min(r,g,b)>45:alfa.putpixel((x,y),0)
            boca.putalpha(alfa)
            estado=base.copy()
            # Retirar la boca original antes de pintar la expresión nueva.
            # El plano oscuro local conserva la piel y el contorno coloreado.
            oscuros=[region.getpixel((x,y))[:3] for y in range(region.height) for x in range(region.width)
                     if max(region.getpixel((x,y))[:3])<45 and max(region.getpixel((x,y))[:3])-min(region.getpixel((x,y))[:3])<=15]
            fondo=tuple(sorted(c[j] for c in oscuros)[len(oscuros)//2] for j in range(3)) if oscuros else (8,8,12)
            for y in range(region.height):
                for x in range(region.width):
                    r,g,b,a=region.getpixel((x,y))
                    if max(r,g,b)-min(r,g,b)<=45 and max(r,g,b)>45:
                        estado.putpixel((caja_boca[0]+x,caja_boca[1]+y),(*fondo,a))
            estado.alpha_composite(boca,caja_boca[:2]);estados.append(estado)
    return estados

def vista_pantalla(estado,tamano=(320,210),fase=0):
    # Recorte de cámara, no redibujo: la misma silueta y pose en los tres estados.
    vista=estado.crop((0,0,estado.width,round(estado.height*148/350))).resize(tamano,Image.Resampling.LANCZOS)
    # Óptica y señal de cámara: resolución algo menor, grano fino y barrido.
    reducido=(max(1,round(tamano[0]*.78)),max(1,round(tamano[1]*.82)))
    vista=vista.resize(reducido,Image.Resampling.BILINEAR).resize(tamano,Image.Resampling.BILINEAR)
    vista=ImageEnhance.Color(vista).enhance(.92)
    rng=random.Random(431+fase)
    ruido=Image.frombytes('L',(320,210),rng.randbytes(320*210)).resize(tamano,Image.Resampling.NEAREST)
    grano=ImageOps.colorize(ruido,'#101c23','#ddd4ca').convert('RGBA');grano.putalpha(ruido.point(lambda a:7+a//20))
    vista=Image.alpha_composite(vista,grano)
    lineas=Image.new('RGBA',vista.size);d=ImageDraw.Draw(lineas)
    paso=max(3,round(tamano[1]/70))
    for y in range(fase%2,vista.height,paso):d.line((0,y,vista.width,y),fill=(2,9,17,49))
    borde=Image.radial_gradient('L').resize(tamano).point(lambda a:round(a*.19))
    vineta=Image.new('RGBA',tamano,(1,7,12));vineta.putalpha(borde)
    return Image.alpha_composite(Image.alpha_composite(vista,lineas),vineta)

def fragmentar(vista,variante,transparente=False):
    """Desgarro de señal, sin envolver píxeles en los bordes ni pintar un fondo."""
    rng=random.Random(70+variante*37);w,h=vista.size;salida=vista.copy()
    fuerza=(.045,.075,.12,.055,.095,.14)[variante%6]
    for i in range(13):
        y=rng.randrange(max(1,h-3));fin=min(h,y+max(1,round(h*rng.uniform(.006,.047))))
        dx=round(w*rng.uniform(-fuerza,fuerza))
        banda=vista.crop((0,y,w,fin))
        salida.paste((0,0,0,0),(0,y,w,fin))
        # Franjas cromáticas derivadas del cuerpo, no líneas sobre el escritorio.
        for desplazamiento,color in ((-max(2,w//60),'#5c32f5'),(max(2,w//75),'#24d4a1')):
            fantasma=Image.new('RGBA',banda.size,color);fantasma.putalpha(banda.getchannel('A'))
            salida.alpha_composite(fantasma,(dx+desplazamiento,y))
        salida.alpha_composite(banda,(dx,y))
        if i%3==0:
            corte=max(1,round(h*.004));salida.paste((0,0,0,0),(0,y,w,min(fin,y+corte)))
    if transparente:
        # Tk usa color transparente: conservar alfa binario y margen vacío.
        salida.putalpha(salida.getchannel('A').point(lambda a:255 if a>=100 else 0))
    return salida


def interferencia(vista,variante):return fragmentar(vista,variante)

class Avatar:
    def __init__(self,ruta,bocas=None):
        self.fotos=[];self.glitches=[];self.estados=[];self.estados_hd=[];self.glitch_activo=False;self.vistas=[];self.escala=1
        self.proximo_glitch=time.monotonic()+random.uniform(3,6);self.glitch_hasta=0;self.sonrisa_hasta=0
        try:
            self.estados=estados_originales(ruta,bocas or ruta.with_name('capri-bocas-v2.png'))
            self.vistas=[vista_pantalla(estado) for estado in self.estados]
            hd=ruta.with_name('capri-base-hd-v1.png')
            if hd.exists():self.estados_hd=estados_originales(hd,bocas or ruta.with_name('capri-bocas-v2.png'))
            self.vista_maestra=vista_pantalla((self.estados_hd or self.estados)[0],(960,630))
            self.redimensionar(1)
        except (OSError,ValueError):pass

    def redimensionar(self,escala):
        self.escala=escala;tamaño=(round(320*escala),round(210*escala))
        vistas=[vista_pantalla(v,tamaño) for v in (self.estados_hd or self.estados)]
        self.fotos=[ImageTk.PhotoImage(v) for v in vistas]
        originales=self.estados_hd or self.estados
        self.senales=[[self.fotos[i]]+[ImageTk.PhotoImage(vista_pantalla(v,tamaño,fase)) for fase in (1,2)] for i,v in enumerate(originales)]
        self.glitches=[[ImageTk.PhotoImage(interferencia(v,i)) for i in range(6)] for v in vistas]

    def indice(self,hablando=False,feliz=False,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora
        if hablando:return (0,1,1,0,1,0)[int(ahora*7)%6]
        return 2 if feliz or ahora<self.sonrisa_hasta else 0

    def sonreir(self):self.sonrisa_hasta=time.monotonic()+1.8

    def imagen(self,hablando=False,glitch=True,ahora=None):
        ahora=time.monotonic() if ahora is None else ahora
        indice=self.indice(hablando,ahora=ahora)
        if glitch and ahora>=self.proximo_glitch:
            self.glitch_hasta=ahora+random.uniform(.22,.38)
            self.proximo_glitch=ahora+random.uniform(1.8,3.5) if hablando else ahora+random.uniform(4,8)
        self.glitch_activo=glitch and ahora<self.glitch_hasta
        return self.glitches[indice][int(ahora*28)%len(self.glitches[indice])] if self.glitch_activo else (self.senales[indice][int(ahora*8)%3] if glitch else self.fotos[indice])

def dibujar_marco(c,fase,color,estado,nivel=0,glitch=False,escala=1):
    c.create_polygon(13,11,343,11,352,20,352,280,342,289,8,289,8,20,fill='#120b10',outline='#8e304a',width=1)
    c.create_line(23,43,339,43,fill='#502034')
    c.create_text(25,28,text='CAPRI',anchor='w',fill='#edf6f6',font=(FAMILIA,round(13*escala),'bold'))
    c.create_text(310,29,text=estado,anchor='e',fill=color,font=(FAMILIA,max(8,round(9*escala))))
    c.create_text(337,27,text='···',fill='#79909e',font=(FAMILIA,round(11*escala),'bold'))
    for x,y,sx,sy in [(16,51,1,1),(344,51,-1,1),(16,269,1,-1),(344,269,-1,-1)]:
        c.create_line(x,y,x+sx*28,y,fill=color,width=2)
        c.create_line(x,y,x,y+sy*18,fill=color,width=2)
    c.create_line(23,281,336,281,fill='#502034')
    if glitch:
        c.create_line(17,49,135,49,fill='#ff3c72',width=3)
        c.create_line(170,271,337,271,fill='#ff96ab',width=3)
