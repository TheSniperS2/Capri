# Conectar Capri con YouTube en Opera GX

Esta conexión controla el vídeo de la pestaña seleccionada mediante sus propiedades de reproducción. Evita depender del deslizador que Opera expone a Windows. Sirve para volumen interno, silencio, pausa, continuar y los botones Siguiente/Anterior disponibles del reproductor.

## Cargar una vez

1. Cierra Capri completamente y vuelve a abrirla para cargar la actualización.
2. Clic derecho sobre Capri → **Conectar YouTube con Opera**.
3. Pulsa **Abrir gestor de Opera**. Activa **Modo desarrollador** y elige **Cargar extensión descomprimida**.
4. Pulsa **Abrir carpeta de extensión** en el panel de Capri. Selecciona esa misma carpeta desde el selector de Opera: es `integraciones\opera-capri` dentro de la instalación de Capri.
5. Recarga la pestaña de YouTube. Deja seleccionado un vídeo. El panel de Capri debe mostrar **Conectada con la pestaña seleccionada de YouTube**.

La instalación es local; no se publica nada ni se necesita cuenta de desarrollador. Después de actualizar los archivos de esta extensión, pulsa **Recargar** en su tarjeta de Opera y recarga YouTube.

## Ejemplos

- «Pon el volumen de YouTube al 50%»; también acepta «pone el volumen…» del dictado.
- «Sube el volumen del vídeo», «baja el volumen de YouTube».
- «Silencia el vídeo», «quita el silencio de YouTube».
- «Pausa el vídeo», «reanuda YouTube», «siguiente vídeo».

Subir o bajar sin cantidad cambia diez puntos. El volumen se lee después de cambiarlo y se limita a 0–100. **Pedir un nivel mayor que cero también activa el sonido**; pedir cero lo silencia. La extensión actualiza el controlador del reproductor en el contexto de la página y comprueba su estado, el elemento de vídeo y las etiquetas visibles del control; evita desmutear solo el audio dejando el icono anterior. «Silencia el vídeo» y «quita el silencio de YouTube» siguen disponibles. Capri también activa el sonido si detecta la respuesta de la versión 1.0.1 aún cargada, sin repetir un incremento que ya se aplicó. Un vídeo debe estar cargado; el navegador puede exigir iniciarlo manualmente antes de permitir reproducirlo por una orden. Siguiente/Anterior dependen de que YouTube ofrezca esos botones; Capri confirma la solicitud, no una navegación que aún no terminó.

## Alcance

La extensión se ejecuta únicamente en dominios de YouTube y habla con Capri por `127.0.0.1:18741`. Usa la pestaña seleccionada en la última ventana de Opera utilizada, sin activarla ni cambiar el foco. Su módulo de página solo acepta operaciones de volumen y silencio acotadas; no recibe código para ejecutar. No consulta otras páginas, cookies, contraseñas ni archivos; tampoco transmite títulos o historial al servidor local.

Capri crea las órdenes dentro del proceso. El servidor local solo permite a la extensión identificada recibir esas órdenes y devolver resultados acotados. No ofrece una ruta HTTP para enviar instrucciones al computador, abrir archivos o ejecutar código. Se cierra con Capri. Si se corta la conexión después de enviar una orden, no la repite automáticamente.

Si el panel no conecta: comprueba que Capri esté abierto, que la extensión esté habilitada y que hayas recargado la pestaña seleccionada de YouTube. Si otra aplicación usa el puerto, el panel lo indica. La instalación por sí sola no demuestra que tu pestaña esté conectada: verifica el indicador antes de probar la voz.

Referencias: [permisos de red de extensiones Chromium](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests), [identidad estable mediante la clave pública del manifiesto](https://developer.chrome.com/docs/extensions/reference/manifest/key), [volumen del elemento de vídeo](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/volume).
