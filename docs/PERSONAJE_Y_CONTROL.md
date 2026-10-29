# Personaje de escritorio y control ampliado

## Una forma de Capri a la vez

Clic derecho sobre Capri → **Transformar en personaje**. En modo personaje aparece un menú circular; **Modo pantalla** permite volver. También se elige en **Ajustes → Forma de Capri**. Se conserva la elección; la pantalla sigue siendo el modo inicial de instalaciones nuevas.

El personaje conserva su pose de reposo y se desplaza únicamente mediante una descarga roja, sin caminar ni alternar pasos. Para subir a una ventana se convierte en energía roja y reaparece en una esquina del borde superior, con el cuerpo orientado hacia afuera para tapar menos contenido. Puedes arrastrarlo hasta ese borde. Sigue la ventana cuando se mueve; si se minimiza, desaparece o queda tapada, vuelve al escritorio. La detección usa la geometría de las ventanas de Windows, no el contenido de las pestañas del navegador. Necesita espacio suficiente encima de la ventana.

**Pausar desplazamientos** lo deja quieto. F8 y «Capri» siguen funcionando. Haz clic sobre el personaje para abrir una entrada flotante al lado; nunca se añade una barra debajo del cuerpo. Al enviar, pulsar Esc o perder el foco se oculta conservando el texto no enviado. Las respuestas normales desaparecen tres segundos después de terminar la voz o la escritura. Las confirmaciones de operaciones se mantienen mientras esperan tu respuesta, hasta su caducidad. El tamaño habitual también se aplica al personaje. Al transformar, el panel crece y se desplaza al centro, se convierte en la pose de bienvenida y se reduce hasta el personaje. La conversión de personaje a pantalla es directa y breve, sin la pose gigante en el centro. Los rayos acompañan la imagen.

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

Las aplicaciones instaladas se buscan en el menú Inicio y en los accesos directos de Inicio y Escritorio. «Abre League of Legends» o «abre LoL» utiliza su acceso directo para conservar los argumentos del lanzador de Riot. Requiere Control ampliado activo; no depende de que el modelo recuerde una lista de programas.

«Cierra Spotify» identifica el proceso de Spotify, aunque esté minimizado o su título sea una canción. Pide confirmación antes de terminar los procesos identificados y vuelve a comprobar su identidad. Esto termina la aplicación y puede perder trabajo sin guardar; para detener únicamente la música usa «pausa Spotify». El cierre de una ventana concreta sigue disponible por su título.

## Páginas, vídeos y música

- «Entra a YouTube», «métete a YouTube» y «abre Netflix» abren el sitio en Opera GX. Una dirección explícita como youtube.cl se respeta.
- «Busca Crunchyroll» o «busca Netflix» abre el sitio si la consulta es exactamente un nombre conocido. También se reconocen Disney+, Prime Video, Twitch, Wikipedia, GitHub, Reddit y Steam, además de direcciones explícitas. «Busca en Google Crunchyroll» o «busca opiniones de Crunchyroll» sigue siendo una búsqueda de Google; «busca cyberpunk en YouTube» busca dentro de YouTube. Una búsqueda web no se convierte en apertura de un programa instalado.
- «Pon un vídeo de cyberpunk en YouTube» abre resultados e intenta activar el primer enlace de vídeo disponible. «Siguiente vídeo», «pausa el vídeo» y «reanuda YouTube» usan controles accesibles de esa página. Tras hablar de YouTube, «siguiente» se refiere a YouTube; una orden explícita de Spotify cambia el contexto.
- Para pausar, continuar o pasar vídeo, primero se intenta la sesión multimedia de Windows de Opera: se exige que el título de esa sesión coincida con una ventana de YouTube, sin controlar Spotify ni otras sesiones por defecto. Si no hay una sesión inequívoca o no acepta la acción, se intenta el control accesible de la página, incluyendo botones con accesibilidad heredada. El vídeo debe haberse iniciado y la pestaña de YouTube debe estar seleccionada en Opera GX para identificarlo. No todos los vídeos ofrecen Anterior o Siguiente a Windows; varias páginas visibles pueden requerir elegir una. Los errores distinguen la sesión multimedia del control accesible, sin atribuir todo a que la pestaña no esté seleccionada.
- «Súbele el volumen a Spotify», «baja el volumen de Spotify un 20%», «pon el volumen de Spotify al 50%», «silencia Spotify» y «quita el silencio de Spotify» actúan sobre el **deslizador interno del cliente Spotify**. Sin cantidad, subir/bajar cambia diez puntos; los límites son 0–100. Identifica un único deslizador accesible de volumen en los procesos Spotify, distinto de la barra de progreso, y comprueba su valor después del cambio. No utiliza el mezclador de Windows ni modifica la voz de Capri. No activa la ventana ni envía teclas globales. Si Spotify no expone ese control, lo informa sin recurrir al mezclador. Para quitar el silencio recuerda el último nivel positivo leído en esta ejecución; si aún no lo conoce utiliza 50%.
- «Sube el volumen de YouTube», «baja el volumen del vídeo» y «pon el volumen de YouTube al 40%» controlan el **volumen del reproductor de YouTube**, sin cambiar el volumen de Opera ni del sistema. Si el tema activo es YouTube, «sube el volumen» también se refiere a ese reproductor. Acepta «pone el volumen…» del dictado. La vía preferida es la [extensión local de Opera](CONECTAR_OPERA.md): utiliza el controlador del reproductor de YouTube y verifica su estado y sus controles. Clic derecho sobre Capri → **Conectar YouTube con Opera** muestra los pasos y el estado. Requiere cargar la extensión una vez y recargar la pestaña; su preparación no significa que ya esté conectada. Sin esa conexión, el control accesible de Windows se conserva como alternativa, pero puede no estar disponible. No recurre al mezclador ni manda teclas a otras ventanas.

En YouTube, pedir un volumen **mayor que cero activa el sonido**, aunque el vídeo estuviera silenciado. Pedir cero lo silencia. La conexión directa sincroniza el controlador de YouTube, el vídeo y las etiquetas del reproductor. «Silencia el vídeo» y «quita el silencio de YouTube» también siguen disponibles. Recarga la extensión en Opera y la pestaña después de actualizarla. La alternativa de accesibilidad rechaza cambiar el nivel si detecta el reproductor silenciado, porque no puede garantizar esa sincronización.
- Las búsquedas de Spotify intentan primero enviar el texto literal, incluidos los espacios de «high forever», a sus controles accesibles en segundo plano. Si ese método falla en el escritorio, recuperan la apertura de búsqueda compatible con el cliente de Spotify y vuelven a intentar reproducir el resultado. Esta alternativa puede traer Spotify al frente. La URI usa `%20` para espacios y `%2B` para un signo `+` literal.
- Antes de esa alternativa se consulta el ejecutable y la geometría de la ventana activa: se bloquea si es un juego conocido (incluido LoL), si ocupa todo el monitor o si Windows no permite verificarlo. En ese caso Capri explica que la búsqueda por nombre necesita volver al escritorio. Esto no ofrece búsqueda universal en segundo plano; pausa, reanudar y siguiente canción siguen usando la sesión multimedia de Windows sin abrir la ventana.
- Las playlists se buscan en Tu biblioteca sin activar una URI; las vinculadas se identifican por su ID si el enlace está accesible. Necesitan que Spotify esté ejecutándose y exponga sus controles de biblioteca.

Estos controles locales no requieren una clave de API. La automatización de páginas depende de la interfaz accesible que expongan Opera y los sitios; no equivale a control universal de cualquier página.

## Permisos y confirmaciones

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

La caminata está desactivada. Los desplazamientos al suelo, a una ventana y a una nueva esquina se representan mediante el mismo tránsito de rayos. El glitch se recorta a la silueta del personaje y el alfa se vuelve binario para evitar bordes negros del color transparente de Windows.

Al transformar la pantalla en personaje aparece una [pose de bienvenida](PROMPT_SALUDO.md) grande. La secuencia de pantalla a personaje dura unos 2,7 segundos: primero se centra y crece, después cambia de forma y finalmente se encoge antes de acomodarse en el escritorio. Puede interrumpirse con Esc o F8. El atlas de ocho pasos permanece como recurso histórico, sin cargarse en la animación actual.


Se usó la **herramienta integrada de generación de imágenes**, con las capturas de cuerpo completo y pose sentada aportadas por el usuario como referencias. A continuación se conservan los prompts empleados.

### Generación del atlas

> Create a production-ready TRANSPARENT sprite sheet for a Windows desktop companion of Capri, the red-haired green-and-black angular digital female character shown in the supplied reference images. The reference images are character/pose references ONLY; do not include video UI, environments, window bars, or screenshots. Match her very specific enormous asymmetrical jagged lightning silhouette of hot red hair, small lime-green triangular face with a single visible geometric eye, extremely thin angular black body, red/pink geometric torso/legs and green accents, long sharp hands, purple outlines, one single white mouth with no teeth. Keep the same character model and proportions in ALL cells, full body never cropped. Anime cyberpunk cel-shaded flat geometric illustration with restrained digital grain. NOT a chibi, not rounded, not a human girl with conventional hair or clothes. One atlas with EXACTLY 3 equal columns and 2 equal rows, 6 independent sprites centered in their cell, broad transparent padding and absolutely no background, no labels, no borders, no ground shadows. Top-left standing idle facing 3/4 right, top-middle walking right step A left leg forward, top-right walking right step B right leg forward. Bottom-left sitting sideways on an invisible window edge with hips at 58 percent of cell height, one knee raised and the other long leg hanging down (same as seated reference, no ledge drawn). Bottom-middle same standing idle pose but mouth opened as one solid white shape for talking. Bottom-right same standing idle pose with the one eye closed for blinking. All standing poses have same head location and foot baseline at 90 percent cell height. Hair/body stay same size in every cell. Uniform sheet alignment is essential. Transparent RGBA background.

### Ajuste de transparencia

> Edit this exact 3-column 2-row sprite sheet. Preserve the SIX characters exactly, their size, alignment, poses, black body details, red hair, green eyes, purple outlines. Remove ALL background, ALL glows/halos/haze/ambient color behind them, ALL drop shadows. Make the space outside each precise character silhouette completely transparent alpha=0, including all space between hair spikes and between limbs. Character interior black shapes must remain opaque, NOT holes. Use sharp clean isolated sticker edges, no luminous bleed. No scene, no dark background, no gradient. Fix top hair and bottom feet so all six figures fit with a little transparent padding inside their own equal cell, with no overlap between rows. This is an RGBA cutout sprite sheet for a desktop app: only the characters have nonzero alpha. Do not add any text or grid.

## Referencias técnicas

Detección de ventanas: [Windows, ventanas de nivel superior](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-windows). Papelera: [implementación moderna de Send2Trash](https://github.com/arsenetar/send2trash/blob/master/send2trash/win/modern.py) y [opciones de IFileOperation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags).

## Menú circular y sombra

Clic derecho sobre el personaje abre ocho sectores: Ajustes, Chat, Juegos, Aspecto, Modo pantalla, Tamaño, Voz y Más. Los sectores con opciones abren otro círculo; pulsa el centro para volver. Esc, otro clic derecho o un clic fuera lo cierran. También se puede seleccionar con las flechas izquierda/derecha y Enter. Capri pausa sus desplazamientos mientras está abierto.

**Aspecto** permite elegir una sombra de contorno con cortes digitales: Violeta, Neón, Hielo, Rojo o Sin sombra. La elección se conserva. Es una copia coloreada de la silueta, desplazada hacia un lado y completa, sin cortes, que se dibuja detrás del cuerpo; no un contorno alrededor de toda la figura. No añade un fondo negro.

## Voz en modo personaje

Las respuestas aparecen en un globo violeta con retrato de Capri y una punta dirigida al personaje. La misma respuesta completa se conserva en el historial; el globo muestra hasta seis líneas y se ajusta a su contenido. La escritura sigue los eventos del reproductor de voz. La boca alterna entre cerrada y una figura blanca abierta, tanto de pie como sentada, usando la misma señal de audio del modo pantalla. No cambia el cuerpo al abrir la boca. Al terminar, el globo se oculta después de tres segundos; las confirmaciones siguen visibles mientras esperan respuesta.

Las descargas que acompañan la transformación quedan fuera de los límites de la imagen para no cruzar su rostro o boca.

## Fluidez y despedida

La preparación de los fotogramas se realiza en un trabajador de Pillow, con cola acotada. Tk recibe pequeños lotes de imágenes en el hilo de interfaz, de modo que la preparación no bloquea todos los eventos. Se reutiliza la caché completa al repetir la transformación; las tareas incompletas se cancelan al interrumpir o cerrar.

Al cerrar normalmente, Capri se transforma en una mano roja centrada, con la silueta de la referencia, que señala una estrella en la parte superior central. Después se descompone en un rayo rojo que viaja hacia esa luz y se consume en su brillo. La secuencia dura unos 2,6 segundos y termina cerrando el proceso. La mano y la estrella son formas vectoriales, por lo que se adaptan al monitor. F8, Esc con foco o una segunda solicitud de cierre permiten terminar de inmediato. Si desactivas las animaciones, el cierre es inmediato.
