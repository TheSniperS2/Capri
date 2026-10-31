# Intro unificada, sonrisa y cámara antigua (v13)

Arte de despedida: `assets/capri-despedida-expresiones-v9.png`, atlas de 3344 × 1882. Cuatro imágenes de 1672 × 941, editadas con imagegen integrado a partir del retrato aprobado de v12. La primera imagen tenía 1671 píxeles de ancho y se uniformó a 1672 al empaquetar el atlas. La sonrisa es más estrecha y menos dentada. Los originales se conservan; no se presenta como arte oficial ni como 4K nativo.

Intro: `assets/capri-intro-vector-v7.json`, generado por `scripts/generar_intro_unificada.py` con la biblioteca estándar. El modelo se dibuja completo en un solo sistema de coordenadas. Cara, mandíbula, cuello y tronco forman una superficie continua; los brazos solapan sus raíces. Se eliminan el recorte horizontal y el empalme de cabeza/cuerpo de los modelos previos. Pelo monumental, máscara pequeña, torso fino y acentos verdes/magenta, sin las antiguas solapas blancas. Ojos, boca y pivote se declaran en el JSON y se animan con la misma proyección. Se mantienen aparición muda, saludo y contracción al panel.

La referencia de cámara es el clip local aportado por el usuario. Se simula una señal de vídeo antigua, sin abrir cámara real: detalle de luminancia conservado, crominancia ligeramente suavizada, contraste y saturación algo menores, velo cálido, viñeta, trama y grano. Un margen de sensor permite que el encuadre oscile unos píxeles sin mostrar bordes vacíos; se añade un pequeño indicador REC. El fotograma que se transforma en la mano se recorta de nuevo al tamaño de pantalla e incluye la óptica. La voz y la pausa de 0,52 segundos antes de choom se conservan.

## Prompts de las ediciones

### Sonrisa fina

```text
Precise LOCAL MOUTH edit of the provided single Capri portrait. Preserve EXACTLY every pixel outside the small mouth region: huge speckled magenta hair, tiny black triangular face, green mask, circular blue eyes, pose, neck, body, blue night sky, native image dimensions. Replace the current chunky white three-tooth staircase triangle with a much gentler, thinner affectionate WHITE ANGULAR SMILE. It is a narrow asymmetrical wedge, softly upswept at the right corner, only ONE small subtle angular notch along its upper edge, NO repeated teeth, NO sawtooth staircase, NO giant solid white triangular hole. Mouth height about HALF its current height, width similar, remains fully inside the same black face area. Capri is saying a calm fond goodbye, not grinning aggressively. No lips, no nose, no human anatomy. Exactly one crisp cel-anime image, no grid, no atlas, no text, no baked camera effects. Keep everything else pixel-identical as far as possible.
```

### Mirada inicial

```text
Edit only the GAZE in this single Capri image. Keep the newly delicate thin white smile EXACTLY unchanged. Move blue irises and white pupils a little upward inside the same black eye sockets, looking at a star above her. Preserve exactly all other pixels, hair texture and silhouette, tiny face proportions, head pose, neck, shoulder, body, background and image dimensions. No redesign, no new teeth, no head motion, no text, no atlas, no camera effects. Single crisp cel anime frame.
```

### Habla

```text
Precisely edit ONLY the mouth in this Capri image into the speaking variant of the same delicate smile. Preserve all pixels outside the mouth, all hair texture/shape, tiny face, green mask, circular blue ring eyes with white pupils, neck/body and night sky. The mouth is a SMALL open angular smile: thin white upper smile wedge with a single subtle notch, a little BLACK interior beneath it and a very small white lower edge. Slightly taller than the current thin closed smile, not a solid white triangle, not a staircase of teeth, no human lips. Friendly and understated, as she softly says goodbye. Single same-size HD image, no text, atlas or camera effects.
```

### Corrección del interior de boca

```text
Make one microscopic correction in the MOUTH ONLY: remove the small reddish tongue-like patch inside Capri's speaking mouth and replace it with flat BLACK matching her face. Keep the thin white upper smile edge and the tiny white lower edge. Her mouth has only black and white geometric shapes; NO red tongue, no flesh, no lips, no teeth staircase. Everything outside that tiny red tongue patch must stay unchanged: same eyes, mask, hair and its texture, pose, small face, body, sky, dimensions. Single same-size image, no atlas or text.
```

### Sonrisa final

```text
Precisely edit ONLY both eyes of this single Capri image to happy closed GREEN CRESCENT eyelids within the same black eye sockets, as she smiles fondly goodbye. Preserve EXACTLY the current delicate thin white smile: no new teeth or larger mouth. Keep all other pixels, image dimensions, enormous speckled magenta hair, tiny face and mask, neck, shoulder, body and night sky unchanged. No head shift, no new features, no text, no atlas, no camera effects.
```
