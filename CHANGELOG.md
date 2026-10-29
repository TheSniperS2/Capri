# Cambios

## En desarrollo

### Corregido

- El puente de Opera 1.0.4 selecciona resultados de YouTube sin necesitar un vídeo ya cargado. La orden por número deja de depender exclusivamente de accesibilidad de Windows.
- Aclaraciones como «de la playlist Capri» extraen «Capri» y conservan la canción pendiente, en lugar de buscar una lista con toda la frase como nombre.
- Destinos explícitos Spotify/YouTube prioritarios, selección de resultados de YouTube por número y alcance de playlist conservado aunque falte su nombre.
- Escribir deja de recuperar el globo anterior; abandonar el campo cancela la composición sin perder el borrador ni ocultar respuestas nuevas.
- La aceptación automática puede vigilar también colas iniciadas directamente en LoL. La opción guardada se recupera al iniciar Capri, se reconecta al cliente y sigue disponible entre partidas, con estado visible en ajustes.
- El globo sigue cada movimiento de Capri sin esperar al temporizador de texto. Escribir alterna su apertura y cierre; el borde inferior encaja en el marco.
- Separación medida entre iconos y etiquetas del menú radial, también en portugués y japonés.
- El foco de un campo oculto ya no mantiene al personaje suspendido al soltarlo. Escribir en un campo visible con foco sigue pausando el movimiento.
- Las respuestas que se desvían claramente del idioma elegido se corrigen antes de narrarlas. Los mensajes extranjeros en el historial no cambian la selección actual.

### Mejorado

- Entrada con revelado progresivo, indicadores en la paleta roja y rostro despejado durante la secuencia.

### Añadido

- Búsqueda, cancelación y aceptación de cola en el cliente local de LoL. Menú y órdenes en cuatro idiomas; aceptación automática opcional para las búsquedas iniciadas con Capri.
- Se conserva la despedida anterior: mano roja, traslado eléctrico hacia la estrella y apagado gradual.
- README con instalación, ejemplos, idiomas y límites de las integraciones; índice de documentación, mapa de módulos y plantillas para reportes y propuestas.

### Incorporado desde 0.1.0

- Modo personaje, anclajes, menú radial y ajustes con marcos propios.
- Interfaz, respuestas y voces en español, inglés, portugués de Brasil y japonés.
- Selector de modelos y micrófonos, tecla para hablar configurable y controles del reproductor.
- Recursos de mayor resolución y nuevas transiciones.

## 0.1.0

Primera versión preparada para distribución general en Windows.

- Chat con Ollama y reconocimiento local Whisper/Vosk.
- Activación por nombre, F8 y botón Hablar, con captura continua de la orden.
- Interrupción de voz y respuestas pendientes.
- Pestañas y búsquedas en Opera, aplicaciones registradas y carpetas de Windows.
- Controles de la sesión actual de Spotify y vinculación de playlists.
- Interfaz flotante e icono de Capri.
- Valores predeterminados genéricos, sin nombre personal del interlocutor.
- Código, pruebas, instalador y documentación en carpetas separadas.
- Pruebas automatizadas en Windows y empaquetado de versiones mediante GitHub Actions.

### Limitaciones

- Requiere Python 3.12; no es un ejecutable autónomo.
- La exactitud del reconocimiento depende del micrófono, el ruido y el equipo.
- La voz natural usa un servicio externo y no reproduce la voz exacta de la actriz.
- La activación por nombre se pausa mientras la aplicación habla.
- Las integraciones de Spotify dependen de la sesión y los controles que exponga la aplicación; no se garantiza toda versión o estado de interfaz.
- Aquella versión no incluía el modo personaje ni las expresiones de boca incorporadas después en desarrollo.
