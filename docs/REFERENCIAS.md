# Referencias y decisiones de presentación

Consulta: 27 de octubre de 2026. Se toman ideas de interacción, sin incorporar código, imágenes ni modelos del proyecto de referencia.

## Referencia comprobada

[Capri: The Desktop Construct](https://github.com/Juliowiwiwiwi/Capri-Capricorn-The-Desktop-Construct) describe una compañera sobre el escritorio, estados de reposo como parpadeo/dormir, chat compacto y respuestas progresivas con Ollama. Su README presenta entrada y salida de voz como trabajo pendiente. No es evidencia de que ese repositorio ya resuelva el reconocimiento o la voz que buscamos.

Ideas aprovechables: diálogos junto al personaje, estados de escucha/pensamiento/voz diferenciados y controles que no obliguen a mantener un chat grande abierto. Se añadió una burbuja de diálogo con escritura progresiva a la implementación propia.

## Referencias aportadas por el usuario, sin inspección directa

- [Canal capri.ai](https://www.tiktok.com/@capri.ai).
- [Diálogos que se van escribiendo](https://www.tiktok.com/@capri.ai/video/7700907147483352338).
- [Movimiento de boca, parpadeo y voz](https://www.tiktok.com/@overyx2/video/7701226194892492084).

TikTok bloqueó la lectura web y no hay un navegador conectado disponible. La descripción de esos efectos procede del usuario: no se afirma haber visto los clips ni escuchado su voz.

Actualización con las diez capturas aportadas por el usuario: se pueden comprobar los paneles compactos, diálogos con estados, marcos geométricos, controles de efectos, imágenes del personaje en distintas expresiones y el modo mascota sobre el escritorio. Las imágenes no permiten comprobar el sonido, la duración del reconocimiento ni el movimiento entre fotogramas. La captura del repositorio muestra además un commit que anuncia voz: el README puede estar rezagado, por lo que no basta para concluir que esa función no existe en el código actual.

Implementación propia a partir de esa dirección visual: panel compacto de conversación sin abrir el historial grande, escritura ligada a la reproducción de voz, marco geométrico y estado real de preparación del micrófono. Tras la corrección solicitada por el usuario, se descartó el avatar de seis fotogramas que alteraba pelo y cuerpo. Ahora se conserva la ilustración base con tres estados limitados a la boca y efectos de pantalla en ráfagas, con un panel horizontal y diálogo encima. Véase ARTE_ANIMADO.md. No se extrajeron sprites, diseños ni código de las capturas o del repositorio.

Sigue pendiente escuchar los videos para evaluar timbre y efectos de voz; no se cambió el modelo ni se aplicó reverberación o delay arbitrarios. La boca nueva no realiza sincronización fonética exacta. Las ilustraciones anteriores se conservan como alternativa al desactivar animaciones.
