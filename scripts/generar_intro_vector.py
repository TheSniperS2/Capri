"""Traza el arte de la intro para Canvas. Solo desarrollo: Pillow, numpy, OpenCV.

No se necesita OpenCV en Capri. Ejecutar desde la raíz del repositorio.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

BASE=Path(__file__).resolve().parents[1]
PALETA=['#0d0913','#ff0054','#ed004c','#ff598e','#b10061',
        '#0af02d','#05ae28','#9018e9','#49148a','#f0f3fc','#b8b5da','#1ea9e9']


def trazar():
    im=Image.open(BASE/'assets/capri-intro-primer-plano-v2.png').convert('RGBA')
    im=im.crop((0,0,im.width//2,im.height))
    rgba=np.asarray(im)
    # La textura fotográfica del atlas no forma parte de la silueta vectorial.
    rgb=cv2.medianBlur(rgba[:,:,:3].copy(),5).astype(np.int32)
    colores=np.array([tuple(bytes.fromhex(c[1:])) for c in PALETA],dtype=np.int32)
    indices=np.argmin(((rgb[:,:,None,:]-colores[None,None,:,:])**2).sum(axis=3),axis=2)
    solido=(rgba[:,:,3]>210).astype(np.uint8)
    # Elimina motas semitransparentes, conserva puntas y silueta angular.
    solido=cv2.morphologyEx(solido,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    solido=cv2.morphologyEx(solido,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    # Soporte anatómico continuo debajo de las solapas y los acentos. El atlas
    # tiene recortes abiertos en mangas/pecho: no son dedos ni huecos del pelo.
    soporte=np.zeros_like(solido)
    uniones=[[(466,437),(493,431),(574,455),(624,408),(652,425),(668,470),
              (650,517),(689,585),(658,724),(446,724),(503,678),(476,637),
              (467,570),(441,516),(450,471)],
             [(386,424),(431,441),(466,486),(486,556),(473,630),(440,610),
              (407,591),(376,580),(343,548),(309,533),(277,516),(260,493),
              (301,480),(344,493)],
             [(644,433),(674,446),(710,439),(752,448),(788,462),(827,483),
              (854,507),(860,545),(822,548),(794,586),(757,594),(715,588),
              (693,554),(677,517)],
             [(266,565),(305,578),(351,589),(387,605),(422,640),(450,649),
              (439,607),(396,556),(321,530),(276,537)],
             [(738,531),(798,553),(851,530),(828,573),(797,601),(773,616),
              (751,580)],
             [(250,489),(301,469),(356,487),(415,510),(452,555),(475,607),
              (470,648),(436,642),(394,620),(356,603),(310,590),(272,575),(251,540)],
             [(685,446),(739,437),(788,452),(847,486),(879,514),(860,555),
              (841,584),(820,610),(783,632),(758,609),(731,573),(700,521)]]
    for p in uniones:cv2.fillPoly(soporte,[np.array(p,dtype=np.int32)],1)
    nuevos=(soporte>0)&(solido==0);solido|=soporte
    # Las motas alfa encerradas dentro del personaje no son recortes de su silueta.
    n,etiquetas,stats,_=cv2.connectedComponentsWithStats(1-solido)
    for i in range(1,n):
        x,y,w,h,area=stats[i]
        if area<=180 and x>0 and y>0 and x+w<im.width and y+h<im.height:solido[etiquetas==i]=1
    reparar=((solido>0)&(rgba[:,:,3]<=210)).astype(np.uint8)
    rgb=cv2.inpaint(rgb.astype(np.uint8),reparar,3,cv2.INPAINT_TELEA).astype(np.int32)
    rgb[nuevos]=tuple(bytes.fromhex(PALETA[0][1:]))
    indices=np.argmin(((rgb[:,:,None,:]-colores[None,None,:,:])**2).sum(axis=3),axis=2)
    # Los refuerzos son polígonos simples independientes: no dependen del
    # relleno par/impar de los contornos con puentes, ni se abren con el rig.
    formas=[[PALETA[0],[v for p in union for v in p]] for union in uniones]
    for k,color in [(-1,PALETA[0])]+list(enumerate(PALETA)):
        mask=solido.copy() if k==-1 else ((indices==k)&(solido>0)).astype(np.uint8)
        if k>=0:
            # Solapamiento de un píxel antes de simplificar: evita grietas entre colores.
            mask=cv2.dilate(mask,np.ones((3,3),np.uint8))&solido
        contornos,jerarquia=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        if jerarquia is None:continue
        for i,contorno in enumerate(contornos):
            if jerarquia[0,i,3]!=-1 or cv2.contourArea(contorno)<120:continue
            exterior=cv2.approxPolyDP(contorno,1.0,True).reshape(-1,2).tolist()
            if len(exterior)<3:continue
            hueco=jerarquia[0,i,2]
            while hueco!=-1:
                if cv2.contourArea(contornos[hueco])>=30:
                    interior=cv2.approxPolyDP(contornos[hueco],1.0,True).reshape(-1,2).tolist()
                    # Un puente de ida/vuelta conserva huecos con el relleno par/impar de Tk.
                    dist=((np.array(exterior)[:,None,:]-np.array(interior)[None,:,:])**2).sum(axis=2)
                    a,b=np.unravel_index(dist.argmin(),dist.shape)
                    vuelta=interior[b:]+interior[:b]+[interior[b]]
                    exterior=exterior[:a+1]+vuelta+[exterior[a]]+exterior[a+1:]
                hueco=jerarquia[0,hueco,0]
            formas.append([color,[v for p in exterior for v in p]])
    salida={'tamano':list(im.size),'formas':formas,'origen':'capri-intro-primer-plano-v2.png: mitad izquierda; uniones de mangas y torso reparadas'}
    ruta=BASE/'assets/capri-intro-vector-v5.json'
    ruta.write_text(json.dumps(salida,separators=(',',':')),encoding='utf-8')
    print(f'{len(formas)} formas, {ruta.stat().st_size} bytes')


if __name__=='__main__':trazar()
