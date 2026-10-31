"""Reconstruye el cuerpo con planos editables; conserva cabeza y rig de la intro.

Sólo desarrollo: Pillow, numpy, OpenCV. Runtime consume únicamente el JSON.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw

BASE=Path(__file__).resolve().parents[1]
NEGRO='#0d0913';ROSA='#ff0054';VERDE='#0af02d';VIOLETA='#9018e9'


def generar():
    formas=[]
    def pieza(color,*puntos):formas.append([color,[v for p in puntos for v in p]])
    # Cuello y tronco: una sola superficie sólida hasta el borde inferior.
    pieza(NEGRO,(477,400),(613,382),(649,427),(626,463),(673,485),(701,549),
          (686,623),(652,724),(431,724),(481,673),(465,623),(443,545),(414,488),(465,450))
    # Mangas continuas desde la axila hasta cada muñeca. Ningún recorte interior.
    pieza(NEGRO,(439,458),(385,441),(337,465),(300,481),(248,465),(207,482),
          (217,542),(279,578),(336,602),(390,615),(433,643),(469,619),(481,556))
    pieza(NEGRO,(648,459),(697,439),(744,446),(788,464),(838,458),(877,484),
          (865,551),(828,593),(790,623),(744,621),(702,601),(672,557))
    # Cada palma y todos sus dedos pertenecen al mismo contorno, sin puentes
    # de ida/vuelta como los del trazado fotográfico anterior.
    pieza(NEGRO,(213,477),(163,447),(127,421),(112,388),(62,348),(84,415),
          (99,452),(124,478),(91,502),(40,536),(4,624),(85,582),(117,563),
          (137,589),(126,631),(141,714),(178,659),(173,616),(198,629),
          (278,680),(258,638),(230,603),(214,573),(199,543),(242,551),
          (310,579),(282,545),(235,515))
    pieza(NEGRO,(839,472),(865,429),(915,381),(946,302),(1025,279),(1010,345),
          (966,397),(945,437),(968,453),(1009,457),(1047,472),(1086,512),
          (1041,497),(1002,489),(974,495),(1001,527),(1046,556),(1049,608),
          (1007,567),(976,548),(955,541),(964,583),(989,628),(973,685),
          (945,619),(923,572),(901,546),(873,552))
    # Bordes y acentos sobre las superficies sólidas; nunca agujerean la manga.
    pieza(VIOLETA,(217,531),(279,567),(336,591),(395,607),(433,631),(430,640),
          (389,620),(332,607),(275,584),(215,547))
    pieza(VIOLETA,(702,588),(744,609),(787,612),(826,582),(865,541),(863,553),
          (830,598),(791,628),(741,625),(700,601))
    pieza(ROSA,(246,465),(300,481),(336,465),(380,446),(359,469),(301,496),(247,480))
    pieza(VERDE,(337,478),(372,460),(421,475),(447,518),(412,493),(374,480))
    pieza(ROSA,(788,465),(833,457),(875,481),(861,499),(837,479),(799,480))
    pieza(VERDE,(724,452),(754,452),(793,468),(770,476),(747,465))
    pieza(VIOLETA,(61,349),(79,362),(99,417),(129,444),(124,451),(91,425))
    pieza(ROSA,(62,348),(112,388),(127,421),(162,448),(151,448),(116,425),(102,394))
    pieza(VIOLETA,(42,540),(94,507),(127,479),(140,484),(103,520),(55,549),(4,624))
    pieza(ROSA,(127,630),(141,714),(147,683),(143,632),(157,595),(147,577))
    pieza(VIOLETA,(176,616),(201,623),(278,680),(266,679),(195,636),(176,631))
    pieza(VIOLETA,(946,302),(1025,279),(1015,293),(955,311),(928,381),(876,438),(869,434),(915,377))
    pieza(ROSA,(1025,279),(1010,345),(966,397),(953,411),(959,389),(998,338),(1007,298))
    pieza(VIOLETA,(975,485),(1012,478),(1049,487),(1086,512),(1040,495),(1000,488),(976,500))
    pieza(ROSA,(1000,527),(1046,556),(1049,608),(1035,587),(1034,561),(986,535))
    pieza(VIOLETA,(955,541),(968,580),(990,628),(973,685),(972,647),(977,628),(951,583),(944,549))
    # Solapas del diseño de intro, redibujadas en planos coherentes y cerrados.
    pieza(VIOLETA,(391,418),(476,449),(507,506),(492,500),(506,565),(451,521),(442,472))
    pieza('#f0f3fc',(394,419),(473,453),(495,491),(480,484),(496,548),
          (458,517),(453,476),(435,461))
    pieza('#b8b5da',(394,419),(453,454),(478,477),(473,484),(446,461))
    pieza(VIOLETA,(776,416),(708,451),(685,488),(707,520),(701,540),(790,651),
          (754,562),(737,489),(751,450))
    pieza('#f0f3fc',(770,421),(711,456),(695,488),(719,520),(711,538),
          (779,628),(745,554),(726,487),(740,454))
    pieza('#b8b5da',(770,421),(714,455),(706,477),(717,474),(740,449))
    pieza(ROSA,(516,488),(550,505),(594,482),(570,523),(546,529))
    pieza(ROSA,(550,538),(571,532),(597,550),(581,579),(605,607),(578,630),
          (601,675),(563,700),(538,673),(548,638),(524,614),(545,585),(530,564))
    pieza(VERDE,(475,534),(483,555),(465,600),(438,642),(444,607),(458,577))
    pieza(VERDE,(651,531),(641,572),(621,612),(620,575),(630,550))
    pieza(ROSA,(491,680),(537,666),(557,697),(540,724),(477,724),(511,705))
    pieza(ROSA,(608,638),(626,668),(624,724),(604,724),(597,688))
    fuente=json.loads((BASE/'assets/capri-intro-vector-v5.json').read_text(encoding='utf8'))
    # Recortar directamente un polígono con puentes de huecos une islas con
    # segmentos horizontales falsos. Separar las islas de la cabeza antes de
    # volver a trazarla evita esas costuras sobre el cuerpo nuevo.
    im=Image.new('RGBA',tuple(fuente['tamano']));d=ImageDraw.Draw(im)
    for tono,xy in fuente['formas']:d.polygon(list(zip(xy[::2],xy[1::2])),fill=tono)
    cabeza=im.crop((0,0,im.width,445))
    # Los dedos levantados del atlas antiguo no pertenecen a la cabeza.
    mascara_cabeza=Image.new('L',cabeza.size)
    ImageDraw.Draw(mascara_cabeza).polygon([(0,0),(im.width,0),(im.width,275),
        (945,275),(945,445),(178,445),(178,330),(0,330)],fill=255)
    cabeza.putalpha(Image.fromarray(np.minimum(np.asarray(cabeza.getchannel('A')),np.asarray(mascara_cabeza))))
    rgba=np.asarray(cabeza)
    colores=list(dict.fromkeys(t for t,p in fuente['formas']))
    for tono in colores:
        rgb=np.array(tuple(bytes.fromhex(tono[1:])),dtype=np.uint8)
        mascara=((rgba[:,:,3]>0)&np.all(rgba[:,:,:3]==rgb,axis=2)).astype(np.uint8)
        contornos,jerarquia=cv2.findContours(mascara,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        if jerarquia is None:continue
        for i,contorno in enumerate(contornos):
            if jerarquia[0,i,3]!=-1 or cv2.contourArea(contorno)<25:continue
            exterior=cv2.approxPolyDP(contorno,1.35,True).reshape(-1,2).tolist()
            hueco=jerarquia[0,i,2]
            while hueco!=-1:
                interior=cv2.approxPolyDP(contornos[hueco],1.35,True).reshape(-1,2).tolist()
                if len(interior)>=3 and cv2.contourArea(contornos[hueco])>5:
                    dist=((np.array(exterior)[:,None,:]-np.array(interior)[None,:,:])**2).sum(axis=2)
                    a,b=np.unravel_index(dist.argmin(),dist.shape)
                    vuelta=interior[b:]+interior[:b]+[interior[b]]
                    exterior=exterior[:a+1]+vuelta+[exterior[a]]+exterior[a+1:]
                hueco=jerarquia[0,hueco,0]
            if len(exterior)>=3:pieza(tono,*exterior)
    datos={'tamano':fuente['tamano'],'formas':formas,'origen':'cabeza v5; cuerpo y manos vectoriales reconstruidos, sin recortes de textura'}
    ruta=BASE/'assets/capri-intro-vector-v6.json'
    ruta.write_text(json.dumps(datos,separators=(',',':')),encoding='utf8')
    print(f'{len(formas)} formas; {ruta.name}')


if __name__=='__main__':generar()
