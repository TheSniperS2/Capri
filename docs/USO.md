# Capri

Abre **Abrir Capri.pyw**. La primera apertura instala sus dependencias en una carpeta propia, descarga Whisper base multilingüe (148 MB), el reconocimiento rápido de respaldo y las referencias de Capri. Verás el avance; necesita internet para esa preparación. Al actualizar conserva tu micrófono y los modelos de conversación ya descargados.

Después aparece una ventana flotante con la imagen del personaje. Arrástrala para moverla. Haz clic para abrir el chat. Pulsa **F8** o **Hablar** para dictar una frase; haz una pausa para que responda. Pulsa **Esc** para detener la voz. El menú del botón derecho permite salir. Se crea un acceso directo **Capri** en el escritorio; también puedes abrir otra vez el lanzador original.

También puedes decir **«Capri»** y dar la orden, o decir **«Capri, busca memes de Cyberpunk»** en una misma frase, sin esperar un aviso. Se conserva la misma captura desde el nombre hasta terminar la orden, aunque el reconocedor la divida en varios segmentos. Si dices solo «Capri», espera hasta seis segundos de silencio por la instrucción sin cerrar ni volver a abrir el micrófono. Después de la orden espera aproximadamente 0,85 segundos de silencio antes de transcribir. La activación está habilitada al abrir normalmente la aplicación; usa el micrófono seleccionado y el modelo Vosk local ya instalado. Whisper transcribe el audio completo al terminar si elegiste Mixto. La escucha mantiene solo un fragmento temporal en memoria, sin archivos ni envío de audio. Se pausa mientras Capri habla y mientras están abiertos los Ajustes, y se reanuda automáticamente. Durante su voz, usa Hablar o F8 para interrumpir. Puedes desactivar **Ajustes → Activar al decir «Capri»**. La detección depende del ruido y de la pronunciación; no es una garantía de reconocimiento en cualquier ambiente.

En **Ajustes → Micrófono** puedes elegir la entrada de audio que quieres usar. La selección se guarda para las próximas aperturas. Si conectas otro micrófono, pulsa **Actualizar**. La lista oculta las repeticiones de un dispositivo que Windows ofrece mediante varias interfaces de audio. «Predeterminado de Windows» es una opción automática, no un micrófono adicional. Si el elegido se desconecta, Capri avisa en lugar de cambiar automáticamente al micrófono de los audífonos.

La captura se inicializa en un hilo de audio propio de Windows. Evita WDM-KS y, si una interfaz falla, intenta otras variantes inequívocas del mismo micrófono. Si no logra abrirlo, `diagnostico-microfono.json` contiene los intentos y los errores del controlador, sin grabaciones ni texto reconocido.

**Ajustes → Reconocimiento de voz** permite elegir **Whisper · español y nombres en inglés** o **Rápido · Vosk español**. Whisper usa el modelo multilingüe instalado con español fijado para evitar que frases breves se interpreten como italiano u otro idioma. Conserva nombres de aplicaciones y canciones en inglés y aporta Spotify, YouTube y Opera GX para favorecer su reconocimiento sin traducirlos. Este perfil está pensado para hablar en español. Al abrir aplicaciones también acepta variantes de pronunciación como «espotifai». Whisper hace una pausa breve al detectar el final de la frase y después la transcribe. Si el resultado es dudoso, aparece en el cuadro de texto para revisarlo antes de enviarlo. La precisión real depende del ruido y del micrófono. Su primera carga tarda más; el modelo queda en memoria para las siguientes frases.

Prueba: «abre una pestaña en Opera GX», «puedes abrirme una pestaña», «me gustaría que abrieras una pestaña del Opera GX», «abre una pestaña y busca recetas de pasta», «abre la calculadora», «abre Spotify», «habla más rápido» o «qué hora es».

Las búsquedas admiten, por ejemplo, «búscame memes de Cyberpunk», «puedes buscarme memes de Cyberpunk», «quiero que busques memes de Cyberpunk» y «haz una búsqueda de memes de Cyberpunk». Abren la consulta en Opera GX. También puedes pedir «abre mis archivos», «abre Descargas», «abre Documentos», «abre Imágenes» o «abre el Escritorio»; las carpetas respetan las ubicaciones configuradas en Windows.

Para Spotify: **«reproduce la música»**, **«reanuda la canción»** y **«pon la música»** reanudan la sesión actual, sin buscar otra canción ni cambiar la cola. **«Salta la canción»**, **«pon la siguiente canción de la playlist»** y **«podrías poner la música siguiente»** pasan a la siguiente pista de la cola actual; **«pon la canción anterior»** vuelve a la anterior. **«Pausa Spotify»** pausa esa sesión. **«Qué canción está sonando»** consulta el título y estado que comunica Spotify. Estos controles usan la sesión multimedia de Windows de Spotify, sin abrir páginas ni buscar canciones. Si Spotify no comunica una sesión o rechaza una orden, Capri lo indica. El modelo de charla no afirma qué está sonando basándose en sus propias respuestas.

Para elegir otra canción: «busca Never Fade Away en Spotify» o «reproduce Never Fade Away en Spotify». La búsqueda usa la aplicación instalada. Para reproducir un título concreto, Capri intenta invocar un control accesible cuyo nombre coincida con la búsqueda. Necesita una sesión iniciada y controles accesibles en Spotify. No pulsa coordenadas ni envía teclas a otra ventana. Si no puede confirmar el control, mantiene abierta la búsqueda y lo informa.

Para playlists: **«pon mi playlist Cyberpunk»** intenta encontrarla en **Tu biblioteca**, sin buscarla entre playlists públicas. Si Spotify no expone la biblioteca mediante controles accesibles, usa **Ajustes → Vincular playlist de Spotify**: introduce el nombre y pega su enlace. Puede seguir siendo privada; debe ser accesible desde tu cuenta iniciada. Se guarda solo el nombre y el identificador de playlist en `playlists.json`, sin contraseña ni tokens. Una vez vinculada, también admite «pon Cyberpunk». No hace públicas listas ni cambia permisos. Si abre una playlist pero no puede confirmar su reproducción, lo informa. La reproducción real y el acceso a la biblioteca no han podido verificarse desde el entorno restringido de desarrollo.

El nombre del navegador se detecta automáticamente, con preferencia por Opera GX. Las búsquedas se abren como una pestaña de Google; la aplicación no lee ni resume sus resultados. Solo abre las aplicaciones que tiene registradas.

Las órdenes reconocidas de pestañas, páginas y aplicaciones van al ejecutor del programa, sin pedir al modelo que las describa. Una pestaña nueva sin destino usa una página en blanco. Las acciones de computador que todavía no estén implementadas muestran un aviso. Las preguntas sobre cómo hacer algo siguen siendo conversación.

Las aperturas toleran errores pequeños de transcripción en el comienzo de la petición, como «Podríes avrir Spotify»: corrigen una letra omitida, cambiada o intercambiada si el destino es una aplicación conocida. La corrección no cambia el texto de búsquedas ni convierte frases negadas o explicaciones en órdenes. La conversación conoce las capacidades reales del ejecutor y corrige negativas globales falsas sobre abrir Spotify o aplicaciones; no presenta una acción como realizada si no pasó por el ejecutor. Esto mejora la interpretación de la frase recibida, sin garantizar que el reconocimiento de voz transcriba todas las palabras correctamente.

Para conversación libre: **Ajustes → Activar IA local → Descargar y activar**. Se descargan Ollama y llama3.2:3b (aprox. 2 GB de modelo, más el instalador). Después conversa sin pago por uso. Si ya tienes Ollama con un modelo, se usa automáticamente. No se ejecuta código propuesto por la IA.

Con la IA local activada, las peticiones que no se reconocen directamente pasan a un intérprete de intención. Puedes decir «¿podrías dejar la música en pausa un ratito?», «detenla un momento», «pon otra» o «prefiero la de antes». Tras pausar Spotify, «ahora sigue» usa ese contexto para reanudar. Si no hay un referente claro, Capri pregunta a qué te refieres. Los agradecimientos conservan el tema; una conversación sobre otro asunto lo cambia. El intérprete conserva hasta cuatro turnos durante tres minutos, solo en memoria, con el resultado real del ejecutor. No supone que una acción fallida se completó. Al cerrar la aplicación ese contexto desaparece.

El modelo interpreta una acción por turno entre las capacidades existentes; no genera ni ejecuta comandos de consola. La interpretación local puede tardar más durante la primera carga. Esto amplía la comprensión de peticiones y referencias, sin garantizar que cualquier frase o transcripción de voz sea entendida correctamente.

El micrófono se reconoce localmente. El audio permanece en memoria y no se graba en archivos. La voz natural de respuesta usa Microsoft Edge TTS y requiere internet: se envía el texto a sintetizar. Se puede desactivar en Ajustes para usar la voz de Windows. El perfil Capri usa una voz sintética femenina en español latino con ritmo y tono más enérgicos; no reproduce el timbre exacto de la actriz. La memoria del chat dura solo mientras la aplicación está abierta.

La velocidad inicial es **1×**, normal, tanto en la voz natural como en la voz de Windows. Para una lectura más fluida, el texto hablado omite marcas de formato y reduce las pausas de comas, dos puntos y punto y coma; conserva puntos y preguntas. La velocidad se cambia en **Ajustes → Velocidad de voz**, o con «habla más rápido», «lee más lento» y «habla a velocidad normal». La elección se guarda.

La identidad se fija como **Capri** en cada petición y las presentaciones sencillas responden directamente. El texto aparece mientras se genera; la respuesta se narra completa en una sola lectura para evitar esperas entre audios separados de cada frase. **Hablar o F8 interrumpen la voz y la respuesta pendiente antes de activar el micrófono**, incluso si todavía estaba preparando el audio. Se mantiene el modelo local cargado durante 15 minutos y se limita la longitud normal de las respuestas para reducir la espera. La primera carga del modelo, el uso de la GPU por otros programas y la conexión de la voz natural influyen en la demora.

Los archivos instalados quedan en **%LOCALAPPDATA%\Capri**. Allí están ajustes.json (sin claves), modelos/ y assets/. Capri no se añade al inicio automático de Windows. No requiere permisos de administrador.

El icono de las ventanas y del acceso directo del escritorio usa la referencia de Capri incluida en la aplicación, convertida a un icono de Windows con varios tamaños. No se modifica su rostro. Windows puede conservar temporalmente en caché el icono anterior de un acceso anclado a la barra de tareas; desanclar ese acceso antiguo y anclar de nuevo el acceso Capri actual permite actualizarlo.

## Elegir modelos

En Ajustes puedes seleccionar el modelo de conversación instalado en Ollama. Se utiliza tanto para conversar como para interpretar peticiones con contexto. El selector muestra únicamente modelos locales instalados; cambiarlo no borra los anteriores. La primera carga del modelo seleccionado puede tardar más. «Activar IA local» conserva el modelo que hayas elegido.

Debajo del modo de reconocimiento puedes elegir **Whisper base** o **Whisper small** si están instalados. Small es más pesado y puede aumentar la espera, especialmente en CPU; Base permite volver a una respuesta más rápida. El cambio se aplica a las siguientes capturas. Si falta el modelo seleccionado, se usa uno instalado; Vosk se conserva como respaldo. La primera instalación sigue descargando Base, y los pesos no se incluyen en el ZIP.

Para preparar Small desde el código fuente: `python src/preparar_whisper.py RUTA_DE_MODELOS small`. Se descarga a una carpeta independiente, sin sustituir Base. Este paso necesita internet; después el reconocimiento funciona localmente.

## Apariencia y procedencia

La aplicación muestra las referencias publicadas de Capri y conserva sus rasgos. Anima la flotación, las partículas y el cambio de imagen al hablar. Esta primera versión no tiene un cuerpo 3D ni animación labial del anime.

Referencias del personaje: https://mudae.net/character/3127100/Capri%20%7BCP%7D

Capri y las imágenes de la serie pertenecen a sus respectivos titulares. Aplicación de aficionado para uso personal, no oficial. El avatar usa una imagen base de la galería indicada en ARTE_ANIMADO.md y las referencias adicionales se descargan desde esa galería; no se incluyen episodios ni se modifican archivos del juego.

Vosk y modelos: https://alphacephei.com/vosk/models

Whisper base: https://huggingface.co/Systran/faster-whisper-base

Faster Whisper: https://github.com/SYSTRAN/faster-whisper

Ollama: https://ollama.com/

Edge TTS: https://github.com/rany2/edge-tts

## Estado de verificación

El dictado usa búsqueda de cinco candidatos y contexto de órdenes musicales, conservando los nombres ingleses. Las transcripciones «revoluces la canción» y «ciente canción» se interpretan como reanudar y siguiente únicamente cuando forman una orden completa; no se sustituyen palabras dentro de búsquedas, títulos o negaciones. Esto mejora la interpretación de esos errores conocidos y no garantiza una transcripción perfecta.

El nombre con que vinculas una playlist puede ser un alias. Para reproducirla, Capri busca el botón con el título real dentro de la página de esa playlist, aunque el título use emojis. La confirmación requiere el botón de pausa de esa misma playlist; el botón de pausa general no sirve como prueba. Si Spotify no expone esos controles, Capri informa que no pudo confirmar la reproducción.

En **Ajustes → Volumen de Capri** puedes elegir de 0 a 100%. Se guarda para las siguientes respuestas, tanto con voz natural como con la voz de Windows; 0% la silencia. El control no modifica el volumen de Spotify ni el volumen general del equipo.

Puedes decir «Capri abre Spotify» seguido, sin esperar una señal. El aviso de escucha aparece en cuanto el reconocedor libre detecta el nombre, sin esperar a terminar la frase. Ese aviso todavía no autoriza ejecutar nada: en modo Whisper, el dictado del audio original debe confirmar «Capri» al principio antes de enviar la orden. Vosk puede proponer la confusión «Capriles» para esa comprobación, pero esa palabra nunca autoriza una orden por sí sola. Si Whisper no confirma «Capri», la frase se descarta. En modo Rápido, sin esa comprobación independiente, se exige el nombre exacto en el resultado final de Vosk. Se conserva una única captura y un margen breve de audio para no perder el principio de una orden rápida. F8 y Hablar son activación manual y no requieren decir el nombre. La precisión con voz real depende del micrófono y del ambiente.

La activación aplica una ganancia limitada al audio de voz bajo antes de enviarlo a Vosk y usa un umbral más bajo para captar frases suaves. No cambia el volumen del micrófono en Windows. La ganancia no amplifica el silencio, está limitada a tres veces y evita saturar los picos; la captura original se conserva para Whisper. La detección del nombre todavía depende del micrófono, el ruido y la pronunciación.

Al activar por nombre, la barra muestra el nivel del micrófono durante la captura. El detector de voz local incluido con Whisper distingue habla de ruido continuo para cerrar tras aproximadamente un segundo sin voz; si no está disponible, se usa el umbral de volumen de respaldo. Decir solo «Capri» conserva una ventana para dar la orden. Al cerrar el micrófono, el estado cambia a «Reconociendo la frase» mientras se transcribe. El nombre de activación se quita del dictado antes de enviarlo al chat, también si se dijo usando F8; escribirlo manualmente conserva el texto escrito.

Se prueban las órdenes, los argumentos de ejecución sin consola, las búsquedas, el paquete, la interfaz, el audio simulado, la revisión de transcripciones dudosas, el texto progresivo, la lectura continua y la interrupción durante la reproducción o preparación del audio. También se prueban la activación y transcripción de la orden con audio simulado, el descarte de órdenes canceladas y los resultados del adaptador de Spotify. Se comprobó que el vocabulario Vosk instalado incluye «capri» y que el controlador PowerShell de Spotify tiene sintaxis válida. Se comprobó la conversación real con el llama3.2:3b instalado, incluida su presentación como Capri y el tiempo de primer texto con el modelo cargado. La captura real, la precisión de Whisper con tu voz, la detección del nombre en tu ambiente, Spotify, las descargas nuevas y la voz sintética requieren comprobarse desde tu sesión normal fuera del entorno restringido de desarrollo.

Una pausa sin voz finaliza la hipótesis pendiente de Vosk sin esperar varios segundos a su cierre interno. Una nueva frase descarta el audio de conversación anterior con un margen breve para conservar el comienzo del nombre. Todas las repeticiones consecutivas de «Capri» se quitan del dictado.

## Probar el micrófono

En **Ajustes → Prueba de micrófono**, pulsa **Grabar prueba · 5 s** y habla normalmente. Verás el nivel de tu voz y una advertencia si satura. Después pulsa **Escuchar prueba** para oír el audio capturado por el micrófono seleccionado. La prueba no requiere decir Capri, no transcribe, no ejecuta órdenes ni envía audio a internet. Conserva una sola grabación temporal en memoria y la descarta al cambiar de micrófono o cerrar Ajustes. Grabar otra prueba reemplaza la anterior. No se graba automáticamente al abrir Ajustes. Puedes detener la grabación o reproducción con Detener prueba; F8 interrumpe la prueba para iniciar el dictado normal.

El **umbral automático** conserva el comportamiento previo. Para ajustar manualmente, desmárcalo y mueve el control: **izquierda = capta voz más baja; derecha = exige hablar más fuerte**. La línea roja indica el umbral y el color muestra si el volumen lo supera. El filtro se aplica al reconocimiento por nombre y al dictado F8; no cambia el volumen del micrófono de Windows. La reproducción de prueba conserva el audio original, sin ese filtro, para que puedas juzgar la señal y el ruido. Superar el umbral no demuestra que el nombre o las palabras se reconozcan correctamente.

## Diálogos junto al personaje

La conversación usa un panel pequeño con la última pregunta, respuesta y una entrada para escribir. Se coloca encima del personaje si hay espacio y, si no, a un lado. **Escribir** o un clic en el personaje abren ese panel. Hablar no abre automáticamente el historial grande. Puedes consultar la conversación completa desde **Historial** en el panel pequeño o en el menú del personaje. El historial dura solo mientras Capri está abierta; el panel pequeño muestra el tramo reciente de respuestas extensas. Los dictados dudosos también se revisan en esa entrada pequeña antes de enviar.

El glitch añade un cursor y pequeños trazos transitorios durante la escritura; nunca modifica el texto confirmado, el historial ni la entrada enviada al modelo. Puedes desactivar **Glitch sutil al escribir los diálogos**. El panel se puede ocultar con × o desactivando **Mostrar diálogos progresivos junto a Capri**; aun así, el botón Escribir permite abrirlo manualmente.

El avatar conserva la ilustración base: las tres variantes solo cambian una pequeña región de la boca (normal, abierta completamente blanca y sonrisa). El pelo, cuerpo y pose son idénticos. La vista aplica un recorte de cámara, suavizado y líneas de pantalla; no redibuja el personaje. Las interferencias desplazan algunas bandas durante unos 160 ms y luego vuelven a la imagen limpia. Son menos frecuentes en reposo y algo más frecuentes al hablar. **Interferencias breves de imagen y texto** permite desactivarlas. Al desactivar las animaciones se mantiene la imagen normal fija.

Con voz activada y volumen mayor que cero, el texto visible espera a que empiece la reproducción. La voz natural usa las marcas de palabra y el reloj del reproductor para revelar el texto; la boca descansa entre marcas de habla. La voz de Windows se sintetiza primero a un WAV temporal y usa el mismo reproductor, con avance aproximado según la duración porque no aporta esas marcas. No se fragmenta la lectura en peticiones separadas. La preparación puede tardar: el panel muestra **Preparando voz** durante esa espera. Sin voz o con volumen cero, se conserva la escritura progresiva independiente. Estos tiempos siguen al reproductor, no prometen alineación fonética exacta ni compensan toda latencia del dispositivo de salida.

## Preparación al iniciar

El estado **Preparando activación** indica que el detector todavía está cargando. La entrada se abre antes de cargar Vosk y el detector de voz, y conserva el audio inicial en una cola acotada durante esa preparación. El estado cambia a **Di «Capri» o pulsa F8** cuando la entrada y los detectores están preparados. La precarga del modelo de conversación empieza después de ese aviso para dar prioridad al micrófono. Durante reconocimiento o reproducción puede haber otros estados; no significan que la activación esté lista. Esto evita perder por diseño toda la primera frase mientras se carga el detector, pero no garantiza precisión perfecta ni una latencia constante con cualquier voz y ruido.
