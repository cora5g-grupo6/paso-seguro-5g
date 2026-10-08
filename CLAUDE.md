# Paso Seguro 5G · Contexto para Claude

Este archivo es para cualquier Claude (o persona) que abre el proyecto por primera vez. Explica qué es, dónde está cada cosa, cómo validarlo y qué reglas seguir.

## Qué es

Proyecto del **Grupo 6 (CORA 5G)** en el **Hackatón Centroamericano de Innovación 5G** (PCII, Vázquez de Coronado, Costa Rica, del 5 al 9 de octubre de 2026). El pitch al jurado es el viernes 9.

**En una frase:** un sensor mide el nivel del río en un vado (cruce sin puente). Un servidor de borde, dentro de la red 5G del Testbed, decide si el cruce está **LIBRE, en CUIDADO o CERRADO** y avisa por varios canales:
- al guía (página `/guia` en el teléfono XR20, con sirena y voz);
- al turista (`/turista`, por QR, en español e inglés);
- al mapa (feed oficial de Waze, CIFS);
- con una alarma local en el cruce, que funciona aunque no haya internet.

Primer piloto propuesto: el vado del río Vainilla, en la Ruta Nacional 623 (Lepanto, Puntarenas), que administra el Conavi.

## Primero: validar (sin hardware, unos 2 minutos)

```bash
bash tools/validar.sh
```

Crea el entorno de Python si falta (hace falta Python 3.11 o más nuevo) y comprueba cinco cosas:
1. las 165 pruebas automáticas;
2. que el borde arranca en modo demo;
3. el flujo LIBRE → CUIDADO → CERRADO y que no reabre de golpe;
4. los feeds de Waze contra la spec CIFS y el XSD oficial;
5. que un «teléfono del guía» simulado confirma 3 avisos.

Tiene que terminar en `RESULTADO: todo en verde ✅`.

Para ver la demo completa en el navegador: `bash tools/demo_sin_hardware.sh` y abrir http://localhost:8000 (también `/guia` y `/turista`).

## Dónde está cada cosa

| Ruta | Qué hay |
|---|---|
| `docs/DOCUMENTO-TECNICO-jurado.md` | **Documento técnico para el jurado** (también en PDF en `entregables/`). Empezar por aquí |
| `docs/PITCH-viernes-9.md` | Guion minuto a minuto, indicadores y banco de preguntas |
| `docs/PREGUNTAS-DIFICILES-jurado.md` | Las 20 preguntas más difíciles con su respuesta, y los puntos débiles |
| `docs/PENDIENTES-pitch-viernes-9.md` | Qué falta y quién lo hace |
| `docs/INVESTIGACION-mercado-costos-casos.md` | Costos por punto, mercado, quién paga, por qué 5G y casos de otros países, con fuente y fecha en cada cifra |
| `README.md` | Cómo correr cada parte |
| `ESTADO.md` | Estado del prototipo y cómo quedó cableado el sensor |
| `PLAN.md` | Plan, reglas del hackatón, lo que pidió el mentor y hallazgos con fuentes |
| `edge/` | Servidor de borde (Python 3.11 + FastAPI). Reglas de decisión en `edge/app/estado.py`; rutas en `edge/app/main.py`; configuración en `edge/app/config.py`; pruebas en `edge/tests/` |
| `edge/static/` | Páginas: tablero, guía, turista, calibrar y `/medir` (ping 5G contra 4G) |
| `esp32/PasoSeguro/` | Programa de la ESP32 (ultrasónico, flotador, alarma local, Wi-Fi). La clave del Wi-Fi va en `secretos.h`, que **no** está en el repo; ver `secretos.h.example` |
| `arduino_uno/` | Variante de respaldo con Arduino UNO |
| `tools/` | `validar.sh`, `medir_latencia.py` (ping, alerta y `--guia`), `medir_precision.py` (5 marcas × 10 lecturas), `validar_feed.py`, `demo_sin_hardware.sh` y `prueba_conectividad.sh` |
| `entregables/` | PDF del documento técnico (el video de la prueba no está en el repo por su tamaño) |

## Reglas de decisión (las que hay que validar)

Están en `edge/app/estado.py` y se configuran en `edge/app/config.py`.
- **CUIDADO** con 40 % o más y **CERRADO** con 70 % o más. Sube apenas cruza el umbral.
- Para bajar, el nivel tiene que quedar `bajada_s` segundos por debajo: 30 s en la demo, 900 s o más en un río real. Baja **de a un escalón**.
- Una **subida rápida** de 15 %/min o más, o lluvia fuerte del IMN, suben al menos a CUIDADO.
- El **flotador** activado manda CERRADO.
- **Sin datos de nivel, nunca baja y queda al menos en CUIDADO** (modo degradado): el sistema falla del lado seguro.
- Una persona puede subir el estado, nunca bajarlo.

## Qué está medido y qué falta (al 8-oct-2026)

| Indicador | Resultado | Estado |
|---|---|---|
| ESP32 → borde por Wi-Fi + 5G (FastMile, red privada del Testbed) | p50 de 31 ms y p95 de 44 ms en el tablero (7-oct, 11:42); en la prueba con cartón, 22–60 ms, con picos de 150–210 ms | OBTENIDO |
| Borde → servidor en internet (HTTPS) | p50 de 1.738 ms, unas 50 veces más que decidir en el borde | OBTENIDO |
| Prueba con cartón | 78 cm → 29 cm = 0 % → 100 % | OBTENIDO |
| Pruebas automáticas | 165 en verde | OBTENIDO |
| Feed de Waze | El JSON cumple CIFS y el XML pasa el XSD oficial | OBTENIDO |
| Aviso al XR20 por 5G con la red cargada | — | PREVISTO |
| 5G contra 4G (200 muestras de cada uno) | — | PREVISTO |
| Precisión del nivel (5 × 10) | — | PREVISTO |
| Costo por punto | US$1.135–2.195 instalado y US$305–860 al año | OBTENIDO (estimación con fuentes) |

## Cómo validar cada afirmación

| Afirmación | Cómo comprobarla |
|---|---|
| «Decide LIBRE, CUIDADO o CERRADO con histéresis y modo seguro» | `edge/app/estado.py` y `edge/tests/test_maquina_estados.py`; paso 3 de `validar.sh` |
| «165 pruebas en verde» | `cd edge && .venv/bin/python -m pytest -q` |
| «El feed de Waze pasa el XSD oficial» | paso 4 de `validar.sh` o `tools/validar_feed.py` |
| «El aviso llega al teléfono del guía y confirma la recepción» | paso 5 de `validar.sh`; en el XR20 real: `tools/medir_latencia.py --guia xr20` con `/guia?id=xr20` abierta |
| «La alarma local funciona sin red» | `esp32/PasoSeguro/PasoSeguro.ino`: modo local, `luces()` y `buzzer()` |
| Costos, mercado, leyes y casos | `docs/INVESTIGACION-mercado-costos-casos.md`: cada cifra tiene enlace y fecha, y lo estimado está marcado EST o CALC |

## Reglas de trabajo

- **Sin secretos en el repo.** Claves del Wi-Fi en `esp32/PasoSeguro/secretos.h`; claves del borde en `edge/.env`. Los dos están en `.gitignore`. No usar credenciales de la red ni de servicios de la PCII.
- **Honestidad:** cada cifra dice si está OBTENIDA o PREVISTA. Lo que no está medido se dice como pregunta abierta. No prometer *network slicing* (en el laboratorio hay un solo slice).
- **Waze:** el feed está listo, pero solo lo publica un socio oficial (Conavi o MOPT). No publicarlo por nuestra cuenta.
- Las rutas `/api/demo/*` existen solo con `MODO_DEMO=true`. **En el prototipo, la API del borde no pide clave por dispositivo**; para el piloto, una clave por sensor y TLS.
- Textos para el equipo: en español, claros y cortos. Horas de Costa Rica.
- No hacer commit ni push sin que el equipo lo pida.

## Puntos débiles conocidos

Están en `docs/PREGUNTAS-DIFICILES-jurado.md`, sección B. Los más importantes:
- el hardware del prototipo es frágil (cables de prueba, convertidor de nivel sin soldar);
- faltan las mediciones de 5G contra 4G y del aviso en el XR20;
- nadie de afuera (Conavi, un guía) lo validó todavía;
- el flotador no está conectado en la demo.

## Si te piden validar el proyecto

1. Correr `bash tools/validar.sh` y reportar el resultado.
2. Leer `edge/app/estado.py` y revisar que las reglas de arriba se cumplan, buscando casos borde.
3. Revisar que cada cifra del documento técnico coincida con su fuente en la investigación.
4. Reportar en español lo que no cuadra, con el archivo y la línea.
