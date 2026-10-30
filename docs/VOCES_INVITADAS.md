# Llamadas invitadas

King, D, Roman y Talia usan diálogos de broma escritos para esta aplicación y perfiles sintéticos originales. El nombre y los subtítulos del invitado aparecen dentro del aviso telefónico; no en el globo sobre el personaje de Capri. La reacción posterior sí la dice Capri, una vez cerrado el enlace telefónico.

El cuadro crece por líneas según avanza el texto sincronizado con la voz, sin reservar de antemano la altura del guion completo. Su ancho y esquina superior permanecen fijos. Con la voz desactivada muestra el texto completo y ajusta su altura a ese contenido.

Los rasgos de partida se consultaron en la [página oficial de Cyberpunk: Edgerunners 2](https://www.cyberpunk.net/es/edgerunners2): King es un veterano, D un netrunner, Roman un cinéfilo y Talia está vinculada al cromo y Maelstrom. Los chistes no son diálogos oficiales ni resumen la trama.

| Invitado | Dirección de voz sintética |
|---|---|
| King | Grave, pausada y seca |
| D | Base mexicana masculina, contenida y algo más grave; se retiró el acento de España |
| Roman | Base mexicana femenina con registro juvenil, más ligera que la base masculina adulta anterior |
| Talia | Femenina, enérgica y descarada |

Se usa una voz de síntesis del idioma de la interfaz y ajustes propios de tono y ritmo. Los identificadores se comprobaron en Edge TTS para español, inglés, portugués y japonés. Para español se tomó como referencia el doblaje latino: Roman usa `es-MX-DaliaNeural` a +18 Hz y +4 %, y D usa `es-MX-JorgeNeural` a −8 Hz y −2 %. King conserva sus ajustes anteriores. Los otros idiomas conservan sus perfiles.

La búsqueda contrastó el [catálogo oficial de Microsoft](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support): existe una voz infantil mexicana Marina en Azure, pero el servicio Edge utilizado por esta aplicación solo devuelve Dalia y Jorge para México. Estos ajustes son aproximaciones de registro y acento, no una coincidencia auditiva verificada con los intérpretes. La conexión y la disponibilidad del servicio pueden afectar a la reproducción. Las preferencias de voz, acento, modelo y micrófono de Capri permanecen intactas.

Desde que aparece el aviso entrante se prepara en segundo plano el comentario posterior de Capri, aprovechando también la espera antes de contestar. Al cortar se reutiliza ese archivo, evitando otra solicitud de síntesis en el momento del remate. La pausa prevista es la del tono breve de desconexión, unos 240 ms, más el inicio de reproducción. Una red lenta puede retrasar una preparación todavía incompleta. Si cambias el perfil o el idioma durante la llamada, se descarta el audio anterior para respetar la configuración nueva. Colgar antes o dar otra orden cancela la preparación y limpia sus archivos temporales.

Las llamadas invitadas usan siempre sus perfiles de Edge, incluso si Capri tiene desactivada la voz natural. Si falla esa síntesis se informa del fallo y se cierra la llamada; no se sustituye al invitado por la voz genérica de Windows. Dalia también es una base disponible para Capri: el perfil de Roman aplica sus propios ajustes de tono y ritmo, pero no constituye una voz oficial o clonada.

Hay dos guiones por invitado, con una reacción contextual de Capri para cada uno. Las llamadas normales de Capri conservan sus 24 bromas y sus disfraces de voz. El reparto de invitados no cambia la identidad de Capri en las conversaciones normales.
