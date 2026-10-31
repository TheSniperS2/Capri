"""Traza el contorno de la mano del video aportado por el usuario.

Solo desarrollo: av, numpy, opencv-python-headless. No redistribuye el video.
python scripts/trazar_mano_despedida.py --video video.mp4 --segundo 36.04
"""
import argparse,json
from pathlib import Path
import av,cv2,numpy as np
from PIL import Image


def main():
    p=argparse.ArgumentParser();entrada=p.add_mutually_exclusive_group(required=True)
    entrada.add_argument('--video');entrada.add_argument('--imagen');p.add_argument('--segundo',type=float,default=36.04)
    p.add_argument('--salida');args=p.parse_args();segundo=None
    if args.imagen:imagen=Image.open(args.imagen).convert('RGB')
    else:
        c=av.open(args.video);c.seek(int(args.segundo*1e6))
        cuadro=next(f for f in c.decode(video=0) if f.time is not None and f.time>=args.segundo)
        segundo=float(cuadro.time);imagen=cuadro.to_image();c.close()
    a=np.asarray(imagen);alto=imagen.height
    mascara=(((a[:,:,0]>150)&(a[:,:,1]<65)&(a[:,:,2]<150)) if args.imagen else
             ((a[:,:,0]>130)&(a[:,:,1]<55)&(a[:,:,0]>a[:,:,2]*1.6))).astype(np.uint8)
    contornos,_=cv2.findContours(mascara,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    contorno=max(contornos,key=cv2.contourArea);puntos=cv2.approxPolyDP(contorno,1.65 if args.imagen else .65,True).reshape(-1,2).tolist()
    if cv2.contourArea(contorno)<3000:raise ValueError('El fotograma no contiene una silueta roja de mano utilizable.')
    salida=np.zeros_like(mascara);cv2.fillPoly(salida,[np.array(puntos)],1)
    iou=float(np.logical_and(salida,mascara).sum()/np.logical_or(salida,mascara).sum())
    ancla=min(puntos,key=lambda p:p[1]);extendidos=[]
    for x,y in zip(puntos,puntos[1:]+puntos[:1]):
        extendidos.append(x)
        if x[1]>=alto-3 and y[1]>=alto-3 and abs(x[0]-y[0])>20:extendidos.extend([[x[0],alto+150],[y[0],alto+150]])
    rojo=(a[:,:,0]>220)&(a[:,:,1]<15)&(a[:,:,2]<150)
    if int(rojo.sum())<100:raise ValueError('No hay suficientes píxeles rojos para obtener el color de la mano.')
    color=np.median(a[rojo],axis=0).astype(int)
    datos=dict(tamano=list(imagen.size),puntos=extendidos,iou=iou,ancla=ancla,alto_visible=alto-ancla[1],referencia_segundos=segundo,color='#%02x%02x%02x'%tuple(color))
    if args.imagen:datos['suavizar']=True
    destino=args.salida or ('assets/mano-despedida-v3.json' if args.imagen else 'assets/mano-despedida-v2.json')
    Path(destino).write_text(json.dumps(datos,separators=(',',':')),encoding='utf8')
    print(f'{len(extendidos)} puntos; coincidencia de silueta IoU={iou:.5f}')


if __name__=='__main__':main()
