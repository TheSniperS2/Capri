# Cambios

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
- La interfaz no incluye cuerpo 3D ni animación labial.
