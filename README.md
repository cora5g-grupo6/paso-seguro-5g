# Paso Seguro 5G

Alerta de crecidas en cruces de río, cañones y caminos. Grupo 6 (CORA 5G) · Hackatón Centroamericano de Innovación 5G · PCII Coronado, 5 al 9 de octubre de 2026.

La cámara 5G mira la regla y el servidor de borde decide **LIBRE, CUIDADO o CERRADO**. Después avisa por cuatro vías:
- luces y zumbador del ESP32, sin internet;
- el teléfono del guía, con voz y video;
- el turista, en español e inglés;
- los mapas: Waze y Google.

- **Qué tenemos y qué falta para conectarlo**, en simple: **[ESTADO.md](ESTADO.md)**.
- El plan, los riesgos, las preguntas para la PCII y el guion de la demo: **[PLAN.md](PLAN.md)**.

```
paso-seguro-5g/
├── PLAN.md                  arquitectura, equipos, plan día por día, preguntas, riesgos, latencia
├── edge/                    servidor de borde (Python 3.11 + FastAPI)
│   ├── app/                 estado.py (máquina de estados) · vision/ · feeds/ · alertas.py · imn.py · sistema.py · main.py
│   ├── static/              tablero (/), guía (/guia), turista (/turista), calibrar (/calibrar); sin internet
│   ├── config/              cruce.json (el cruce y su polilínea) · calibracion.json (la cámara)
│   ├── tests/               134 tests (pytest)
│   ├── Dockerfile · docker-compose.yml · mosquitto/ · deploy/k8s.yaml · .env.example
│   └── correr_local.sh      arranca todo en una laptop, sin Docker
├── esp32/
│   ├── PasoSeguro/PasoSeguro.ino   sketch del flotador (sin librerías extra)
│   └── prueba_en_pc/        compila el sketch en la PC y lo prueba contra el borde
└── tools/                   simulador del ESP32, video de prueba, latencia, validador de feeds, relé de cámara
```

---

## 1. Correrlo hoy en una laptop, sin hardware

Hace falta **Python 3.11** (o [`uv`](https://docs.astral.sh/uv/)). `ffmpeg` es opcional.

```bash
cd edge && ./correr_local.sh
```

Ese comando:
- crea el entorno e instala las dependencias;
- copia `.env.example` a `.env`;
- genera el video de prueba;
- arranca el borde en **http://localhost:8000**.

| Página | Para qué |
|---|---|
| `/` | Tablero: estado, video, mapa, fuentes, latencia, eventos, feeds, lluvia del IMN y botones de ensayo |
| `/guia` | Teléfono del guía (XR20): alerta con sirena, voz, vibración y clip de video; botón «Cerrar el cruce» |
| `/turista` | Aviso para el turista en español e inglés (para un QR en el cruce) |
| `/calibrar` | Calibrar la cámara con 5 clics |

Para la demo completa sin hardware (video de prueba como cámara más el ESP32 simulado):

```bash
cd tools && ./demo_sin_hardware.sh
```

Para correr los tests:

```bash
cd edge && .venv/bin/python -m pytest
```

### Herramientas (`tools/`, con el Python de `edge/.venv`)

| Herramienta | Uso |
|---|---|
| `simular_sensor.py` | Simula el ESP32 por HTTP o MQTT. Escenarios: crecida, estable, oscilante, corte, flotador |
| `generar_video_prueba.py` | Video del tubo con agua teñida, regla, marca de referencia y una «persona» que cruza, más su calibración |
| `servir_rtsp.sh` | Sirve el video por la red: RTSP con mediamtx o, si no está, HTTP MPEG-TS con ffmpeg |
| `medir_latencia.py` | `/ping` (p50, p95, jitter), comparación con la nube y tiempo «el agua sube → llega la alerta» |
| `validar_feed.py` | Valida el feed de Waze contra la spec CIFS y el XSD oficial |
| `relay_camara.py` | Plan C de la cámara: empuja cuadros de una webcam al borde por HTTP |

---

## 2. Con el hardware

### ESP32

1. En Arduino IDE, elegir la placa **ESP32 Dev Module** (paquete «esp32 by Espressif»). No hace falta instalar librerías.
2. En `esp32/PasoSeguro/PasoSeguro.ino`, poner:
   - `WIFI_NOMBRE` y `WIFI_CLAVE` del CPE 5G;
   - `BORDE_HOST`, la IP del borde.
3. Cargar el sketch y abrir el Monitor Serie a 115200.
4. Calibrar: anotar `agua=` en seco y con el sensor mojado hasta arriba, y ponerlos en `AGUA_SECO` y `AGUA_LLENO`.
5. Mismo cableado que el kit CORA. El relé y el sensor magnético no se usan.

Para probar el sketch sin placa (lo compila con clang y habla con el borde de verdad):

```bash
cd esp32/prueba_en_pc && ./probar.sh
```

- `./probar.sh mqtt` prueba el modo MQTT.
- `PRUEBA_SIN_WIFI=1 ./probar.sh` prueba el modo local, sin red.

### Cámara

`CAMARA_FUENTES` lleva una lista separada por comas, en orden de preferencia. Por ejemplo:

```
CAMARA_FUENTES=rtsp://USUARIO:CLAVE@IP-CAMARA:554/RUTA,0,../tools/videos/rio_prueba.mp4
```

- Si se corta la primera fuente, el borde pasa sola a la siguiente: RTSP de la cámara 5G → webcam USB → video.
- En Mac, OpenCV no lee RTSP. El borde usa PyAV automáticamente (`CAMARA_LECTOR=auto`).
- Calibrar en `/calibrar`, en este orden:
  1. esquina de arriba del tubo;
  2. esquina de abajo;
  3. marca de 0 %;
  4. marca de 100 %;
  5. un clic dentro del agua.
- Maqueta recomendada:
  - colorante azul fuerte, fondo blanco mate y luz fija;
  - una marca magenta fija junto a la regla, para que la IA sepa si la cámara se movió.
- Personas:
  - `PERSONAS_METODO=movimiento` dentro de `PERSONAS_ZONA` es lo más seguro en una maqueta;
  - `hog` necesita una persona de cuerpo entero.

### MQTT

`docker compose` ya trae Mosquitto. Sin Docker hay dos opciones:
- `MQTT_ACTIVO=false`: solo HTTP, que alcanza para el ESP32;
- un broker en Python: `pip install amqtt && amqtt`.

Temas:
- `pasoseguro/<dispositivo>/sensor`: entrada (ESP32 → borde);
- `pasoseguro/<cruce>/estado`: salida retenida, con latido cada 2 s;
- `pasoseguro/<cruce>/alerta`: salida, una por evento.

---

## 3. Moverlo al MXIE

**Opción A · Docker en el MXIE (o en una VM de él)**

```bash
# en una máquina con Docker (desde Mac con chip Apple: agregar --platform linux/amd64)
cd edge && docker build -t paso-seguro-borde:0.1 .
docker save paso-seguro-borde:0.1 | gzip > borde.tar.gz
# copiar al MXIE borde.tar.gz y la carpeta edge/ (sin .venv), y ahí:
docker load < borde.tar.gz
cp .env.example .env   # CAMARA_FUENTES con la URL RTSP de la cámara 5G, URL_PUBLICA con la IP del MXIE
docker compose up -d
curl http://localhost:8000/salud
```

**Opción B · Kubernetes**, si el MXIE expone Kubernetes en vez de Docker:
1. Importar la imagen en el nodo.
2. Ajustar el ConfigMap de `edge/deploy/k8s.yaml`.
3. Correr `kubectl apply -f edge/deploy/k8s.yaml`.

Queda así: tablero en `:30080` y MQTT en `:31883`.

**Opción C · No se puede usar el MXIE:** la laptop hace de borde, conectada a la red 5G con el dongle DGRx501e o el CPE. Se corre `correr_local.sh` y no cambia nada más.

**Después, en cualquiera de las tres:**
- En el XR20 del guía, abrir `http://IP-DEL-BORDE:8000/guia` y tocar «Activar alertas».
- En el ESP32, poner `BORDE_HOST` = IP del borde.

Ensayo de RTSP real en Linux sin la cámara:

```bash
docker compose --profile simulacion up -d
```

Con ese perfil, mediamtx y ffmpeg sirven el video de prueba en `rtsp://rtsp:8554/rio`.

---

## 4. Configuración

Todo va en `edge/.env`. Los comentarios de [`edge/.env.example`](edge/.env.example) explican cada variable. **Sin secretos en el repo:** `.env` no se versiona. Las principales:

| Variable | Por defecto | Qué hace |
|---|---|---|
| `CAMARA_FUENTES` | video de prueba | Fuentes de video en orden de preferencia |
| `UMBRAL_CUIDADO` / `UMBRAL_CERRADO` | 40 / 70 | Umbrales (% de la regla) |
| `BAJADA_S` | 30 | Segundos sostenidos para bajar un escalón (en un río real, 900 o más) |
| `TASA_CUIDADO` | 15 | %/min de subida que ya es CUIDADO |
| `LLUVIA_1H_MM` / `LLUVIA_3H_MM` | 10 / 25 | Lluvia del IMN que sube a CUIDADO |
| `MODO_DEMO` | true | Habilita `/api/demo/*`. **Poner false fuera de los ensayos.** |
| `URL_PUBLICA` | — | IP o nombre del borde, para los enlaces de las alertas |
| `WEBHOOK_URLS` | — | Webhooks genéricos |
| `N8N_ACTIVO` / `N8N_WEBHOOK_URL` | false | n8n **solo de prueba**: la URL tiene que tener «prueba» o «test» |
| `PTT_ACTIVO` | false | Stub de Team Comms: deja cada alerta en `datos/ptt_pendientes.jsonl` |

El cruce (nombre, río, calle tal como figura en Waze, polilínea y equipos) va en `edge/config/cruce.json`. **El punto actual es de ejemplo.** Ver PLAN.md, sección 8.

---

## 5. API

| Ruta | Para qué |
|---|---|
| `GET /ping` | Hora del servidor, para medir latencia |
| `POST /api/sensor` | Lectura del ESP32. Responde el estado decidido: `estado`, `color`, `buzzer`, `alarma_persona` |
| `GET /api/estado` · `GET /api/stream` (SSE) | Estado completo / eventos en vivo: `estado`, `alerta`, `latencia`, `envios`, `ack` |
| `GET /api/eventos` · `POST /api/alertas/{id}/ack` | Historial de alertas / confirmación del teléfono (mide la entrega) |
| `POST /api/latencia/cliente` · `GET /api/latencia` | Latencias de cada tramo |
| `POST /api/manual` | Cierre manual `{"estado": "CERRADO"}`; con `null` se quita. Nunca abre un cruce en peligro |
| `GET /video.mjpg` · `GET /api/camara/captura.jpg` | Video en vivo con la lectura dibujada / captura |
| `POST /api/camara/frame` | Recibe cuadros JPEG (plan C de la cámara) |
| `GET/POST /api/camara/calibracion` | Calibración de la visión |
| `GET /api/imn` | Lluvia del IMN: estación más cercana y tabla de las 8 |
| `GET /feeds/waze.json` · `/feeds/waze.xml` | Feed CIFS (`?envuelto=1` da la otra variante de JSON de la documentación) |
| `GET /feeds/estado.geojson` · `/feeds/google-cierres.geojson` · `/feeds/validacion` | GeoJSON del estado / carga puntual de Google / validación en vivo |
| `POST /api/demo/{nivel,lluvia,persona,reiniciar}` | Solo con `MODO_DEMO=true` |

---

## 6. Waze y Google Maps

- **Waze (CIFS):**
  - CERRADO va como `ROAD_CLOSED` / `ROAD_CLOSED_HAZARD` y CUIDADO como `HAZARD` / `HAZARD_WEATHER_FLOOD`.
  - Hay JSON y XML. El XML se valida contra el XSD oficial, copiado sin cambios en `edge/app/feeds/cifsv2.xsd`.
  - El `id` y el `starttime` no cambian mientras dura el cierre.
  - El `endtime` se estima en bloques de 3 h, que se extienden de a uno. Al reabrir, queda fija la hora real y el incidente sigue 1 h más en el feed.
  - **Publicarlo de verdad requiere un socio oficial de Waze for Cities**, por ejemplo el MOPT. Durante el hackatón el feed se genera, se valida y se muestra en el tablero.
- **Google Maps:**
  - Los cierres del feed de Waze llegan solos a Google Maps.
  - `google-cierres.geojson` sigue el esquema de carga puntual de Google Maps Content Partners. Solo lleva cierres: Google no tiene tipo «inundación».

---

## 7. Alertas

| Canal | Estado |
|---|---|
| Tablero, guía y turista (SSE, local) | Funciona sin internet |
| ESP32 (respuesta HTTP o MQTT) | Funciona sin internet; si pierde el borde, pasa a modo local |
| Webhook genérico | Listo, apagado si `WEBHOOK_URLS` está vacío |
| n8n | Apagado por defecto; solo URL de prueba y cada alerta marcada `"prueba": true`. **Nunca producción.** |
| PTT/PTV (Nokia Team Comms) | Stub documentado en `app/alertas.py` hasta conocer la API. Plan B: `/guia` |

---

## 8. Qué se probó (5 de octubre, en una laptop Mac sin 5G)

| Probado | Resultado |
|---|---|
| Máquina de estados, feed CIFS (spec y XSD oficial), API, visión, IMN y alertas | 134 tests en verde |
| Revisión independiente del código | Problemas corregidos, con 21 tests nuevos: reinicio con el cruce cerrado, NaN en los datos, disco lleno, guardia de n8n, sirena del guía |
| Video de prueba por red (HTTP MPEG-TS con PyAV) → visión → decisión | Error medio de 0,3 puntos sobre 1500 cuadros; 15 cuadros/s |
| Simulador del ESP32 por HTTP y por MQTT (broker amqtt local) | OK, ida y vuelta de 2–3 ms |
| Sketch del ESP32 compilado en PC: HTTP, MQTT y sin Wi-Fi | OK. Se corrigió un bloqueo de 15 s al arrancar sin Wi-Fi |
| Tablero, guía (alerta y confirmación) y turista en el navegador | OK |
| IMN real, comparación con internet y feeds en vivo | OK |

**No probado:**
- en la placa ESP32 real;
- con la cámara 5G y la red NDAC;
- en el MXIE;
- con RTSP a través de mediamtx (sí con HTTP);
- con Docker, porque esta Mac no lo tiene: el Dockerfile y el compose solo se validaron por sintaxis;
- la API de Team Comms.
