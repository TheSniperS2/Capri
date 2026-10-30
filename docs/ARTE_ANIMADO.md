# Arte, animaciones e interfaz

`assets/capri-base-v2.png` conserva, byte por byte, la imagen capri-3.png que ya usaba la aplicación: https://mudae.net/uploads/3127100/OwjeVmT~59966d2d98c2.png. El pelo, los ojos, el cuerpo y la pose no se generan de nuevo. El avatar anterior de seis fotogramas quedó descartado.

`assets/capri-bocas-v2.png` es un atlas transparente generado con la herramienta integrada image_gen el 27 de octubre de 2026. Contiene solo formas de boca blancas; no contiene personajes. El renderer conserva el estado normal original y superpone las variantes abierta/sonrisa únicamente dentro de la región (111,64)-(142,89) de la imagen base de 225 × 350. La posición se corrigió contrastando la línea blanca original con una vista ampliada de coordenadas. La superposición también recorta sus píxeles al plano neutro para no invadir piel verde, ojos ni contornos de color. Las pruebas comprueban que esas zonas permanecen intactas.

La interfaz usa Chakra Petch, procedente de https://github.com/google/fonts/tree/main/ofl/chakrapetch. Se incluyen las variantes Regular/Bold y su licencia en `assets/fonts/OFL.txt`. La fuente solo se registra dentro del proceso de Capri.

Los tres estados comparten un recorte de cámara y el mismo efecto de pantalla. Las bandas desplazadas de las interferencias son un efecto temporal del renderer, no otro dibujo del personaje. No hay colmillos ni lengua de colores en las bocas generadas.

## Prompt final enviado a la herramienta integrada

Asset type: tiny animation mouth overlays for an existing character, NOT a new character illustration. Reference image is Capri with the correct original hair and body: do NOT draw or change her hair, eyes, face outline, jacket or body. Generate ONE horizontal transparent sprite atlas with exactly THREE equal square cells in one row. Each cell contains ONLY a single stylized solid WHITE mouth mark on true transparency, no face, no eyes, no labels. The mouth follows the character's angular white zigzag mouth and tilts upward to the right by approximately 35 degrees. Keep the two mouth corner anchors identical in all three cells, same position and scale. Cell1 normal: thin closed white zigzag slit. Cell2 talking: an opened mouth with the ENTIRE INSIDE one continuous opaque WHITE shape, a compact angular oblique lozenge/wedge with lightly irregular zigzag edges, like a luminous flat cartoon mouth. Cell3 smiling: a slightly wider upturned white grin, the entire grin is solid white too, no separate teeth. These are abstract simple 2D mouth animation overlays, minimalist flat geometry. NO fangs, NO individual teeth, NO black holes inside white, NO pink or red tongue, NO lips, NO gradients or shading, NO black background, NO head or character drawing. Equal generous transparent margins around every white sprite. The white filled talking mouth must be unbroken white. Approximate square cell shape 512x512; total sheet 1536x512. Do not reproduce any user interface.


## Fuente HD y efectos de pantalla

El modo pantalla usa ahora una [reconstrucción HD](PROMPT_HD.md) del mismo encuadre. El original de 225 × 350 se conserva. El recorte se genera directamente desde los estados de alta resolución al tamaño solicitado, con Lanczos; no se amplía una vista reducida previamente a 320 píxeles. Esto mejora el detalle disponible en los tamaños de interfaz admitidos; no convierte la ilustración en un vector de resolución ilimitada.

La vista simula una cámara: una ligera reducción de nitidez, grano en tres fases, líneas de barrido y viñeta tenue. Los fotogramas se preparan al cambiar el tamaño, sin generar imágenes en cada actualización normal. Desactivar las interferencias detiene las ráfagas y el grano animado; la textura estática de pantalla permanece.

El glitch es transitorio: seis variantes con franjas de distinta altura, fragmentos desplazados, cortes transparentes y estelas violetas/verdes. Las ráfagas duran aproximadamente 0,22–0,42 segundos. En modo personaje afectan a la pose de pie, sentada y sujetándose; los fragmentos pueden sobresalir del contorno original, conservando el fondo transparente y alfa binario para Windows. Las cachés de poses sujetas tienen límite. Las descargas decorativas sueltas de las transformaciones de modo se han retirado.

## Entrada, transformación y salida

La intro de arranque dura 6,8 segundos. Revela el avatar desde el centro, usa marcas angulares y una paleta roja, y mantiene el rostro despejado del rótulo de conexión. Después el avatar se fragmenta y viaja a su posición, conservando parte de su textura y color. Es una secuencia visual; no representa el avance real de descarga o carga del modelo.

La transformación de pantalla a personaje dura unos 2,7 segundos: el panel se centra, aparece la pose de bienvenida y se reduce antes de llegar a su ubicación. La vuelta es directa y más breve. Se preparan 85 estados de ida y 31 de vuelta mediante un trabajador de Pillow y una cola acotada. Tk recibe las imágenes en el hilo de interfaz; se reutilizan las dos direcciones de la caché. En Windows, los fotogramas usan RGB con el color transparente de la ventana para reducir el coste de transferencia. La preparación y el monitor pueden afectar la fluidez.

La despedida dura unos 4,4 segundos. Las piezas de Capri convergen en una mano roja centrada, basada en la silueta de referencia. El antebrazo se descompone y una descarga compacta, con puntas convergentes, viaja hasta la estrella. La punta alcanza su núcleo antes de la absorción y del apagado gradual. La mano y la estrella son vectoriales. Se usa `#f60031` para la mano; no se captura el escritorio para preparar la secuencia.

F8, Esc con foco o una segunda solicitud de cierre permiten terminar la despedida inmediatamente. Desactivar las animaciones omite el cierre animado.

## Personaje y anclaje

Los saltos emplean `TrasladoTeselas`: cortes con la textura y alfa del sprite, un tinte transitorio y reconstrucción de la pose de destino. La sombra elegida se compone en los fotogramas antes del viaje para evitar que aparezca de golpe al llegar.

El personaje puede aparecer en cualquier punto del área de trabajo y acercarse a ventanas accesibles. Al soltarlo, la caída comienza sin esperar un clic adicional. La gravedad es de 900 px/s² y la velocidad terminal de 700 px/s a escala 1. Escribir en una entrada visible con foco, arrastrar o una interacción activa pueden pausar su movimiento; un campo oculto no lo pausa.

Una estaca temporal puede detener la caída durante 3,5–6 segundos. Se ven la inserción, las marcas de impacto y las chispas. El brazo del sprite se coloca sobre el mango, con dedos delante y balanceo alrededor del agarre. El anclaje desaparece al arrastrar al personaje o al comenzar un traslado. Las cachés de poses y sombras tienen límites.

## Interfaz y accesibilidad visual

La interfaz usa rojo oscuro, carmesí y texto claro. Ajustes, aspectos y conversación tienen contornos angulares, cierre propio y margen inicial respecto de los bordes del área de trabajo. El menú radial busca espacio libre alrededor del personaje y se mantiene dentro de la pantalla.

La sombra es una copia sólida desplazada de la silueta, no una circunferencia. El globo conserva hasta seis líneas, retrato y espacio debajo del texto. Durante la captura aparece un indicador con nivel de audio. Las etiquetas se adaptan al idioma; los campos de conversación usan tipografía de lectura y soporte japonés. La tecla para hablar se captura al presionar la tecla o combinación deseada, con F8 como valor inicial.

La galería de aspectos utiliza vistas del sprite real. Los recursos de saludo y de mayor resolución se documentan en [PROMPT_SALUDO.md](PROMPT_SALUDO.md) y [PROMPT_HD.md](PROMPT_HD.md). Los materiales de terceros mantienen los derechos descritos en [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
