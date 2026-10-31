# Voz inglesa y continuidad de animación

## Voces en inglés

En Ajustes → Voz hay dos alternativas sintéticas adicionales: **Inglés vivaz · Ana** (`en-US-AnaNeural`, tono neutro) y **Inglés cálido · Jenny** (`en-US-JennyNeural`, +12 Hz). Son voces de catálogo de [Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts), no la voz oficial de la actriz ni una clonación del audio del anime. La similitud es subjetiva y se puede valorar con el botón de prueba de voz.

Se aplican al inglés con acento automático o estadounidense. En otros idiomas se conserva el comportamiento de Capri clásica y los acentos explícitos tienen prioridad. No se cambia automáticamente la voz guardada del usuario. El clip de referencia se examinó localmente; no se envió a un servicio de clonación ni se distribuye.

## Intro

Los vértices se proyectan por lotes con numpy y las primitivas de Tk se reutilizan entre cuadros. Las piezas que dejan de estar visibles se ocultan y se retiran de sus etiquetas activas; no se acumulan elementos nuevos en cada cuadro. Se mantiene el mismo arte, la aparición, el silencio y la transformación en el marco elegido con su chat.

Medición comparativa con 224 formas en Tk oculto a 1920 × 1080: mediana de dibujo de 20,39 a 10,55 ms; percentil 95 de 40,43 a 33,57 ms. Son tiempos de esa prueba, no una garantía de FPS al jugar o en otros equipos.

## Mano y telón

El recurso activo es `assets/mano-despedida-v3.json`: 43 puntos de control obtenidos de la nueva imagen de referencia del usuario. Las curvas se interpolan sin redondear la punta ni los cambios de ángulo deliberados. La mano se prepara a cuatro veces su resolución de pantalla y se reduce con LANCZOS para obtener bordes suaves; esa imagen se reutiliza durante la pose sostenida. La formación y la desintegración utilizan el mismo contorno. Se recuperan la posición y el rojo anteriores (`#f60031`).

Se regenera con `scripts/trazar_mano_despedida.py --imagen referencia.png`; requiere Pillow, numpy y OpenCV para generar los controles. El modo `--video` conserva el generador anterior. No se necesita OpenCV en Capri. El JSON v2 se mantiene como antecedente y ya no se usa para dibujar la mano.

Después de absorberse la mano y apagarse la luz, el cielo se recoge hacia arriba durante 0,65 segundos, como un telón. Solo entonces se cierra la ventana. La opción de omitir la despedida sigue cerrando directamente, sin reproducir voz ni telón.
