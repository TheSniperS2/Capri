# Medios de la portada

Esta galería corresponde al código actual de `main`. Los fondos y títulos son una composición de presentación; los personajes, controles y animaciones proceden de los recursos y renderizadores del proyecto. No se capturó el escritorio ni se incluyeron datos de una sesión real del usuario.

| Archivo | Procedencia |
| --- | --- |
| `portada.png` | Composición tipográfica con la ilustración activa `capri-asomo-fiel-v3.png`. |
| `modo-pantalla.png` | Canvas del modo pantalla, mediante `Capri.animar`. |
| `modo-personaje.png` | Sprite del personaje preparado por `Companera`. |
| `asomo.gif` | `AsomoCurioso.dibujar`, con dos posiciones de cursor simuladas. |
| `llamada.png` | `LlamadaCapri`, con un guion incluido de Talia y la voz desactivada. |
| `menu-radial.png` | Menú real `MenuRadial` en modo personaje. |
| `apagado.png` | `LienzoApagado` en un fotograma de la secuencia. No solicita un apagado. |
| `despedida.gif` | Traslado, cámara con gestos y mano/estrella, usando los renderizadores de la aplicación y actividad de habla simulada. No contiene audio. |

Las ventanas de trabajo se mantienen ocultas. No se controlan otras aplicaciones, se consulta el cliente de LoL ni se reproduce sonido. Se usan ajustes temporales de prueba, no las preferencias instaladas.

## Regenerar

Desde el repositorio en Windows, con Python 3.12 y las dependencias de `requirements.txt` instaladas:

```powershell
python scripts/generar_medios_readme.py
```

Las fuentes Chakra Petch incluidas en el proyecto se usan tanto en los rótulos como en los controles. El script exporta únicamente Canvas propios y genera las composiciones con Pillow. Los recursos del personaje conservan la procedencia y los derechos descritos en [arte y animación](../../ARTE_ANIMADO.md) y [avisos de terceros](../../../THIRD_PARTY_NOTICES.md).
