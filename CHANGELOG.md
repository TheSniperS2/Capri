# Cambios

## En desarrollo

### Corregido

- El foco de un campo oculto ya no mantiene al personaje suspendido al soltarlo. Escribir en un campo visible con foco sigue pausando el movimiento.
- Las respuestas que se desvían claramente del idioma elegido se corrigen antes de narrarlas. Los mensajes extranjeros en el historial no cambian la selección actual.

### Mejorado

- Entrada con revelado progresivo, indicadores en la paleta roja y rostro despejado durante la secuencia.
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
