"""Secuencia visual de enlace. No bloquea el audio ni simula carga del modelo."""
import math
from fuentes import FAMILIA

DURACION=2.8

def dibujar(c,progreso,imagen=None,escala=1):
    p=max(0,min(1,progreso));c.delete('all')
    if p>=.68:
        # Ventana transparente: solo viaja el rayo, sin panel opaco.
        puntos=[75,150,158,105,137,151,222,122,193,170,285,143]
        for color,grosor in [('#791329',17),('#e92346',10),('#ff5872',5),('#ffe4e5',2)]:
            c.create_line(*puntos,fill=color,width=grosor)
        return
    c.create_polygon(13,11,343,11,352,20,352,280,342,290,8,290,8,20,fill='#070d16',outline='#6b969e')
    if imagen is not None and p>.12:
        c.create_image(180,153,image=imagen)
        apertura=min(1,(p-.12)/.38);margen=(1-apertura)*105
        c.create_rectangle(19,47,341,47+margen,fill='#070d16',outline='')
        c.create_rectangle(19,257-margen,341,258,fill='#070d16',outline='')
    if p<.64:
        radio=35+14*math.sin(p*math.pi)
        for i in range(8):
            a=p*8+i*math.pi/4;x=180+radio*math.cos(a);y=151+radio*math.sin(a)
            c.create_line(x,y,x+9*math.cos(a),y+9*math.sin(a),fill='#f1d65e' if i%2 else '#7de0df',width=2)
    titulo='CAPRI'[:min(5,1+int(p*13))]
    if p<.27:titulo+=' /_'[int(p*100)%3]
    c.create_text(180,30,text=titulo,fill='#f0da68',font=(FAMILIA,round(22*escala),'bold'))
    c.create_rectangle(103,133,257,173,fill='#0b111b',outline='#e83c61')
    c.create_text(180,153,text='CONECTANDO',fill='#f3d568',font=(FAMILIA,max(8,round(12*escala)),'bold'))
    longitud=300*p;c.create_line(30,285,30+longitud,285,fill='#ec3c62',width=2)
    if .12<p<.48 or .7<p<.77:
        for i in range(3):
            y=65+(int(p*650)+i*39)%170
            c.create_line(25+i*12,y,330-i*8,y,fill='#6cdad9' if i%2 else '#ec3c62',width=2)
