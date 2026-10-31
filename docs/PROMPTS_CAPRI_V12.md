# Despedida v12: proporciones y señal de cámara

Recurso final: `assets/capri-despedida-expresiones-v8.png`, atlas 3344 × 1882, cuatro imágenes de 1672 × 941 sin reducir. Generado con la herramienta integrada imagegen, conservando los originales. Orden: mirada arriba, mirada al espectador, habla, sonrisa. El blanco del pelo es textura de señal sobre magenta opaco, nunca transparencia.

Se usaron las cinco referencias aportadas por el usuario: `Capri_03_CPEDGEII.webp`, `capri-cyberpunk-edgerunners-2-v0-33la1aop5nxh1.webp`, `capri-cyberpunk-edgerunners-2-v0-wj2j5enp5nxh1.webp`, `images (7).jfif` y `r05BWOamk5HWX3ZTjcUmNFPKbMxDXKNnU5zhj_USaEabd1G5OVs0xXQn6m2RqUuNy5tnHUJ8nNElMFv4S__1PQ.webp`. Referencias de identidad, no recursos redistribuidos del programa. El resultado es una ilustración de la aplicación, no arte oficial.

El clip de despedida se examinó localmente: bordes oscuros, señal algo lavada, color cálido y textura de vídeo. El runtime añade una óptica independiente con viñeta, velo cálido, trama fina y grano animado. El retrato mantiene el encuadre LANCZOS a resolución de pantalla, sin JPEG ni reducción a SD. Esa óptica también forma parte del fotograma que se contrae hasta la mano. No se abre ninguna cámara real.

La intro usa `capri-intro-vector-v6.json`. `scripts/generar_intro_limpia.py` reconstruye mangas, torso, palmas y dedos mediante polígonos simples, y conserva la cabeza de v5 separando sus islas antes de volver a trazarla. Así se evitan los puentes falsos de contornos con huecos al recortar. Pillow/numpy/OpenCV sólo para generar el JSON; el runtime no usa OpenCV.

## Prompts exactos

### Retrato base

```text
Create ONE SINGLE WIDE 16:9 HD anime camera farewell portrait of CAPRI using ALL FIVE supplied actual anime frames as identity references (reference only; not a collage). Top priority: accurately MATCH THE UNUSUAL PROPORTIONS AND DESIGN, do not make a generic human anime girl. Her hair is a MONUMENTAL continuous FLAT hot magenta polygonal mass, about FIVE TIMES the width of her tiny face; immense chunky irregular plates and angular straight cuts, long narrow lightning splinters extending sideways, not a traditional hairstyle or soft 3D starburst, not many little strands, not hair highlights. The mass has delicate WHITE SIGNAL SPECKLE TEXTURE ON OPAQUE PINK surfaces as in the references; the white marks are not transparent holes. Tiny narrow BLACK FACE shaped like a tilted triangular wedge, about 20%-23% of image width. LIME GREEN angular domino mask, two circular blue ring irises and white disc pupils, thin black geometric brows, confident friendly small WHITE TRIANGULAR GRIN with two jagged notches along its upper edge. Face is mostly planar black geometry with no nose, no skin, no lips, no eyelashes, no cheek shadows. Extremely thin black neck and narrow black geometric shoulders, one bright lime green arrow shoulder panel, angular magenta lightning on black chest, subtle purple edge outlines. NO WHITE JACKET COLLAR OR LAPELS (previous fake versions had large white lapels, those are wrong). COMPOSITION: medium close bust view showing the whole immense magenta crown spread almost across the full screen in the upper 65%, tiny face in the lower central region around 62%-76% of height, slim neck and upper chest reach bottom edge. The crown can crop slightly at the very top, but must read as a HUGE IRREGULAR MASS, not a symmetric five-point star. Hair to face ratio must match supplied photos. Camera faces Capri, modest natural tilt, two eyes look at viewer, warm playful restrained smile. Dark blue gray cloudy night in background, compatible with departure toward a star, no buildings or other characters. Professionally drawn 2D flat cel animation with precise clean contours and a little white speckled signal texture only within magenta areas. Crisp HD native render, requested largest available 16:9 resolution. No baked camera blur, no UI, no text, no watermark, no film border, no panels or atlas. Single full frame.
```

### Mirada arriba

```text
Precise tiny expression edit of this SINGLE full image. Preserve EXACTLY image dimensions, all opaque speckled pink hair pixels, hair silhouette, small face size, mask, head tilt, black body, green shoulder, background and composition. Change ONLY the eye gaze: both white pupils and blue circular irises look slightly upward toward a star above, staying inside their existing black circular eye sockets. Preserve the tiny jagged white grin unchanged. Absolutely no head motion or enlargement, no hair redesign, no camera effects, no text, no atlas or grid. Same crisp cel anime, one image.
```

### Boca al hablar

```text
Precise local mouth edit on this ONE image. Preserve EXACTLY image size, all hair shape and speckle texture, small face proportions, both circular eyes, head position/tilt, green mask, thin body and blue night sky. Change ONLY the existing little white triangular jagged grin to a slightly more open small white angular speaking mouth, with same width and same two jagged notches on its upper edge, its bottom point 12 pixels lower. It is a friendly goodbye mouth, no human lips, no teeth details, no nose, no changes to any other pixels. Single high-definition cel anime frame, no text, no grid, no camera blur.
```

### Sonrisa final

```text
Precise local happy-goodbye expression edit on this ONE image. Preserve EXACTLY image size, hair silhouette and all opaque pink speckle texture, small face size, head tilt, green mask, black body, green shoulder and night sky. Change ONLY both eyes: close them into two happy upward-curved GREEN CRESCENT eyelids within the existing black eye sockets, like Capri warmly smiling goodbye. Keep the existing small white triangular jagged grin, raise its corners slightly while retaining its 2 upper notches, no human lips or nose. No other edits or shifts, no change to head or face size. Single crisp cel anime frame, no camera effects, no text, no atlas.
```
