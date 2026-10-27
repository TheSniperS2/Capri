# Personaje de escritorio y control ampliado

## Una forma de Capri a la vez

Clic derecho sobre Capri → **Transformar en personaje**. El mismo menú permite volver a **Transformar en pantalla**. También se elige en **Ajustes → Forma de Capri**. Se conserva la elección; la pantalla sigue siendo el modo inicial de instalaciones nuevas.

El personaje camina con un ciclo de ocho pasos, aceleración gradual y posición actualizada por tiempo. Para subir a una ventana se convierte en energía roja y reaparece en una esquina del borde superior, con el cuerpo orientado hacia afuera para tapar menos contenido. Puedes arrastrarlo hasta ese borde. Sigue la ventana cuando se mueve; si se minimiza, desaparece o queda tapada, vuelve al escritorio. La detección usa la geometría de las ventanas de Windows, no el contenido de las pestañas del navegador. Necesita espacio suficiente encima de la ventana.

**Pausar paseo** lo deja quieto. F8 y «Capri» siguen funcionando. Haz clic sobre el personaje para abrir una entrada flotante al lado; nunca se añade una barra debajo del cuerpo. Al enviar, pulsar Esc o perder el foco se oculta conservando el texto no enviado. Las respuestas normales desaparecen tres segundos después de terminar la voz o la escritura. Las confirmaciones de operaciones se mantienen mientras esperan tu respuesta, hasta su caducidad. El tamaño habitual también se aplica al personaje. Cambiar entre personaje y pantalla utiliza la misma estela roja del arranque.

## Jugar con Capri

En **clic derecho → Jugar con Capri**:

- **Jugar a atrápame:** toca a Capri tres veces; después de cada acierto escapa a otra esquina con una descarga.
- **Asomarse por una esquina:** aparece parcialmente desde la esquina inferior y vuelve con una estela.
- **Travesura ahora:** elige una aparición o un salto.

También puedes decir «Capri, juega conmigo», «asómate por una esquina», «haz una travesura» o «deja de jugar» con el modo personaje activo. Dejar de jugar desactiva las travesuras automáticas.

En Ajustes puedes activar **Travesuras suaves y apariciones ocasionales**, apagado de fábrica. Solo ocurren cuando Capri está disponible; se pausan durante conversaciones, escritura, confirmaciones y ajustes. Esc interrumpe el juego actual.

La opción separada **Permitir que el juego abra una pestaña o Documentos**, también apagada de fábrica, autoriza una pestaña vacía en Opera GX o la carpeta Documentos. Tiene un intervalo mínimo de cinco minutos entre aperturas. No cambia archivos. Estas acciones básicas del juego no dependen del permiso de control ampliado, que se configura por separado.

Ideas para ampliar después: un escondite por las esquinas, un destello sorpresa de un segundo con cuenta atrás y volumen elegido, una búsqueda del tesoro con pistas en una pestaña local y pequeñas carreras siguiendo el cursor. Los sustos con sonido no están activados ni implementados en esta versión.

## Control ampliado, opcional

En **Ajustes**, activa **Control ampliado del computador**. Está apagado por defecto y desactivarlo cancela cualquier confirmación pendiente. Trabaja con los permisos de tu cuenta de Windows; no solicita elevación a administrador. Requiere la IA local activa para interpretar las peticiones nuevas.

Permite buscar, listar, abrir y leer archivos de texto, crear carpetas, mover o renombrar archivos individuales, enviarlos a la Papelera, consultar aplicaciones instaladas y abrirlas, y listar, minimizar, maximizar o solicitar el cierre de ventanas. También permite pedir apagado o reinicio con confirmación y una espera de 60 segundos. «Cancela el apagado» solicita a Windows cancelar esa cuenta atrás.

Ejemplos:

- «Busca el archivo vacaciones.png».
- «Borra el archivo foto.png» o «elimina el archivo seleccionado», con un solo archivo seleccionado en el Explorador.
- «Renombra foto.png a viaje.png».
- «Minimiza la ventana Bloc de notas».
- «Abre Blender» si está instalado.

Para operaciones que cambian archivos, Capri muestra la ruta concreta y pregunta de nuevo. Responde **«sí, confirmo»** o **«cancelar»**. Esc también cancela. La confirmación dura dos minutos y sirve una sola vez. Otra petición la invalida. Si cambió el archivo, la ventana o el destino, solicita la operación de nuevo. Los homónimos no se eligen automáticamente: facilita la ruta completa si hay varias coincidencias.

Los archivos borrados se envían mediante la Papelera de Windows, utilizando el backend moderno de Send2Trash. No se ofrece borrado permanente ni borrado masivo de carpetas. Los destinos existentes no se sobrescriben. Abrir archivos se limita a formatos de documentos y medios; los programas se abren por su nombre instalado. Las operaciones se implementan como acciones fijas: el modelo no escribe ni ejecuta scripts o comandos de consola.

Las búsquedas se limitan a las carpetas personales habituales, con un límite de tiempo y resultados para mantener la respuesta ágil. Una ruta completa puede señalar otro archivo accesible por tu cuenta. La lectura de texto se limita a 100 KB y muestra hasta 6000 caracteres. Si la voz natural está activa, lo que Capri lee en voz alta utiliza el mismo servicio de voz configurado para el resto de respuestas.

## Arte y generación

Atlas: `assets/capri-personaje-v1.png`, RGBA, 1536 × 1024, tres columnas y dos filas. Orden: reposo, paso A, paso B, sentada, hablando y parpadeo. Se recorta y escala dentro de la aplicación; no se sustituye el arte del modo pantalla. La transparencia del atlas conserva la silueta negra y los huecos entre pelo y extremidades.

El ciclo de paseo usa además `assets/capri-caminar-v1.png`, RGBA, 1774 × 887, cuatro columnas y dos filas. Sus ocho poses se preparan y registran en una caché; no se generan imágenes ni se interpola con desenfoque durante el movimiento. El lienzo del personaje mide 210 × 240 antes del zoom, con márgenes transparentes para los pasos largos.

El [prompt de generación de los ocho pasos](PROMPT_CAMINAR.md) se conserva junto a esta guía. Se usó la herramienta integrada de generación de imágenes.

Se usó la **herramienta integrada de generación de imágenes**, con las capturas de cuerpo completo y pose sentada aportadas por el usuario como referencias. A continuación se conservan los prompts empleados.

### Generación del atlas

> Create a production-ready TRANSPARENT sprite sheet for a Windows desktop companion of Capri, the red-haired green-and-black angular digital female character shown in the supplied reference images. The reference images are character/pose references ONLY; do not include video UI, environments, window bars, or screenshots. Match her very specific enormous asymmetrical jagged lightning silhouette of hot red hair, small lime-green triangular face with a single visible geometric eye, extremely thin angular black body, red/pink geometric torso/legs and green accents, long sharp hands, purple outlines, one single white mouth with no teeth. Keep the same character model and proportions in ALL cells, full body never cropped. Anime cyberpunk cel-shaded flat geometric illustration with restrained digital grain. NOT a chibi, not rounded, not a human girl with conventional hair or clothes. One atlas with EXACTLY 3 equal columns and 2 equal rows, 6 independent sprites centered in their cell, broad transparent padding and absolutely no background, no labels, no borders, no ground shadows. Top-left standing idle facing 3/4 right, top-middle walking right step A left leg forward, top-right walking right step B right leg forward. Bottom-left sitting sideways on an invisible window edge with hips at 58 percent of cell height, one knee raised and the other long leg hanging down (same as seated reference, no ledge drawn). Bottom-middle same standing idle pose but mouth opened as one solid white shape for talking. Bottom-right same standing idle pose with the one eye closed for blinking. All standing poses have same head location and foot baseline at 90 percent cell height. Hair/body stay same size in every cell. Uniform sheet alignment is essential. Transparent RGBA background.

### Ajuste de transparencia

> Edit this exact 3-column 2-row sprite sheet. Preserve the SIX characters exactly, their size, alignment, poses, black body details, red hair, green eyes, purple outlines. Remove ALL background, ALL glows/halos/haze/ambient color behind them, ALL drop shadows. Make the space outside each precise character silhouette completely transparent alpha=0, including all space between hair spikes and between limbs. Character interior black shapes must remain opaque, NOT holes. Use sharp clean isolated sticker edges, no luminous bleed. No scene, no dark background, no gradient. Fix top hair and bottom feet so all six figures fit with a little transparent padding inside their own equal cell, with no overlap between rows. This is an RGBA cutout sprite sheet for a desktop app: only the characters have nonzero alpha. Do not add any text or grid.

## Referencias técnicas

Detección de ventanas: [Windows, ventanas de nivel superior](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-windows). Papelera: [implementación moderna de Send2Trash](https://github.com/arsenetar/send2trash/blob/master/send2trash/win/modern.py) y [opciones de IFileOperation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags).
