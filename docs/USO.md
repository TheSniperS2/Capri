# Capri

Abre **Abrir Capri.pyw**. La primera apertura instala sus dependencias en una carpeta propia, descarga Whisper base multilingüe (148 MB), el reconocimiento rápido de respaldo y las referencias de Capri. Verás el avance; necesita internet para esa preparación. Al actualizar conserva tu micrófono y los modelos de conversación ya descargados.

Después aparece una ventana flotante con la imagen del personaje. Arrástrala para moverla. Haz clic para abrir el chat. Pulsa **F8** o **Hablar** para dictar una frase; haz una pausa para que responda. Pulsa **Esc** para detener la voz. El menú del botón derecho permite salir. Se crea un acceso directo **Capri** en el escritorio; también puedes abrir otra vez el lanzador original.

También puedes decir **«Capri»** y dar la orden, o decir **«Capri, busca memes de Cyberpunk»** en una misma frase, sin esperar un aviso. Se conserva la misma captura desde el nombre hasta terminar la orden, aunque el reconocedor la divida en varios segmentos. Si dices solo «Capri», espera hasta seis segundos de silencio por la instrucción sin cerrar ni volver a abrir el micrófono. Después de la orden espera aproximadamente 1,15 segundos de silencio antes de transcribir. La activación está habilitada al abrir normalmente la aplicación; usa el micrófono seleccionado y el modelo Vosk local ya instalado. Whisper transcribe el audio completo al terminar si elegiste Mixto. La escucha mantiene solo un fragmento temporal en memoria, sin archivos ni envío de audio. Se pausa mientras Capri habla y mientras están abiertos los Ajustes, y se reanuda automáticamente. Durante su voz, usa Hablar o F8 para interrumpir. Puedes desactivar **Ajustes → Activar al decir «Capri»**. La detección depende del ruido y de la pronunciación; no es una garantía de reconocimiento en cualquier ambiente.

En **Ajustes → Micrófono** puedes elegir la entrada de audio que quieres usar. La selección se guarda para las próximas aperturas. Si conectas otro micrófono, pulsa **Actualizar**. La lista oculta las repeticiones de un dispositivo que Windows ofrece mediante varias interfaces de audio. «Predeterminado de Windows» es una opción automática, no un micrófono adicional. Si el elegido se desconecta, Capri avisa en lugar de cambiar automáticamente al micrófono de los audífonos.

La captura se inicializa en un hilo de audio propio de Windows. Evita WDM-KS y, si una interfaz falla, intenta otras variantes inequívocas del mismo micrófono. Si no logra abrirlo, `diagnostico-microfono.json` contiene los intentos y los errores del controlador, sin grabaciones ni texto reconocido.

**Ajustes → Reconocimiento de voz** permite elegir **Mixto · español e inglés (Whisper)** o **Rápido · Vosk español**. Mixto usa el modelo multilingüe instalado y aporta nombres como Spotify, YouTube y Opera GX para favorecer su reconocimiento sin traducirlos. Al abrir aplicaciones también acepta variantes de pronunciación como «espotifai». Whisper hace una pausa breve al detectar el final de la frase y después la transcribe. Si el resultado es dudoso, aparece en el cuadro de texto para revisarlo antes de enviarlo. La precisión real depende del ruido y del micrófono. Su primera carga tarda más; el modelo queda en memoria para las siguientes frases.

Prueba: «abre una pestaña en Opera GX», «puedes abrirme una pestaña», «me gustaría que abrieras una pestaña del Opera GX», «abre una pestaña y busca recetas de pasta», «abre la calculadora», «abre Spotify», «habla más rápido» o «qué hora es».

Las búsquedas admiten, por ejemplo, «búscame memes de Cyberpunk», «puedes buscarme memes de Cyberpunk», «quiero que busques memes de Cyberpunk» y «haz una búsqueda de memes de Cyberpunk». Abren la consulta en Opera GX. También puedes pedir «abre mis archivos», «abre Descargas», «abre Documentos», «abre Imágenes» o «abre el Escritorio»; las carpetas respetan las ubicaciones configuradas en Windows.

Para Spotify: **«reproduce la música»**, **«reanuda la canción»** y **«pon la música»** reanudan la sesión actual, sin buscar otra canción ni cambiar la cola. **«Salta la canción»**, **«pon la siguiente canción de la playlist»** y **«podrías poner la música siguiente»** pasan a la siguiente pista de la cola actual; **«pon la canción anterior»** vuelve a la anterior. **«Pausa Spotify»** pausa esa sesión. **«Qué canción está sonando»** consulta el título y estado que comunica Spotify. Estos controles usan la sesión multimedia de Windows de Spotify, sin abrir páginas ni buscar canciones. Si Spotify no comunica una sesión o rechaza una orden, Capri lo indica. El modelo de charla no afirma qué está sonando basándose en sus propias respuestas.

Para elegir otra canción: «busca Never Fade Away en Spotify» o «reproduce Never Fade Away en Spotify». La búsqueda usa la aplicación instalada. Para reproducir un título concreto, Capri intenta invocar un control accesible cuyo nombre coincida con la búsqueda. Necesita una sesión iniciada y controles accesibles en Spotify. No pulsa coordenadas ni envía teclas a otra ventana. Si no puede confirmar el control, mantiene abierta la búsqueda y lo informa.

Para playlists: **«pon mi playlist Cyberpunk»** intenta encontrarla en **Tu biblioteca**, sin buscarla entre playlists públicas. Si Spotify no expone la biblioteca mediante controles accesibles, usa **Ajustes → Vincular playlist de Spotify**: introduce el nombre y pega su enlace. Puede seguir siendo privada; debe ser accesible desde tu cuenta iniciada. Se guarda solo el nombre y el identificador de playlist en `playlists.json`, sin contraseña ni tokens. Una vez vinculada, también admite «pon Cyberpunk». No hace públicas listas ni cambia permisos. Si abre una playlist pero no puede confirmar su reproducción, lo informa. La reproducción real y el acceso a la biblioteca no han podido verificarse desde el entorno restringido de desarrollo.

El nombre del navegador se detecta automáticamente, con preferencia por Opera GX. Las búsquedas se abren como una pestaña de Google; la aplicación no lee ni resume sus resultados. Solo abre las aplicaciones que tiene registradas.

Las órdenes reconocidas de pestañas, páginas y aplicaciones van al ejecutor del programa, sin pedir al modelo que las describa. Una pestaña nueva sin destino usa una página en blanco. Las acciones de computador que todavía no estén implementadas muestran un aviso. Las preguntas sobre cómo hacer algo siguen siendo conversación.

Las aperturas toleran errores pequeños de transcripción en el comienzo de la petición, como «Podríes avrir Spotify»: corrigen una letra omitida, cambiada o intercambiada si el destino es una aplicación conocida. La corrección no cambia el texto de búsquedas ni convierte frases negadas o explicaciones en órdenes. La conversación conoce las capacidades reales del ejecutor y corrige negativas globales falsas sobre abrir Spotify o aplicaciones; no presenta una acción como realizada si no pasó por el ejecutor. Esto mejora la interpretación de la frase recibida, sin garantizar que el reconocimiento de voz transcriba todas las palabras correctamente.

Para conversación libre: **Ajustes → Activar IA local → Descargar y activar**. Se descargan Ollama y llama3.2:3b (aprox. 2 GB de modelo, más el instalador). Después conversa sin pago por uso. Si ya tienes Ollama con un modelo, se usa automáticamente. No se ejecuta código propuesto por la IA.

El micrófono se reconoce localmente. El audio permanece en memoria y no se graba en archivos. La voz natural de respuesta usa Microsoft Edge TTS y requiere internet: se envía el texto a sintetizar. Se puede desactivar en Ajustes para usar la voz de Windows. El perfil Capri usa una voz sintética femenina en español latino con ritmo y tono más enérgicos; no reproduce el timbre exacto de la actriz. La memoria del chat dura solo mientras la aplicación está abierta.

La velocidad inicial es **1×**, normal, tanto en la voz natural como en la voz de Windows. Para una lectura más fluida, el texto hablado omite marcas de formato y reduce las pausas de comas, dos puntos y punto y coma; conserva puntos y preguntas. La velocidad se cambia en **Ajustes → Velocidad de voz**, o con «habla más rápido», «lee más lento» y «habla a velocidad normal». La elección se guarda.

La identidad se fija como **Capri** en cada petición y las presentaciones sencillas responden directamente. El texto aparece mientras se genera; la respuesta se narra completa en una sola lectura para evitar esperas entre audios separados de cada frase. **Hablar o F8 interrumpen la voz y la respuesta pendiente antes de activar el micrófono**, incluso si todavía estaba preparando el audio. Se mantiene el modelo local cargado durante 15 minutos y se limita la longitud normal de las respuestas para reducir la espera. La primera carga del modelo, el uso de la GPU por otros programas y la conexión de la voz natural influyen en la demora.

Los archivos instalados quedan en **%LOCALAPPDATA%\Capri**. Allí están ajustes.json (sin claves), modelos/ y assets/. Capri no se añade al inicio automático de Windows. No requiere permisos de administrador.

El icono de las ventanas y del acceso directo del escritorio usa la referencia de Capri incluida en la aplicación, convertida a un icono de Windows con varios tamaños. No se modifica su rostro. Windows puede conservar temporalmente en caché el icono anterior de un acceso anclado a la barra de tareas; desanclar ese acceso antiguo y anclar de nuevo el acceso Capri actual permite actualizarlo.

## Apariencia y procedencia

La aplicación muestra las referencias publicadas de Capri y conserva sus rasgos. Anima la flotación, las partículas y el cambio de imagen al hablar. Esta primera versión no tiene un cuerpo 3D ni animación labial del anime.

Referencias del personaje: https://mudae.net/character/3127100/Capri%20%7BCP%7D

Capri y las imágenes de la serie pertenecen a sus respectivos titulares. Aplicación de aficionado para uso personal, no oficial. Las referencias se descargan desde la galería; no se incluyen episodios ni se modifican archivos del juego.

Vosk y modelos: https://alphacephei.com/vosk/models

Whisper base: https://huggingface.co/Systran/faster-whisper-base

Faster Whisper: https://github.com/SYSTRAN/faster-whisper

Ollama: https://ollama.com/

Edge TTS: https://github.com/rany2/edge-tts

## Estado de verificación

Se prueban las órdenes, los argumentos de ejecución sin consola, las búsquedas, el paquete, la interfaz, el audio simulado, la revisión de transcripciones dudosas, el texto progresivo, la lectura continua y la interrupción durante la reproducción o preparación del audio. También se prueban la activación y transcripción de la orden con audio simulado, el descarte de órdenes canceladas y los resultados del adaptador de Spotify. Se comprobó que el vocabulario Vosk instalado incluye «capri» y que el controlador PowerShell de Spotify tiene sintaxis válida. Se comprobó la conversación real con el llama3.2:3b instalado, incluida su presentación como Capri y el tiempo de primer texto con el modelo cargado. La captura real, la precisión de Whisper con tu voz, la detección del nombre en tu ambiente, Spotify, las descargas nuevas y la voz sintética requieren comprobarse desde tu sesión normal fuera del entorno restringido de desarrollo.
