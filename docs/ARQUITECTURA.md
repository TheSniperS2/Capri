# Mapa de módulos

Capri separa la interfaz Tk, el trabajo de audio y las integraciones. El código de ejecución está en `src/`; el instalador copia esos módulos a la carpeta de cada usuario.

| Área | Módulos principales | Responsabilidad |
| --- | --- | --- |
| Aplicación | `app.py` | Estado de la sesión, eventos, cancelación y coordinación. |
| Interfaz | `ajustes_ui.py`, `dialogos.py`, `entrada.py`, `menu_radial.py` | Ajustes, conversación, escritura y menú del personaje. |
| Personaje | `companera.py`, `ventanas.py`, `travesuras.py` | Física, apoyo sobre ventanas, anclajes y juegos opcionales. |
| Animación | `avatar.py`, `intro.py`, `despedida.py`, `sincronia.py` | Expresiones, transiciones, cierre y sincronización con voz. |
| Idiomas | `idiomas.py`, `traducciones.json` | Catálogo de interfaz y comprobación del idioma de las respuestas. |
| Conversación y órdenes | `core.py`, `intenciones.py`, `nombres.py` | Ollama, interpretación, contexto y nombres de aplicaciones. |
| Audio | `voz.py`, `reconocimiento.py`, `activacion.py`, `prueba_microfono.py` | Captura, reconocimiento, activación y síntesis. |
| Escritorio | `aplicaciones.py`, `control_pc.py`, `escritorio.py` | Catálogo de programas y acciones verificables sobre el equipo. |
| Multimedia | `multimedia.py`, `playlists.py`, `volumen_apps.py` | Spotify, biblioteca, sesiones y volumen interno. |
| League of Legends | `league.py` | Conexión local limitada a sala, búsqueda y ready-check; aceptación opcional cancelable. |
| Navegador | `navegador.py`, `puente_opera.py`, `integraciones/opera-capri/` | Sitios, YouTube y puente local del navegador. |
| Preparación | `recursos.py`, `activar_ia.py`, `preparar_whisper.py`, `empaquetar.py`, `installer/plantilla.py` | Descargas, modelos, empaquetado y arranque. |

## Flujo de una petición

La interfaz recibe texto o una transcripción. El intérprete intenta resolver una acción disponible; si corresponde, consulta al modelo local. El ejecutor devuelve un resultado que se registra como contexto. La conversación libre se genera por otra vía y nunca se ejecuta como código.

Los trabajadores envían eventos a la interfaz. Tk crea y modifica sus widgets e imágenes en el hilo principal. Los identificadores de petición y señales de cancelación permiten descartar respuestas anteriores.

El idioma elegido se aplica a la interfaz, al texto y a la voz. Una respuesta que se desvía claramente de idioma se corrige antes de narrarla; la elección de una voz por sí sola no traduce el contenido.

## Dónde cambiar cada cosa

- **Un fallo visual:** empieza por la ventana o el renderer correspondiente. Comprueba también los tamaños pequeños y los cuatro idiomas.
- **Una orden:** añade o ajusta interpretación y ejecutor; conserva argumentos literales y el resultado real de la acción.
- **Una etiqueta:** actualiza el catálogo para inglés, portugués y japonés. Conserva las variables de las plantillas.
- **Un archivo de ejecución nuevo:** inclúyelo en `empaquetar.ARCHIVOS` y comprueba el lanzador generado.
- **Un fallo de foco o animación:** reproduce tanto el flujo de la interfaz como el estado del personaje; una prueba de física aislada no comprueba el foco de Tk.

Las rutas de los módulos se mantienen estables para actualizar instalaciones anteriores sin invalidar sus preferencias.
