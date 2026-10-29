# Avatar corregido: misma ilustración y tres bocas

`assets/capri-base-v2.png` conserva, byte por byte, la imagen capri-3.png que ya usaba la aplicación: https://mudae.net/uploads/3127100/OwjeVmT~59966d2d98c2.png. El pelo, los ojos, el cuerpo y la pose no se generan de nuevo. El avatar anterior de seis fotogramas quedó descartado.

`assets/capri-bocas-v2.png` es un atlas transparente generado con la herramienta integrada image_gen el 27 de octubre de 2026. Contiene solo formas de boca blancas; no contiene personajes. El renderer conserva el estado normal original y superpone las variantes abierta/sonrisa únicamente dentro de la región (111,64)-(142,89) de la imagen base de 225 × 350. La posición se corrigió contrastando la línea blanca original con una vista ampliada de coordenadas. La superposición también recorta sus píxeles al plano neutro para no invadir piel verde, ojos ni contornos de color. Las pruebas comprueban que esas zonas permanecen intactas.

La interfaz usa Chakra Petch, procedente de https://github.com/google/fonts/tree/main/ofl/chakrapetch. Se incluyen las variantes Regular/Bold y su licencia en `assets/fonts/OFL.txt`. La fuente solo se registra dentro del proceso de Capri.

Los tres estados comparten un recorte de cámara y el mismo efecto de pantalla. Las bandas desplazadas de las interferencias son un efecto temporal del renderer, no otro dibujo del personaje. No hay colmillos ni lengua de colores en las bocas generadas.

## Prompt final enviado a la herramienta integrada

Asset type: tiny animation mouth overlays for an existing character, NOT a new character illustration. Reference image is Capri with the correct original hair and body: do NOT draw or change her hair, eyes, face outline, jacket or body. Generate ONE horizontal transparent sprite atlas with exactly THREE equal square cells in one row. Each cell contains ONLY a single stylized solid WHITE mouth mark on true transparency, no face, no eyes, no labels. The mouth follows the character's angular white zigzag mouth and tilts upward to the right by approximately 35 degrees. Keep the two mouth corner anchors identical in all three cells, same position and scale. Cell1 normal: thin closed white zigzag slit. Cell2 talking: an opened mouth with the ENTIRE INSIDE one continuous opaque WHITE shape, a compact angular oblique lozenge/wedge with lightly irregular zigzag edges, like a luminous flat cartoon mouth. Cell3 smiling: a slightly wider upturned white grin, the entire grin is solid white too, no separate teeth. These are abstract simple 2D mouth animation overlays, minimalist flat geometry. NO fangs, NO individual teeth, NO black holes inside white, NO pink or red tongue, NO lips, NO gradients or shading, NO black background, NO head or character drawing. Equal generous transparent margins around every white sprite. The white filled talking mouth must be unbroken white. Approximate square cell shape 512x512; total sheet 1536x512. Do not reproduce any user interface.


## Fuente HD y efectos de pantalla

El modo pantalla usa ahora una [reconstrucción HD](PROMPT_HD.md) del mismo encuadre. El original de 225 × 350 se conserva. El recorte se genera directamente desde los estados de alta resolución al tamaño solicitado, con Lanczos; no se amplía una vista reducida previamente a 320 píxeles. Esto mejora el detalle disponible en los tamaños de interfaz admitidos; no convierte la ilustración en un vector de resolución ilimitada.

El glitch es transitorio: seis variantes con separación de canales, bandas de distintas alturas, desplazamientos y pequeños cortes digitales. Las líneas de trama normales tienen menos opacidad para no emborronar el rostro. Las descargas decorativas sueltas de las transformaciones de modo se han retirado.


La transici?n prepara 163 estados de ida y 43 de vuelta fuera del hilo de interfaz. Durante el movimiento usa remuestreo r?pido y durante la pausa central y los extremos usa Lanczos. El temporizador descuenta el tiempo de dibujo para mantener una cadencia objetivo de 60 Hz. El rendimiento final depende del equipo. La sombra del personaje conserva su silueta completa con un desplazamiento menor (5 px, 7 durante glitch). Durante la captura de voz aparece un indicador temporal ?TE ESCUCHO? sobre el personaje, con barras de nivel; se oculta al terminar. La despedida usa rojo #f60031 muestreado de la referencia, mano ligeramente a la izquierda de la estrella y destellos diagonales m?s largos.


Despedida electrica (4,4 s): el antebrazo se consume hacia el dedo conservando la escala de la mano; una descarga delgada con nucleo luminoso, cambios angulares y ramificaciones proporcionales asciende hacia la estrella. Al llegar aumenta el brillo, se contraen los rayos y los destellos se reducen hasta desaparecer antes de cerrar. No utiliza capturas del escritorio ni agrega imagenes a pantalla completa.


Revision de despedida: primero se traslada la imagen actual de Capri al centro (0-18%); solo despues forma la mano alli (18-33%). La mano completa se transforma geometricamente en una descarga roja rellena (58-70%), conservando un volumen proporcional al antebrazo. Se interpola el contorno uniforme de ambas siluetas y el rayo asciende y se estrecha hasta la estrella (70-95%). Sustituye la version previa de hilos, nucleo rosa y ramas, y conserva el apagado gradual final.


Ajuste de traslado y estela final: la llegada al centro reutiliza intro.dibujar_viaje, el mismo renderer de desplazamiento del personaje. La mano se desintegra en franjas desplazadas hacia la energia, en lugar de interpolarse a un zigzag macizo. La subida reutiliza la energia orientada a la estrella con tres puntas escalonadas y convergentes; el volumen inicial depende de la altura de la mano y se afina al llegar. Las chispas y cortes son transparentes fuera de las siluetas. Se conserva el apagado gradual de la estrella.


Mano de referencia 201212: contorno vectorial trazado con 91 vertices a partir de su silueta, conservando curvas de indice, nudillos, pulgar y muneca. El antebrazo se prolonga fuera de pantalla. Al aterrizar el traslado NO recompone la imagen de origen: la mano se revela directamente a escala final desde la energia del centro, sin una pantalla intermedia ni una mano miniatura que crece. La disolucion usa 80 franjas finas con desplazamiento continuo en vez de 18 cortes gruesos.


Formacion por teselas: la despedida descompone la transmision en piezas que vuelan por arcos cortos y encajan directamente en celdas recortadas de la silueta de la mano. Cada pieza conserva su destino, cambia del color muestreado de la imagen al rojo, y completa la mano en el 30% de la secuencia. Sustituye los rayos de traslado de esta despedida. La locomocion normal del personaje sigue igual. La descarga ascendente conserva una punta visible hasta alcanzar exactamente el nucleo de la estrella al 88%; se absorbe hasta el 92%. El pulso de contacto y el apagado de la estrella ocurren despues de la llegada.


Revision 2026-10-29: morfosis con 85 estados de ida y 31 de vuelta, cola de anticipacion de 8 y cache acotada de las dos direcciones. Recorta margenes transparentes antes de transferir imagenes a Tk y evita composiciones cuando solo queda una fuente. Posicion y bitmap usan el mismo estado preparado. La pose de personaje se completa al 78%, antes del viaje final que empieza al 78%, evitando que llegue una bienvenida gigante y sea sustituida de golpe. Perfil Tk propio a1920x1080, no FPS del escritorio: atraso maximo preparado 1.304s->0.064s; coste mediano9.4ms, p9588.46ms, sin prometer60FPS.

Los saltos sobre ventanas usan TrasladoTeselas: fragmentos con la textura y alfa reales de Capri, tinte rojo transitorio y reconstruccion de la pose sentada durante el recorrido. Sustituye descargas gigantes externas. El menu radial busca espacio sobre el personaje y, si no cabe, un lateral; ajusta diametro para mantenerse en pantalla. Soltar en cualquier punto conserva esa ubicacion. Solo se ajusta a una barra si la cadera queda a menos de8px escalados, y conserva el punto horizontal elegido en vez de forzar esquina.


Optimizacion adicional: en Windows los frames de morfosis se componen como RGB con el mismo color transparente #010203 de la ventana, evitando la conversion RGBA de Tk; los demas sistemas mantienen alfa. El Canvas conserva un unico item de imagen, mueve sus coordenadas e intercambia el bitmap solo al cambiar de estado. Con el estado listo se interpola la posicion entre fotogramas. Perfil Tk propio1920x1080:158ticks/2.7s, mediana0.86ms,p9511.62ms, atraso maximo de preparacion0.002s; referencia anterior84ticks,9.4ms,p9588.46ms,.064s. No equivale a medir FPS del escritorio ni garantiza60FPS en cualquier equipo.

Autonomia: destinos aleatorios en todo el area de trabajo, preferencia75% por una ventana cercana cuando existe una accesible, caida40px/s2 limitada65px/s (escala1), pausa tras aterrizar/arrastrar, sujecion probabilistica temporal2-4s con marca y union a mano. El anclaje se limpia al iniciar un traslado. Apariencia y ajustes tienen vistas propias con la paleta violeta/rojo/verde y tipografia de Capri; no se anaden assets externos nuevos.


Revision roja: la paleta de marcos, entradas, dialogos, menu y ajustes pasa a carmesi/rojo oscuro. VentanaCyber proporciona contorno recortado, titulo propio, cierre, arrastre y redimensionado desde esquina inferior derecha; se aplica a ajustes, aspectos y conversacion. Las tarjetas de aspectos son Canvas angulares con vista del sprite y estado ACTIVO. Conversacion mantiene visible la entrada con altura de historial ajustada. El panel muestra DI CAPRI y la entrada lo recuerda. La tecla global F2-F12 se configura en Voz, conservando F8 por defecto.

Fisica final: se elimina toda espera al soltar/aterrizar. Gravedad900px/s2 y terminal700px/s a escala1. La sujecion tiene estaca de dos planos, guarda y mango, insercion0.16s, grietas/chispas de impacto y union a la mano. Un asentamiento amortiguado y rotacion discreta de hasta4grados alrededor de la mano simulan el cuerpo colgando. La estaca queda fija y se elimina al viajar. La sombra se compone dentro de los bitmaps de morfosis y teselas antes del traslado; la cache incluye el aspecto elegido.
