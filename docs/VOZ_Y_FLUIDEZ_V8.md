# Voz inglesa y continuidad de animación

## Voces en inglés

En Ajustes → Voz hay dos alternativas sintéticas adicionales: **Inglés vivaz · Ana** (`en-US-AnaNeural`, tono neutro) y **Inglés cálido · Jenny** (`en-US-JennyNeural`, +12 Hz). Son voces de catálogo de [Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts), no la voz oficial de la actriz ni una clonación del audio del anime. La similitud es subjetiva y se puede valorar con el botón de prueba de voz.

Se aplican al inglés con acento automático o estadounidense. En otros idiomas se conserva el comportamiento de Capri clásica y los acentos explícitos tienen prioridad. No se cambia automáticamente la voz guardada del usuario. El clip de referencia se examinó localmente; no se envió a un servicio de clonación ni se distribuye.

## Intro

Los vértices se proyectan por lotes con numpy y las primitivas de Tk se reutilizan entre cuadros. Las piezas que dejan de estar visibles se ocultan y se retiran de sus etiquetas activas; no se acumulan elementos nuevos en cada cuadro. Se mantiene el mismo arte, la aparición, el silencio y la transformación en el marco elegido con su chat.

Medición comparativa con 224 formas en Tk oculto a 1920 × 1080: mediana de dibujo de 20,39 a 10,55 ms; percentil 95 de 40,43 a 33,57 ms. Son tiempos de esa prueba, no una garantía de FPS al jugar o en otros equipos.

## Cámara, mano y cierre

La cámara de despedida ocupa toda la pantalla. El atlas v9 conserva las proporciones de Capri aprobadas y afina su sonrisa en cuatro expresiones de 1672 × 941 píxeles. El efecto de cámara antigua conserva luminancia detallada y suaviza sólo crominancia, con color algo lavado, velo cálido, viñeta, trama, grano y oscilación leve del sensor. No se reduce a SD ni se comprime como JPEG. Un margen evita bordes vacíos durante la oscilación. Durante el traslado todavía se ve el escritorio; el cielo se prepara detrás de la cámara una vez que esta cubre la pantalla. Al terminar la frase y sostener la sonrisa, el fotograma completo, incluida la óptica, se contrae hasta la mano. Referencias y prompts: [PROMPTS_CAPRI_V13.md](PROMPTS_CAPRI_V13.md).

La deformación se prepara con Pillow en un hilo sin referencias a Tk, a 1280 píxeles mientras se distingue la cara, 960 en el tramo intermedio y 800 al estrecharse y quedar roja. Se amplía después a la resolución de la pantalla y se consume mediante una cola acotada a seis cuadros; las imágenes de Tk se crean únicamente en el hilo de la interfaz. Cerrar directamente cancela también esa preparación.

La intro usa `capri-intro-vector-v7.json`, un modelo completo generado por `scripts/generar_intro_unificada.py`, sin recortar ni empalmar mitades anteriores. La cara es pequeña frente al pelo y el torso es fino; mandíbula, cuello y tronco comparten un contorno y un eje. Los ojos, boca y pivote están declarados en el propio JSON. La aparición, el saludo mudo y la contracción al panel mantienen la misma secuencia.

La despedida conserva la coma en la síntesis y garantiza un mínimo de 0,52 segundos antes de «choom» usando las marcas de palabra. Sólo se añade el silencio que falta y se desplazan las marcas posteriores; la boca permanece quieta en la pausa. La voz de Windows usa una pausa explícita dentro del mismo audio. Este tratamiento se limita a las frases de despedida; no cambia el perfil de voz ni el ritmo del resto de los diálogos.

El recurso activo es `assets/mano-despedida-v3.json`: 43 puntos de control obtenidos de la nueva imagen de referencia del usuario. Las curvas se interpolan sin redondear la punta ni los cambios de ángulo deliberados. La mano se prepara a cuatro veces su resolución de pantalla y se reduce con LANCZOS para obtener bordes suaves; esa imagen se reutiliza durante la pose sostenida. La formación y la desintegración utilizan el mismo contorno. Se recuperan la posición y el rojo anteriores (`#f60031`).

Se regenera con `scripts/trazar_mano_despedida.py --imagen referencia.png`; requiere Pillow, numpy y OpenCV para generar los controles. El modo `--video` conserva el generador anterior. No se necesita OpenCV en Capri. El JSON v2 se mantiene como antecedente y ya no se usa para dibujar la mano.

Después de absorberse la mano y apagarse la luz, el cielo permanece inmóvil y se desvanece durante 0,95 segundos para revelar el escritorio. Solo entonces se cierra la ventana. La opción de omitir la despedida sigue cerrando directamente, sin reproducir voz ni animación.
