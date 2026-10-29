# Referencias de voz — 29 de octubre de 2026

Se conserva el perfil elegido por el usuario. La alternativa nueva se llama **Capri latina · experimental** y se puede comparar desde Ajustes → Voz → Escuchar prueba.

## Qué se encontró

- [capri-desktop, implementación de voz](https://github.com/lachydotmcg/capri-desktop/blob/main/app/Voice.cs): integra ElevenLabs y una alternativa local basada en Kokoro mediante sherpa-onnx. Los nombres «Her own», «Bright», «Sly» y «Sharp» son selecciones de hablante del proyecto; ese nombre no verifica que se trate de la actriz del anime.
- [Paquete de voz de ese repositorio](https://github.com/lachydotmcg/capri-desktop/blob/main/app/VoicePack.cs): declara un paquete de unos 316 MB, con léxicos de inglés estadounidense y británico. No se descargó ni se instaló como si fuera un modelo del doblaje latino.
- [TheAgencyMGE/capri-companion](https://github.com/TheAgencyMGE/capri-companion): otro proyecto de escritorio no oficial, útil como referencia de integración. Su presentación no demuestra que incluya un modelo TTS de la voz española original.
- [Página oficial de Edgerunners 2 en español](https://www.cyberpunk.net/es/edgerunners2): se revisó como referencia oficial. Los nombres de reparto mostrados corresponden a las voces japonesas; no permiten identificar por sí solos una voz sintética equivalente al doblaje latino.
- [Catálogo de Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) y [edge-tts](https://github.com/rany2/edge-tts): permiten mantener el motor actual y comparar voces españolas sin añadir un servicio de pago.

## Opción añadida

La propuesta experimental usa Dalia, español de México, con tono +10 Hz y ritmo del perfil un 6 % más ágil, multiplicado por la velocidad que elija el usuario. Es una variante entre el perfil clásico (+16 Hz) y Latina suave (+6 Hz), pensada para comparar un registro menos agudo que el clásico sin perder claridad al hablar español latino.

**No se ha verificado auditivamente como la voz más parecida a Capri.** La búsqueda no proporcionó una muestra fiable y aislada de su doblaje español para una comparación directa. No es un clon, ni un modelo oficial, ni se presenta como la actriz de la serie. La similitud queda pendiente de comparar una referencia concreta del doblaje que quiera el usuario.

Los perfiles anteriores siguen disponibles y la actualización no cambia el seleccionado. Solo se aplica otra voz al elegirla expresamente.


## Alternativa multilingue

Se verifico en el catalogo real y se sintetizo una muestra espanola con en-US-EmmaMultilingualNeural. Se ofrece como Emma multilingue - espanol, con +8Hz. Es una voz base inglesa capaz de leer espanol; no es la actriz ni una clonacion de Capri. Microsoft documenta el espanol entre sus idiomas: https://learn.microsoft.com/es-es/azure/ai-services/speech-service/speech-synthesis-markup-voice . La opcion permanece sin seleccionar hasta que el usuario la elija.
