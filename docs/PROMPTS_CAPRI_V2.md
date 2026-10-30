# Capri: asomo tierno y grabación de despedida

Versión histórica. El asomo y la despedida activos se describen en [pelo, ojos y gestos v4](PROMPTS_GESTOS_V4.md).

Modo: imagegen integrado. Las versiones anteriores quedan conservadas; el runtime usa estos nuevos assets:

- `assets/capri-asomo-tierno-v2.png`: RGBA 1448 × 1086, transparente.
- `assets/capri-despedida-camara-v2.png`: plano rectangular 1448 × 1086, con fondo.

## Referencias consultadas

Se revisaron los fotogramas aportados por el usuario en `Pictures/Capri`, el retrato original usado por Capri y cuatro secuencias adicionales de la serie publicadas en Tenor:

- [Capri frente a cámara y gestos de manos](https://tenor.com/view/cyberpunk-cyberpunk-edgerunners-cyberpunk-2077-capri-capricorn-gif-8624623317979628493).
- [Mano junto al rostro](https://tenor.com/view/capri-cyberpunk-cyberpunk-edgerunners-cyberpunk-2077-gif-6524549678632533851).
- [Rostro y silueta en distintas orientaciones](https://tenor.com/view/capri-cyberpunk2-cyberpunk-2-edgerunners-2-cyberpunk-edgerunners-2-capricorn-gif-5541033963201170705).
- [Primer plano de ojos](https://tenor.com/view/cyberpunk-capri-cyberpunk-capri-edgerunners-2-edgerunners-2-gif-5774155399214368565).

Rasgos que se conservaron: enorme cabello asimétrico rojo/rosa, flequillo diagonal, parte inferior de la cara negra, franja verde en los ojos, círculos azules/cian y boca blanca fina en zigzag. Se retiraron los dientes, la cara completamente verde y el cuello de chaqueta inventados en la primera propuesta. Las capturas de D aportadas por el usuario se usaron solo para el encuadre cercano y la expresión tranquila de despedida.

## Prompt exacto: asomo

Create a transparent PNG desktop peeking sprite of CAPRI from Cyberpunk Edgerunners 2, strictly on-model to these identity references, not a redesign. Capri is an abstract sharp geometric digital woman: enormous asymmetric hot red/pink angular hair mass, very long diagonal fringe over one side, BLACK lower face/chin, a NARROW horizontal neon GREEN eye-band, BLACK angular eye sockets, cyan/blue concentric circular eyes with small WHITE centers, fine WHITE CLOSED zigzag-line mouth (NO teeth, NO fangs, no open mouth). Black angular body with small green/red geometric patches and thin violet contour accents, NOT a human green face, NOT a jacket collar, no eyelashes, no nose, no blush. Make her CUTE through shy curious head tilt and large round inquisitive ringed eyes, relaxed small zigzag smile. She peeks upward over the bottom edge of the canvas, both small BLACK geometric hands with neon green accents gently resting on that edge, head and hair above hands, lower torso hidden outside frame. Keep asymmetry and simple flat shapes from the references. Frontal enough that both blue eye rings remain visible. Transparent surrounding background, clean flat anime cel graphic, no text, no icons, no UI, no frame, no watermark. Complete hair inside top and sides, bottom cuts off torso. About 4:3 landscape composition, one character only.

Entradas: fotograma 0 de la primera secuencia de Tenor y `assets/capri-base-hd-v1.png` como identidad.

## Prompt exacto: despedida

Generate a 4:3 CAMERA RECORDING STILL of Capri from Cyberpunk Edgerunners 2 giving a bittersweet farewell to the person filming. References 1 and 2 are STRICT Capri character identity; reference 3 (blue-haired D smiling into camera) is ONLY the close-up framing, emotional delivery and relaxed eyes-closed smile, do NOT copy D's appearance. Capri must keep her original abstract angular design: vast asymmetric bright pink-red jagged hair with long diagonal fringe covering one side; BLACK lower face and pointed chin; NARROW NEON GREEN HORIZONTAL BAND around eyes; black geometric eye sockets. Eyes are softly CLOSED angular cyan curves within the black sockets, mouth a single thin WHITE CLOSED zigzag smiling line on the BLACK lower face. NO human green skin, NO teeth, NO fangs, NO nose, NO rosy cheeks, NO eyelash embellishments, NO cartoon jacket collar. Black angular upper body with original neon red/green fragments and thin violet accents. She looks tender and calm, head inclined slightly, shoulders relaxed, a close-up as if leaning toward Roman's camera saying goodbye. Frame crops hair at top and shoulders at bottom, matching D's intimate recorded farewell reference. Background is a dim indistinct blue-gray Night City rooftop at dusk, subdued. Flat graphic anime cels faithful to the references, lightly washed analog camera colors and subtle photographic grain; still sharply identifiable. NO REC text, NO UI, NO subtitles, NO logos or watermark (these will be drawn by app). This is one opaque rectangular filmed scene, NOT a floating sticker or an avatar icon.

Entradas: las dos anteriores y `Pictures/Capri/images (5).jfif` como expresión/encuadre de D.

## Uso en la aplicación

El asomo conserva el recorte contra el borde, el arrastre para desprenderlo y el seguimiento de ojos. Sus núcleos blancos se localizaron en (683,19; 727,14) y (949,93; 655,75) sobre el PNG de 1448 × 1086; el renderer transforma esas coordenadas con la pose.

La despedida reutiliza el traslado eléctrico y las teselas del personaje durante 1,1 segundos hasta el centro. Después muestra un visor de reproducción 4:3 con marcas de encuadre, tiempo y frase localizada. La voz empieza después de llegar. Es una ilustración con tratamiento de cámara: no se accede a una cámara real ni se graba al usuario. La mano y la estrella mantienen sus trazos originales.

La interpretación temporal `despedida_roman` toma la base sintética del perfil invitado Roman, baja su tono 10 Hz y reproduce la frase al 86 % de la velocidad configurada. No modifica las preferencias de Capri ni usa audio del doblaje. Es una aproximación de registro y ritmo; no una reproducción verificada de la actuación oficial.
