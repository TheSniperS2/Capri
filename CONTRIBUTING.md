# Contribuir a Capri

Usa Python 3.12 en Windows. Crea un entorno virtual, instala `requirements.txt`, genera el lanzador y ejecuta las pruebas con los comandos del README.

El [índice de documentación](docs/README.md) reúne las guías. Para localizar el código, consulta el [mapa de módulos](docs/ARQUITECTURA.md). Las novedades que aún no tienen una Release están en la sección «En desarrollo» del changelog.

Antes de enviar un cambio:

1. Describe el problema y el comportamiento esperado con un ejemplo de frase o acción.
2. Cambia los módulos de `src/`, no los archivos generados de `dist/`.
3. Añade una prueba cuando corrijas un fallo de interpretación, captura, cancelación o integración.
4. Ejecuta `python empaquetar.py` y `python -m unittest discover -s tests -v` con el entorno virtual activado.
5. Comprueba `git diff --check` y revisa que no haya datos personales en los archivos preparados para el commit.

No incluyas ajustes, playlists privadas, credenciales, diagnósticos con datos personales, grabaciones, pesos de modelos ni recursos descargados. Para reportar problemas de audio, explica la versión de Windows, el motor elegido y el mensaje de error, sin compartir grabaciones ni datos de tu cuenta.

Las acciones nuevas deben tener argumentos definidos y resultados verificables. Las respuestas del modelo de conversación siguen siendo texto: no deben ejecutarse como código ni comandos de consola. No declares una acción como completada si la integración no la confirmó.

Los cambios en interfaz y audio necesitan comprobación manual en una sesión normal de Windows además de las pruebas automatizadas. Indica qué comprobaste y qué sigue pendiente.

Para textos de interfaz, incluye las traducciones de inglés, portugués y japonés. Conserva las variables de las plantillas y las identidades internas de las opciones. El nombre de un modelo, un archivo o una playlist no se traduce como si fuera una etiqueta.

Un reporte útil incluye la frase o los pasos, el resultado esperado, la versión y la configuración relacionada. Issues ofrece formularios para errores y propuestas; las solicitudes de cambios incluyen espacio para describir la comprobación y sus limitaciones.
