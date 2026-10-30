"""Genera la galería pública con recursos y renderizadores de Capri, sin capturar el escritorio."""
from pathlib import Path
import base64,io,sys
from types import SimpleNamespace
from unittest.mock import patch
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image,ImageDraw,ImageFont,ImageTk

BASE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(BASE/'src'),str(BASE/'tests')]
from test_companera_control import ModoPersonaje
from fuentes import cargar

SALIDA=BASE/'docs/media/readme'
BG='#0b1019';BLANCO='#e8edf4';ROJO='#ff365e';GRIS='#99a8bc'

def fuente(n,bold=False):
    return ImageFont.truetype(str(BASE/'assets/fonts'/('ChakraPetch-Bold.ttf' if bold else 'ChakraPetch-Regular.ttf')),n)

def fondo(w,h):
    im=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(im)
    for y in range(h):
        q=y/max(1,h-1);d.line((0,y,w,y),fill=(round(13+q*5),round(18-q*4),round(29+q*5)))
    for x in range(0,w,48):d.line((x,0,x,h),fill='#171b2a')
    for y in range(0,h,48):d.line((0,y,w,y),fill='#171b2a')
    d.line((28,1,w-28,1,w-1,28,w-1,h-28,w-28,h-1,1,h-1,1,28,28,1),fill='#793043',width=2)
    return im

def tarjeta(vista,titulo,subtitulo,tamano=(720,500),abajo=False):
    im=fondo(*tamano);d=ImageDraw.Draw(im)
    d.text((32,25),titulo,font=fuente(31,True),fill=BLANCO)
    d.text((33,68),subtitulo,font=fuente(18),fill=GRIS)
    copia=vista.convert('RGBA').copy();copia.thumbnail((tamano[0]-64,tamano[1]-135),Image.Resampling.LANCZOS)
    x=(tamano[0]-copia.width)//2;y=tamano[1]-copia.height if abajo else 119+(tamano[1]-135-copia.height)//2
    im.paste(copia,(x,y),copia)
    return im

def envolver(texto,f,ancho):
    lineas=[]
    for parrafo in texto.split('\n'):
        linea=''
        for palabra in parrafo.split(' '):
            candidato=(linea+' '+palabra).strip()
            if linea and f.measure(candidato)>ancho:lineas.append(linea);linea=palabra
            else:linea=candidato
        lineas.append(linea)
    return lineas

def lienzo(c):
    """Rasteriza solo nuestro Canvas. No lee ventanas ni píxeles del escritorio."""
    w=int(float(c.cget('width')));h=int(float(c.cget('height')))
    bg=c.cget('bg');im=Image.new('RGBA',(w,h),(0,0,0,0) if bg=='#010203' else bg)
    d=ImageDraw.Draw(im)
    for i in c.find_all():
        tipo=c.type(i);p=c.coords(i)
        if tipo=='image':
            datos=c.tk.call(c.itemcget(i,'image'),'data','-format','png')
            if isinstance(datos,str):datos=base64.b64decode(datos)
            foto=Image.open(io.BytesIO(datos)).convert('RGBA');anchor=c.itemcget(i,'anchor')
            x=p[0] if anchor in ('w','nw','sw') else p[0]-foto.width if anchor in ('e','ne','se') else p[0]-foto.width/2
            y=p[1] if anchor in ('n','nw','ne') else p[1]-foto.height if anchor in ('s','sw','se') else p[1]-foto.height/2
            im.alpha_composite(foto,(round(x),round(y)))
        elif tipo in ('polygon','rectangle','oval'):
            color=c.itemcget(i,'fill') or None;borde=c.itemcget(i,'outline') or None
            g=max(1,round(float(c.itemcget(i,'width'))))
            if tipo=='polygon':d.polygon(list(zip(p[::2],p[1::2])),fill=color,outline=borde,width=g)
            elif tipo=='rectangle':d.rectangle(p,fill=color,outline=borde,width=g)
            else:d.ellipse(p,fill=color,outline=borde,width=g)
        elif tipo=='line':
            d.line(list(zip(p[::2],p[1::2])),fill=c.itemcget(i,'fill'),width=max(1,round(float(c.itemcget(i,'width')))))
        elif tipo=='arc':
            inicio=float(c.itemcget(i,'start'));extension=float(c.itemcget(i,'extent'))
            d.arc(p,start=-inicio-extension,end=-inicio,fill=c.itemcget(i,'outline'),width=max(1,round(float(c.itemcget(i,'width')))))
        elif tipo=='text':
            f=tkfont.Font(root=c,font=c.itemcget(i,'font'));prop=f.actual()
            tam=round(abs(prop['size'])*float(c.tk.call('tk','scaling')))
            ff=fuente(max(1,tam),prop['weight']=='bold');caja=c.bbox(i)
            ancho=float(c.itemcget(i,'width'));texto=c.itemcget(i,'text')
            lineas=envolver(texto,f,ancho) if ancho else texto.split('\n')
            paso=f.metrics('linespace');justificar=c.itemcget(i,'justify')
            for n,linea in enumerate(lineas):
                x=caja[0]+1
                if justificar=='center':x+=(caja[2]-caja[0]-d.textlength(linea,font=ff))/2
                elif justificar=='right':x+=caja[2]-caja[0]-d.textlength(linea,font=ff)-2
                d.text((x,caja[1]+n*paso),linea,font=ff,fill=c.itemcget(i,'fill'),anchor='lt')
    return im

def guardar(im,nombre):
    im.save(SALIDA/nombre,optimize=True)

def gif(frames,nombre,duracion):
    muestra=Image.new('RGB',(320,720))
    for j,i in enumerate((0,len(frames)//3,len(frames)//2,len(frames)-1)):
        muestra.paste(frames[i].convert('RGB').resize((320,180)),(0,j*180))
    paleta=muestra.quantize(colors=128)
    cuadros=[f.convert('RGB').quantize(palette=paleta,dither=Image.Dither.NONE) for f in frames]
    cuadros[0].save(SALIDA/nombre,save_all=True,append_images=cuadros[1:],duration=duracion,loop=0,optimize=True,disposal=2)

def portada():
    im=fondo(1440,600);d=ImageDraw.Draw(im)
    d.text((68,47),'ENLACE PERSONAL // WINDOWS',font=fuente(22,True),fill=ROJO)
    d.text((57,84),'CAPRI',font=fuente(148,True),fill=BLANCO)
    d.text((68,269),'Tu escritorio tiene una nueva choom.',font=fuente(37,True),fill=BLANCO)
    d.text((69,334),'Voz, IA local y una buena dosis de caos.',font=fuente(27),fill=GRIS)
    d.line((69,400,700,400),fill='#8b3049',width=2)
    d.text((69,435),'HABLA  /  EXPLORA  /  ACOMPAÑA',font=fuente(23,True),fill='#63dcc2')
    d.text((69,518),'ES  ·  EN  ·  PT-BR  ·  JA',font=fuente(23),fill=GRIS)
    with Image.open(BASE/'assets/capri-asomo-fiel-v3.png') as original:
        capri=original.convert('RGBA');capri.thumbnail((635,510),Image.Resampling.LANCZOS)
        im.paste(capri,(858,600-capri.height),capri)
    guardar(im,'portada.png')

class Oculta(tk.Toplevel):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.withdraw()
    def deiconify(self):pass
    def lift(self,*a):pass
    def focus_force(self,*a):pass
    def focus_set(self,*a):pass
    def grab_set(self,*a):pass
    def grab_release(self,*a):pass

def generar():
    SALIDA.mkdir(parents=True,exist_ok=True);cargar(BASE);portada()
    with patch('tkinter.Toplevel',Oculta),patch('ventanas.mostrar_no_activar'),ModoPersonaje().capri() as (c,_):
        c.cfg['modo_visual']='pantalla';c.animar()
        guardar(tarjeta(lienzo(c.canvas),'MODO PANTALLA','Un enlace flotante con Capri.'),'modo-pantalla.png')
        c.companera.redimensionar(1.3)
        personaje=ImageTk.getimage(c.companera.fotos[0])
        guardar(tarjeta(personaje,'MODO PERSONAJE','Se mueve, cae y se sujeta a tus ventanas.'),'modo-personaje.png')
        c.cfg['modo_visual']='personaje';c.abrir_menu_radial(SimpleNamespace(x_root=500,y_root=400))
        guardar(tarjeta(lienzo(c.radial.canvas),'TODO A UN CLIC','Modos, tamaño, voz y ajustes desde el menú radial.'),'menu-radial.png');c.cerrar_radial()
        c.llamar_capri(invitado='talia');c.llamada_ui.aceptar();c.revisar_interacciones();c.llamada_ui.dibujar()
        guardar(tarjeta(lienzo(c.llamada_ui.c),'UNA LLAMADA INESPERADA','Bromas, voces invitadas y subtítulos en el enlace.'),'llamada.png')
        c.llamada_ui.rechazar();c.descartar_reaccion()
        with patch('asomo.random.choice',return_value='abajo'):c.iniciar_asomo()
        a=c.asomo['curioso'];frames=[]
        for i in range(36):
            a.dibujar(a.inicio+1+i/12,cursor=(-1000 if i<18 else 9000,300))
            frame=tarjeta(lienzo(c.canvas),'¿QUÉ ESTÁS HACIENDO, CHOOM?','Se asoma al borde y sigue el cursor.',abajo=True)
            cx=140 if i<18 else 570;cy=230
            ImageDraw.Draw(frame).polygon([(cx,cy),(cx,cy+28),(cx+7,cy+21),(cx+12,cy+32),(cx+17,cy+29),(cx+12,cy+18),(cx+22,cy+18)],fill='#e8edf4',outline='#59c6bc',width=1)
            frames.append(frame)
        gif(frames,'asomo.gif',90);c.terminar_asomo()
        from apagado import LienzoApagado
        c.canvas.configure(width=640,height=360);LienzoApagado(c.canvas).dibujar(3.8)
        guardar(tarjeta(lienzo(c.canvas),'FLATLINE // APAGADO','Una secuencia CRT para el apagado confirmado.'),'apagado.png')
        with patch.object(c.root,'winfo_screenwidth',return_value=1280),patch.object(c.root,'winfo_screenheight',return_value=720),patch.object(c.root,'winfo_x',return_value=round(1080-c.companera.ancho/2)),patch.object(c.root,'winfo_y',return_value=round(480-c.companera.alto/2)),patch.object(c.root,'winfo_width',return_value=c.companera.ancho),patch.object(c.root,'winfo_height',return_value=c.companera.alto):c.iniciar_despedida()
        from intro import dibujar_viaje,VIAJE
        frames=[];frase=c.frase_despedida
        for i in range(96):
            t=i*.09;c.canvas.delete('all')
            if t<1.1:
                p=t/1.1;viaje=c.salida_traslado
                dibujar_viaje(c.canvas,VIAJE+(1-VIAJE)*p,inicio=viaje.inicio,fin=viaje.fin);viaje.dibujar(c.canvas,p)
            elif t<4.:
                q=t-1.1;c.salida_camara.dibujar(c.canvas,q,frase,hablando=.4<q<2.5,boca=int(q*6)%4!=0,finalizada=q>=2.5)
            else:
                c.salida.imagen=c.salida_camara.fotos[3];c.salida.dibujar(c.canvas,(t-4.)/4.4)
            vista=lienzo(c.canvas);base=fondo(1280,720);base.paste(vista,(0,0),vista)
            frames.append(base.resize((860,484),Image.Resampling.LANCZOS))
        gif(frames,'despedida.gif',90)
    print('\n'.join(f'{p.name}: {p.stat().st_size:,} bytes' for p in sorted(SALIDA.glob('*')) if p.suffix in ('.png','.gif')))

if __name__=='__main__':generar()
