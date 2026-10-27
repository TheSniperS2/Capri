# Comparación local de Llama y Qwen — 27 de octubre de 2026

En el equipo evaluado, **Llama 3.2 3B es la recomendación equilibrada para rapidez**. **Qwen 3 4B Instruct es la alternativa para mayor precisión de instrucciones y mejores historias**, aceptando más espera. Qwen 3.5 2B no superó a Llama en rapidez ni en aciertos de esta prueba.

Equipo: Intel Core i5-10400, 16 GB de RAM y NVIDIA GTX 1650 de 4 GB. Se compararon los tres modelos Llama/Qwen instalados, todos Q4_K_M. No se evaluó todo el catálogo de modelos existente.

| Modelo exacto | Instrucciones correctas | Mediana para interpretar | Mediana de respuesta conversacional completa | Primer texto |
|---|---:|---:|---:|---:|
| `llama3.2:3b` | 30/38 (79 %) | 0,34 s | 1,33 s | 0,17 s |
| `qwen3.5:2b-q4_K_M` | 28/38 (74 %) | 1,41 s | 1,78 s | 0,90 s |
| `qwen3:4b-instruct-2507-q4_K_M` | 34/38 (89 %) | 0,72 s | 2,78 s | 0,34 s |

Estos tiempos corresponden a inferencia con modelo cargado. No incluyen capturar/transcribir la voz, ejecutar Spotify ni generar/reproducir la voz de Capri. El primer texto tampoco equivale al comienzo del audio: Capri prepara una respuesta hablada completa para sincronizar voz y texto.

## Método

Se realizaron 228 solicitudes reales a Ollama desde las clases de Capri, sin ejecutar acciones en el PC: 180 para comparar el programa inicial y 48 conversaciones adicionales con una instrucción de personalidad más breve. Dos rondas, invirtiendo el orden de los modelos en la segunda. Contexto 2048, hasta 100 tokens de salida, temperatura 0 para interpretación y 0,45 para conversación; razonamiento desactivado en Qwen.

Cada modelo recibió 22 instrucciones por ronda. Tres se resolvieron mediante la protección compartida de negaciones/citas; se excluyen de los 38 casos de la tabla para no atribuir sus aciertos ni su rapidez al modelo. Incluyéndolas, los resultados fueron 36/44, 34/44 y 40/44 respectivamente. Las instrucciones usan el intérprete semántico directamente para medirlo; la aplicación también dispone de un parser determinista, por lo que estas tasas no representan todas las órdenes de la interfaz.

Cada modelo respondió ocho tipos de conversación por ronda: identidad, nombre desconocido, posible fallo de escucha, música sin datos, historia corta, charla informal, título inglés y nombre informado en el historial. Los tiempos conversacionales de la tabla corresponden a la instrucción final breve; las instrucciones de acciones no cambiaron. Se mantuvieron las respuestas sin seleccionar las más favorables.

## Calidad y límites observados

Qwen 4B resolvió más formas de pedir canciones siguientes/anteriores y produjo historias con final más consistentes. Llama fue más rápido y, con la instrucción final, se presentó correctamente como Capri. Qwen 2B mostró más confusión de identidad y una respuesta llegó al límite de 100 tokens. Los tres pueden inventar explicaciones técnicas o datos musicales y fallaron al recuperar el nombre de la conversación de prueba: ninguno merece una promesa de memoria o comprensión perfecta. Estas observaciones son una revisión manual de pocos ejemplos, no una puntuación universal de inteligencia.

Las 228 solicitudes terminaron sin errores de transporte o ejecución. Esto comprueba esta sesión; no demuestra estabilidad durante días de uso. No se midió reconocimiento del nombre Capri ni se grabó el micrófono del usuario.

## Por qué difieren en este equipo

Ollama informó todo el modelo cargado en GPU para Llama (~2,32 GB) y Qwen 2B (~1,60 GB). Para Qwen 4B informó ~3,23 GB totales y ~2,34 GB en GPU: parte del trabajo quedó fuera de ella durante la prueba. Con una GTX 1650 de 4 GB compartida con el escritorio, esto contribuye a la espera. Tener menos parámetros tampoco garantiza mayor velocidad: Qwen 2B fue más lento pese a ocupar menos memoria.

Las primeras cargas fueron variables: Llama 17,03/4,62 s, Qwen 2B 6,17/3,69 s y Qwen 4B 7,16/3,68 s. La primera carga de Llama incluye efectos iniciales del servicio/caché; no se confunde con su latencia habitual. Solo hay dos muestras por modelo.

El formato y los campos de medición siguen la [API oficial de Ollama](https://docs.ollama.com/api/chat); la desactivación del razonamiento sigue su [documentación de thinking](https://docs.ollama.com/capabilities/thinking).

## Selección

Se configura **Llama 3.2 3B** en este PC, considerando la prioridad expresada de rapidez y estabilidad. Qwen 4B permanece instalado y seleccionable en Ajustes si se prefiere mayor calidad. No se borran modelos ni se cambia el reconocimiento de voz al elegir un LLM.

La recomendación está medida para este equipo y su carga de escritorio. No se anuncia una selección óptima automática para cualquier computador: en otro equipo se deben comparar sus tiempos y resultados antes de sustituir una elección del usuario.
