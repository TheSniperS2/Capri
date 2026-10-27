# Capri

Asistente de escritorio para Windows con chat, activación por voz y acciones sobre aplicaciones compatibles. Inspirado en Capri de *Cyberpunk: Edgerunners*, con una ventana flotante y una personalidad configurable.

Proyecto de aficionado, independiente y no oficial. La voz es sintética y la interfaz usa referencias visuales del personaje; no es un modelo 3D ni reproduce el timbre exacto de la actriz.

## Instalar y usar

Necesitas **Windows 10 u 11** y **Python 3.12 de 64 bits**, con Tcl/Tk. No hace falta programar, crear una cuenta de API ni introducir claves.

1. Abre la sección **Releases** del repositorio y descarga **Abrir Capri.pyw**.
2. Abre el archivo. Si Windows no lo asocia a Python, ejecútalo con `pythonw "Abrir Capri.pyw"`.
3. Espera la preparación inicial: descarga dependencias, modelos locales de reconocimiento y referencias visuales.
4. Selecciona tu micrófono en **Ajustes** y prueba **«Capri, abre la calculadora»**.

Si todavía no hay una Release publicada, descarga el código y genera el lanzador con `python empaquetar.py`; aparecerá en `dist/`.

La primera apertura necesita internet. Capri crea su entorno y un acceso directo, sin permisos de administrador ni inicio automático con Windows. Los archivos personales quedan en **`%LOCALAPPDATA%\Capri`**, fuera del repositorio.

### Conversación y voz

- Las órdenes directas funcionan sin un modelo de conversación.
- Para conversar, usa **Ajustes → Activar IA local**. Prepara Ollama y `llama3.2:3b`, o reutiliza un modelo local compatible.
- El reconocimiento predeterminado usa Whisper multilingüe. También puedes elegir Vosk español, más rápido.
- La voz natural requiere internet; puedes desactivarla para usar la voz de Windows.

Los modelos se descargan por separado. La primera carga puede tardar más; la latencia depende del equipo.

## Qué puedes pedir

| Petición | Resultado |
| --- | --- |
| «Capri, abre una pestaña en Opera GX» | Abre una pestaña |
| «Búscame memes de Cyberpunk» | Abre la búsqueda en Opera GX |
| «Abre Descargas» | Abre la carpeta configurada en Windows |
| «Abre Spotify» | Abre la aplicación |
| «Reproduce la música» | Reanuda la sesión actual sin buscar otra canción |
| «Salta la canción» o «pon la música siguiente» | Pide la siguiente pista de la cola |
| «Pon la canción anterior» | Pide la pista anterior |
| «Pausa Spotify» | Pausa la sesión actual |
| «Qué canción está sonando» | Consulta el estado que comunica Spotify |
| «Reproduce Never Fade Away en Spotify» | Busca e intenta reproducir ese título |
| «Pon mi playlist Cyberpunk» | Busca la lista en Tu biblioteca o usa su enlace vinculado |

Puedes decir **«Capri» y la instrucción en una misma frase**, sin esperar un aviso. También puedes usar **F8** o el botón **Hablar**. Durante la respuesta, F8 o Hablar interrumpen la voz; **Esc** la detiene. La escucha del nombre se pausa mientras Capri habla o los Ajustes están abiertos.

Para una playlist privada, usa **Ajustes → Vincular playlist de Spotify** y pega su enlace. Debe ser accesible desde la cuenta iniciada; no hace falta hacerla pública.

## Requisitos de las integraciones

- **Opera GX u Opera:** pestañas y búsquedas web.
- **Spotify de escritorio con sesión iniciada:** controles multimedia y playlists.
- **Ollama con un modelo local:** conversación libre.

Capri ejecuta un conjunto definido de acciones; no controla cualquier aplicación ni entiende cualquier instrucción. Las búsquedas abren páginas, pero no leen ni resumen los resultados. La reproducción por título o playlist depende de los controles accesibles que exponga Spotify. Si una acción no se confirma, lo informa.

## Privacidad

- El reconocimiento es local y el audio permanece temporalmente en memoria, sin grabaciones en archivos.
- La conversación con Ollama se procesa en el equipo; el historial dura mientras la aplicación está abierta.
- Edge TTS envía a Microsoft el texto de las respuestas para sintetizarlo.
- Las búsquedas envían la consulta al servicio correspondiente.
- Ajustes, playlists, diagnósticos, modelos y recursos descargados están excluidos de Git.
- El modelo de conversación no ejecuta código ni comandos de consola.
- No hay un nombre personal del usuario fijado en los saludos ni en la personalidad.

Consulta la [guía de uso y solución de problemas](docs/USO.md).

## Desarrollo

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe empaquetar.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El empaquetado genera **`dist/Abrir Capri.pyw`** y **`dist/Capri.zip`**. No edites el código embebido del lanzador: modifica los módulos de `src/` y vuelve a generar los archivos. Las distribuciones no incluyen configuraciones personales ni pesos de modelos.

```text
Capri/
├── src/                 # Aplicación, voz, órdenes e integraciones
├── tests/               # Pruebas de regresión
├── installer/           # Plantilla del lanzador
├── assets/              # Icono distribuido y atribuido
├── docs/                # Uso, contribuciones y publicación de versiones
├── .github/workflows/   # Pruebas en Windows y creación de Releases
├── empaquetar.py        # Generador de distribuciones
├── requirements.txt
├── README.md
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

Las pruebas verifican órdenes, cancelación, aislamiento de argumentos, interfaz y empaquetado, con audio y controles multimedia simulados. No sustituyen una prueba real de micrófono o Spotify. La personalidad se define en `src/core.py`.

Para colaborar, consulta [CONTRIBUTING.md](CONTRIBUTING.md). Los cambios y limitaciones conocidos están en [CHANGELOG.md](CHANGELOG.md).

## Licencia y referencias

El código original usa la [licencia MIT](LICENSE). El personaje, las imágenes, el icono derivado y las marcas de terceros conservan sus propios derechos y quedan excluidos de esa licencia. Consulta [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
