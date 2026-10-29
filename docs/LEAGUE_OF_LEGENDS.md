# Cola de League of Legends

Abre el cliente de LoL, prepara la sala y elige el modo y los roles allí. Capri utiliza esa selección; no crea una sala ni cambia el tipo de partida.

En el menú radial, abre **Más → League of Legends**. También puedes escribir o decir:

| Petición | Resultado |
| --- | --- |
| «Busca partida en LoL» / “Find a match in LoL” | Inicia la búsqueda en la sala preparada. |
| «Busca partida en LoL y acepta por mí» | Busca y acepta automáticamente los ready-checks de esa búsqueda. |
| «Activa la aceptación automática del LoL» | Vigila las colas actuales y futuras, aunque las inicies directamente en LoL. La preferencia se guarda. |
| «Acepta la partida» / “Accept the match” | Acepta el ready-check actual, si existe. |
| «Cancela la cola» / “Cancel the queue” | Cancela una búsqueda que siga en curso. |
| «No aceptes más partidas» / “Disable auto accept in LoL” | Detiene toda aceptación automática y guarda la opción desactivada. |

Portugués: «busque uma partida no LoL», «aceite a partida», «cancele a fila». Japonés: 「マッチを検索して」「マッチを承諾して」「マッチングをキャンセルして」。 Los resultados se muestran en el idioma seleccionado en Capri, sin necesitar una traducción del modelo.

Activa **Más → League of Legends → Activar aceptación automática** o la casilla **Ajustes → IA y servicios → Aceptar partidas automáticamente, también desde LoL**. Basta hacerlo una vez: la elección se guarda y se recupera al abrir Capri. A partir de entonces, busca desde LoL o desde Capri; puede aceptar también una cola que ya estuviera en marcha cuando activas la vigilancia. La opción viene desactivada inicialmente. Activarla no inicia una búsqueda.

El estado de conexión y vigilancia aparece debajo de la casilla. Durante la búsqueda se consulta el cliente cada 250 ms; la aceptación se envía desde un trabajador independiente, sin esperar a una orden de voz ni al modelo. Es un intervalo de consulta, no una garantía de latencia: depende de la respuesta del cliente.

Puedes ir al baño mientras espera: si llega el ready-check, Capri lo acepta. Si otra persona no acepta y el cliente vuelve a buscar, sigue pendiente del siguiente. Durante selección de campeón y partida no actúa y conserva la vigilancia para la próxima cola. Si LoL se cierra o pierde la conexión, vuelve a intentar conectarse; también puedes abrir LoL después de Capri.

Desactivar la casilla o cerrar Capri detiene la vigilancia. Cerrar Capri no cancela la cola de LoL. Una partida ya encontrada se rechaza desde el propio cliente. Si pides cancelar cuando ya hay ready-check, Capri omite esa aceptación; la vigilancia guardada continúa disponible para una nueva búsqueda.

«Busca partida en LoL y acepta por mí» sigue disponible para una sola búsqueda: si no activaste la vigilancia permanente, se detiene al llegar a selección de campeón, salir de la cola o perder la conexión.

## Conexión y límites

Capri se comunica únicamente con la API local del cliente en `https://127.0.0.1`. Descubre el puerto y el token temporal del proceso de LoL o de su `lockfile`; no pide tu contraseña de Riot, no guarda el token y no lo envía a Ollama. No usa proxies ni sigue redirecciones. El certificado autofirmado se admite exclusivamente para ese origen local fijo.

Si el cliente no aparece, ábrelo con los mismos permisos de Windows que Capri. Si hay varios clientes, deja uno solo. Si LoL rechaza una búsqueda, revisa los roles, el líder del grupo y los avisos del cliente. Capri distingue una solicitud enviada de un resultado confirmado; no informa una aceptación exitosa solo por haber enviado la petición.

Esta integración no selecciona campeones ni controla el juego. La [League Client API no tiene soporte oficial para aplicaciones de terceros](https://developer.riotgames.com/docs/lol#league-client-api) y puede cambiar entre versiones. Las pruebas de desarrollo simulan el cliente: no inician colas ni aceptan partidas reales.

## Desarrollo

`src/league.py` limita métodos y rutas a estas operaciones:

- `GET /lol-gameflow/v1/gameflow-phase`
- `GET /lol-lobby/v2/lobby`
- `POST` y `DELETE /lol-lobby/v2/lobby/matchmaking/search`
- `GET /lol-matchmaking/v1/ready-check`
- `POST /lol-matchmaking/v1/ready-check/accept`

La interpretación exige una petición completa. El modelo de conversación no recibe acceso genérico a endpoints. El seguimiento usa un trabajador cancelable, y los avisos vuelven a Tk a través de la cola de eventos.

Riot solicita [registrar las aplicaciones que utilizan el cliente local](https://developer.riotgames.com/docs/lol#league-client-api) en su portal. Este repositorio no afirma contar con aprobación ni registro de Riot; el responsable de una distribución debe realizar ese trámite con su propia cuenta.
