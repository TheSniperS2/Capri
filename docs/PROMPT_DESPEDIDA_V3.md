# Despedida: detalle, cámara y voz

Versión histórica. La despedida activa usa [gestos v4 y la voz habitual de Capri](PROMPTS_GESTOS_V4.md); el tratamiento de voz y el nombre opcional de esta versión se retiraron a petición del usuario.

Asset activo: `assets/capri-despedida-camara-v3.png`, generado mediante **imagegen integrado** como edición de la versión v2. La versión anterior se conserva.

Referencias directas: `capri-despedida-camara-v2.png` para identidad y `Pictures/Capri/images (6).jfif` del usuario para el encuadre, la iluminación, el cielo oscuro y la calidad de la grabación. Se retiró la ciudad iluminada y se añadieron planos secundarios, sombras, pequeñas marcas de superficie y colores lavados.

## Prompt exacto

Edit the first Capri farewell recording to be much closer in cinematography, background, camera quality, intimate facial framing and fine anime detail to the second reference (D's farewell recording). KEEP CAPRI AS CAPRI: asymmetric hot pink/red angular hair, narrow GREEN EYE BAND, BLACK lower face and chin, angular CLOSED cyan eyelids and a very fine white zigzag closed smile. Do not turn her into D or a human, do not add teeth. Use D reference for all filming choices: close head-and-neck shot at eye level, face centrally positioned and filling most of frame, more straight-on warm sincere relaxed farewell expression, shoulders mostly cropped out. Background MUST be the same kind as reference2: dark indigo/blue-gray cloudy night sky and shadowy indistinct rooftop silhouettes; NO city skyline, NO illuminated windows, NO skyscrapers, NO cyberpunk neon bokeh. Give Capri's geometric surfaces substantially richer anime cel detailing: secondary angular shadow planes, delicate contour lines, fine specular scratches on dark facets, restrained violet edge reflections, small imperfections like a hand-drawn anime frame. Preserve solid BLACK lower face and green band rather than human skin details. Match the photographed recording quality of reference2: pale lifted blacks, slightly washed highlights, muted red-pink color, warmer skin-equivalent green band lighting, subtle blue-gray camera cast, soft imperfect lens focus, fine film grain, compression texture, slight chromatic bleed, NOT clean vector art, NOT glossy 3D. The tone is tender, tired but reassuring, an intimate recorded goodbye rather than a mascot smile. Opaque rectangular 4:3 image, frame cuts top hair and bottom chest naturally. NO caption, NO subtitles, NO text, NO watermark, NO UI or frame. The app will add playback indicators.

El resultado original se conserva sin modificar como PNG. El visor lo encuadra a 4:3 en ejecución y superpone seis capas de grano de baja intensidad preparadas una vez, alternadas a 12 Hz. No se captura vídeo ni se usa una cámara real.

## Frase y voz

La frase pasa a «Cuídate mucho» y admite un nombre opcional en **Ajustes → Escritorio → Nombre en la despedida**. No se toma el nombre de la cuenta de Windows. Se localiza en español, inglés, portugués y japonés.

La base sintética de despedida sigue siendo la de Roman, pero ahora baja 38 Hz respecto a su perfil (en español, Dalia a −20 Hz; antes era +8 Hz). La velocidad temporal es el 82 % de la configurada y conserva la coma antes del nombre para que haya una pausa natural. Los diálogos normales no cambian.

`audio_despedida.py` procesa el sonido antes de guardarlo en la caché: caída y alargamiento progresivos del remate, banda de 100–5200 Hz, compresión suave, reflexión de 14 ms al 3,5 % y atenuación leve al terminar. La caché contiene ya el WAV procesado; al reproducirlo no vuelve a aplicar los efectos. Respeta el volumen del usuario y no usa el filtro de teléfono.

Es una dirección de voz sintética distinta, no una reproducción verificada del doblaje o de la actuación de la referencia. Se verifican sus propiedades de audio sin reproducir sonido durante el desarrollo.
