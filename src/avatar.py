"""Ilustración original intacta y tres estados de boca, con efectos de pantalla."""
import random
import time
from PIL import Image,ImageTk,ImageDraw,ImageChops,ImageFilter,ImageEnhance,ImageOps,ImageFont
from fuentes import FAMILIA

BOCA=(111,64,142,89)
from disenos_pantalla import DISENOS,normalizar as normalizar_diseno,superficie
ASPECTOS_PANTALLA={k:(nombre,'#ed6684','#120b10','#8e304a') for k,nombre in DISENOS.items()}

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

def vista_pantalla(estado,tamano=(320,210),fase=0,aspecto='original'):
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
    vista=Image.alpha_composite(Image.alpha_composite(vista,lineas),vineta)
    return vista

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

class LienzoRaster:
    """Rasteriza los mismos trazados del monitor, sin leer la pantalla."""
    def __init__(self,imagen,escala=1,dy=0):
        self.imagen=imagen;self.d=ImageDraw.Draw(imagen);self.s=escala;self.dy=dy
    def puntos(self,p):return [v*self.s+(self.dy if i%2 else 0) for i,v in enumerate(p)]
    def create_polygon(self,*p,**kw):
        pts=self.puntos(p);fill=kw.get('fill') or None;outline=kw.get('outline') or None
        ancho=max(1,round(kw.get('width',1)*self.s))
        if kw.get('smooth'):
            xs=pts[::2];ys=pts[1::2]
            self.d.rounded_rectangle((min(xs),min(ys),max(xs),max(ys)),radius=pts[0]-min(xs),fill=fill,outline=outline,width=ancho)
        else:self.d.polygon(list(zip(pts[::2],pts[1::2])),fill=fill,outline=outline,width=ancho)
    def create_rectangle(self,*p,**kw):self.d.rectangle(self.puntos(p),fill=kw.get('fill') or None,outline=kw.get('outline') or None,width=max(1,round(kw.get('width',1)*self.s)))
    def create_oval(self,*p,**kw):self.d.ellipse(self.puntos(p),fill=kw.get('fill') or None,outline=kw.get('outline') or None)
    def create_line(self,*p,**kw):self.d.line(self.puntos(p),fill=kw['fill'],width=max(1,round(kw.get('width',1)*self.s)),joint='curve')
    def create_text(self,x,y,**kw):
        from pathlib import Path
        from idiomas import ui,idioma_actual
        font=kw.get('font',(FAMILIA,12));size=max(1,round((abs(font[1]) if font[1]<0 else font[1]*4/3)*self.s))
        nombre='ChakraPetch-Bold.ttf' if 'bold' in font else 'ChakraPetch-Regular.ttf'
        ruta=Path(__file__).parent/'assets/fonts'/nombre
        if not ruta.exists():ruta=Path(__file__).parents[1]/'assets/fonts'/nombre
        if font[0]=='Consolas':ruta=Path('C:/Windows/Fonts/consola.ttf')
        if idioma_actual()=='ja':ruta=Path('C:/Windows/Fonts/YuGothB.ttc')
        try:fuente=ImageFont.truetype(str(ruta),size)
        except OSError:fuente=ImageFont.load_default(size=size)
        anchor={'w':'lm','e':'rm','center':'mm','nw':'lt'}.get(kw.get('anchor','center'),'mm')
        texto=ui(kw['text']) if kw.get('traducir',True) else kw['text']
        limite=float(kw.get('width',0))*self.s
        if limite>0:
            lineas=[]
            for parrafo in texto.split('\n'):
                linea=''
                for palabra in parrafo.split(' '):
                    candidata=(linea+' '+palabra).strip()
                    if linea and self.d.textlength(candidata,font=fuente)>limite:lineas.append(linea);linea=''
                    for ch in ((' ' if linea else '')+palabra):
                        if linea and self.d.textlength(linea+ch,font=fuente)>limite:lineas.append(linea.rstrip());linea=''
                        linea+=ch
                lineas.append(linea)
            if len(lineas)>1:
                paso=round(size*1.25);y0=y*self.s+self.dy
                if kw.get('anchor','center') not in ('nw','n','ne'):y0-=len(lineas)*paso/2
                for i,linea in enumerate(lineas):
                    x0=x*self.s
                    if kw.get('anchor')=='e':x0-=self.d.textlength(linea,font=fuente)
                    elif kw.get('anchor','center')=='center':x0-=self.d.textlength(linea,font=fuente)/2
                    self.d.text((x0,y0+i*paso),linea,font=fuente,fill=kw['fill'],anchor='lt')
                return
        self.d.text((x*self.s,y*self.s+self.dy),texto,font=fuente,fill=kw['fill'],anchor=anchor)


def panel_pantalla(vista,aspecto,escala=3,con_entrada=False,escala_avatar=1,texto_entrada='Di «Capri» o escribe…',placeholder=True):
    from disenos_pantalla import cabecera
    alto=292*escala+(46*escala/escala_avatar if con_entrada else 0)
    im=Image.new('RGBA',(round(360*escala),round(alto)))
    c=LienzoRaster(im,escala);superficie(c,aspecto,360,292);cabecera(c,aspecto)
    foto=vista.resize((round(320*escala),round(210*escala)),Image.Resampling.LANCZOS)
    im.alpha_composite(foto,(round(20*escala),round(55*escala)))
    if con_entrada:
        from tema_ui import color
        k=escala/escala_avatar;ancho=360*escala_avatar;dy=292*escala
        entrada=LienzoRaster(im,k,dy);superficie(entrada,aspecto,ancho,46,chat=True)
        entrada.create_line(16,20,23,23,16,26,fill=color('#ec3c62'),width=2)
        entrada.create_line(ancho-28,28,ancho-18,18,fill=color('#9d3b52'),width=1.5)
        entrada.create_line(ancho-26,18,ancho-18,18,ancho-18,26,fill=color('#9d3b52'),width=1.5)
        letras=Image.new('RGBA',im.size);texto=LienzoRaster(letras,k,dy)
        consola=normalizar_diseno(aspecto)=='terminal'
        texto.create_text(35,23,text=texto_entrada,anchor='w',fill=color('#768b96' if placeholder else '#edf5f4'),
                          font=('Consolas' if consola else FAMILIA,11 if consola else 12),traducir=False)
        from disenos_pantalla import ancho_entrada
        caja=(round(35*k),round(dy+4*k),round((35+ancho_entrada(aspecto,ancho))*k),round(dy+42*k))
        im.alpha_composite(letras.crop(caja),caja[:2])
    return im


def miniatura_pantalla(estado,aspecto):
    from tema_ui import color
    panel=panel_pantalla(vista_pantalla(estado,(640,420)),aspecto,escala=2)
    im=Image.new('RGBA',(160,156));im.alpha_composite(panel.resize((160,130),Image.Resampling.LANCZOS))
    superficie(LienzoRaster(im,160/360,dy=134),aspecto,360,46,chat=True)
    ImageDraw.Draw(im).text((16,140),'...',fill=color('#ff9eaf'))
    return im


class Avatar:
    def __init__(self,ruta,bocas=None):
        self.fotos=[];self.glitches=[];self.estados=[];self.estados_hd=[];self.glitch_activo=False;self.vistas=[];self.escala=1
        self.aspecto='clasico'
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
        vistas=[vista_pantalla(v,tamaño,aspecto=self.aspecto) for v in (self.estados_hd or self.estados)]
        self.fotos=[ImageTk.PhotoImage(v) for v in vistas]
        originales=self.estados_hd or self.estados
        self.senales=[[self.fotos[i]]+[ImageTk.PhotoImage(vista_pantalla(v,tamaño,fase,self.aspecto)) for fase in (1,2)] for i,v in enumerate(originales)]
        self.glitches=[[ImageTk.PhotoImage(interferencia(v,i)) for i in range(6)] for v in vistas]

    def aplicar_aspecto(self,aspecto):
        # El aspecto cambia geometria; las ilustraciones y efectos son comunes.
        self.aspecto=normalizar_diseno(aspecto)

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

def dibujar_marco(c,fase,color,estado,nivel=0,glitch=False,escala=1,aspecto='clasico'):
    from disenos_pantalla import cabecera
    superficie(c,aspecto,360,292)
    cabecera(c,aspecto,estado,color,escala)
    if glitch:
        c.create_line(17,49,135,49,fill='#ff3c72',width=3)
        c.create_line(170,271,337,271,fill='#ff96ab',width=3)
