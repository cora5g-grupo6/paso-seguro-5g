# Paso Seguro 5G · Documento técnico

**Grupo 6 · CORA 5G** · Hackatón Centroamericano de Innovación 5G · PCII, Vázquez de Coronado · 9 de octubre de 2026

**Equipo:** Stuart Rojas Barquero y Wladyslaw Labuda (líderes de equipo) · Jorge Eduardo Mejía Cabrera (datos e IA) · Randall Arturo Herradora Fallas (negocio y modelo de negocio) · Eddy Cruz Arroyo (investigación) · Aina Ruiz de Azúa Cladera.

> **En una frase:** un sensor mide el nivel del río en un vado. Un servidor de borde, dentro de la red 5G, decide si el cruce está LIBRE, en CUIDADO o CERRADO, y avisa al guía, al turista, al mapa (Waze) y con una alarma en el sitio, aunque no haya internet.

---

## 1. Resumen

| Tema | Detalle |
|---|---|
| **Problema** | En Costa Rica miles de vecinos y turistas cruzan ríos sin puente. Un río puede crecer en minutos y quien está por cruzar no se entera. |
| **Evidencia** | Vado del río Vainilla (Ruta Nacional 623, Lepanto): «aproximadamente 500 personas» afectadas, «dos o tres carros quedan atascados cada semana y al menos uno es arrastrado mensualmente» (La Nación, 14-sep-2024). En 2024 murió ahí un hombre de 79 años. En 2026, cabezas de agua mataron a un guía en el río Barú (30-ago) y a una turista en Rincón de la Vieja (13-sep). |
| **Solución** | **Mide** (ultrasónico, más flotador en el punto real), **decide** en el borde (reglas con histéresis, subida rápida y modo seguro sin datos) y **avisa** (página del guía con sirena y voz, página del turista en español e inglés, feed oficial de Waze y alarma local). |
| **Resultado** | Flujo completo funcionando con el sensor real en la red del Testbed. Del sensor al borde, por la red: **p50 de 31 ms y p95 de 44 ms** (7-oct). **165 pruebas automáticas** en verde. El feed de Waze pasa la validación del esquema oficial. |
| **Costo** | **US$1.135–2.195** por punto instalado y **US$305–860** al año. Propuesta: US$120 al mes por punto, todo incluido. |
| **Petición** | Acceso prioritario al Testbed para medir la entrega del aviso con la red cargada frente a 4G, y contacto con el **Conavi** y la **CNE** para un piloto en el río Vainilla en la temporada de lluvias de 2027. |

---

## 2. El problema

- **Quién sufre:**
  - guías y grupos de turismo en ríos y cataratas;
  - vecinos y conductores que cruzan vados sin puente;
  - ambulancias: en Lepanto dan «una vuelta de dos horas por Jicaral» (La Nación, 14-sep-2024).
- **Escala:**
  - **Muertes en ríos:** la Cruz Roja contó 36 hasta el 13-oct-2025, dentro de 105 muertes acuáticas.
  - **Caminos expuestos:** el país tiene 30.534 km de caminos cantonales en lastre o tierra (MOPT, 2023).
  - **Inventario:** no hay un inventario nacional de vados. La Ley 10717 de 2025 obliga a hacerlo.
- **Por qué pasa:** el peligro no es el río alto, es **el río que sube mientras nadie lo mira**. La crecida viene de río arriba: en Upala, con el huracán Otto, el río creció «en 20 minutos cuando mucho» (Semanario Universidad, 2016).
- **Cómo se resuelve hoy:** mirar el río a ojo, preguntar a los vecinos o confiar en rótulos fijos. En la Ruta 623 «ni siquiera existen señales de advertencia» (La Nación, 30-oct-2024).

---

## 3. La solución

### 3.1 Cómo decide (servidor de borde)

La lógica está en `edge/app/estado.py`. Es determinista y está cubierta por pruebas automáticas.

| Regla | Valor de la demo | Para qué |
|---|---|---|
| CUIDADO | nivel ≥ 40 % | Avisar antes del peligro |
| CERRADO | nivel ≥ 70 % | Peligro: no cruzar |
| Subida rápida | ≥ 15 % por minuto → al menos CUIDADO | Avisar antes de llegar al umbral |
| Lluvia fuerte del IMN | → al menos CUIDADO | Lluvia río arriba |
| Flotador activado | → CERRADO | Respaldo físico |
| Para bajar | debe pasar 30 s por debajo (900 s o más en un río real) y baja **de a un escalón** | Evitar reabrir de golpe |
| **Sin datos del sensor** | **nunca baja; queda al menos en CUIDADO** (modo degradado) | Si algo falla, el sistema falla del lado seguro |
| Cierre manual | una persona puede subir el estado, nunca bajarlo | El guía o el operador pueden cerrar |

### 3.2 Cómo avisa

| Canal | Qué hace | Funciona sin internet |
|---|---|---|
| **Alarma local** (la ESP32 maneja una sirena y las luces roja, amarilla y verde) | Suena en el cruce | **Sí, y también sin red** |
| **Página del guía** (`/guia`, en el XR20) | Alerta con sirena, voz y vibración; botón para cerrar el cruce; confirma la recepción con su hora | Sí (red privada) |
| **Página del turista** (`/turista`, por QR) | Aviso en español e inglés | Sí, dentro de la red |
| **Tablero** (`/`) | Estado, nivel, latencia en vivo, mapa y lista de eventos con hora | Sí |
| **Waze y Google** (`/feeds/waze.json`, `.xml` y `/feeds/google-cierres.geojson`) | Cierre de la vía en el formato oficial CIFS | Necesita internet y un socio oficial (Conavi o MOPT) |

---

## 4. Arquitectura

```
[Sonda ultrasónica + flotador]
        │ (cable)
[ESP32 · alarma local · luces]  ──Wi-Fi──▶ [CPE FastMile 5G] ══5G n78 (NDAC, red privada del Testbed)══▶ [Servidor de borde]
                                                                                                             │
                                ┌──────────────────────────┬───────────────────────────┬────────────────────┤
                                ▼                          ▼                           ▼                    ▼
                       [Guía · XR20 /guia]      [Turista /turista (QR)]      [Tablero /]        [Waze y Google (con internet)]
```

| Componente | Qué es | Detalle |
|---|---|---|
| Sensor | Ultrasónico impermeable (SEN-CB0214, CRCibernética) | Mide de 25 cm a 4,5 m, de día y de noche, y con lluvia. Mide cada 200 ms y manda cada 1 s |
| Controlador | ESP32 en una placa «Agricultura IoT» de Ricardo Jiménez Guido | Busca solo los pines del sensor; en modo local decide sin red y hace sonar la alarma |
| Red | NDAC del Testbed 5G (n78), CPE Nokia FastMile, teléfonos XR20 | Salida a internet por RACSA, aparte de la red de la PCII |
| Borde | Python 3.11 con FastAPI. Hoy corre en una laptop dentro de la red 5G; es el mismo código que iría en el MXIE | API REST, SSE para alertas al instante, MQTT opcional, InfluxDB opcional |
| Datos externos | Lluvia del IMN (8 estaciones reales) | Con caché si se cae internet |
| Módulo siguiente | Cámara 5G con visión en el borde | Ya está en el código: 1,5 ms por cuadro |

---

## 5. Uso del Testbed 5G

| Lo que usamos | Para qué | Estado |
|---|---|---|
| CPE FastMile por la red privada 5G | Sacar al sensor y a la laptop-borde por 5G | ✅ El sensor real llega al borde (7-oct) |
| Salida a internet por RACSA | IMN, feeds y la comparación con la nube | ✅ `tools/prueba_conectividad.sh` dio OK (6-oct) |
| XR20 | Teléfono del guía | ⏳ Medición del aviso: ver la sección 6 |
| MXIE (borde del operador) | Correr el borde en un contenedor | Plan B en uso: laptop dentro de la red, con el mismo código |
| Slicing | — | **No lo prometemos.** En el laboratorio hay un solo slice, con prioridad por tipo de tráfico. El slicing lo configura el operador cuando se escala |

---

## 6. Resultados y mediciones

**Regla:** cada cifra dice si está OBTENIDA o PREVISTA. Lo que no está medido se presenta como pregunta abierta.

| Indicador | Meta | Resultado | Estado |
|---|---|---|---|
| Sensor real → borde, por la red (Wi-Fi + 5G) | < 100 ms | **p50 de 31 ms y p95 de 44 ms** en el tablero (7-oct, 11:42, se ve en el video); en la prueba con cartón, la mayoría entre 22 y 60 ms, con picos de 150–210 ms | OBTENIDO |
| Borde → servidor en internet (pedido HTTPS completo) | Comparar con decidir en el borde | p50 de 1.738 ms y p95 de 3.869 ms (7-oct, 11:42): **decidir en el borde es unas 50 veces más rápido que ir a la nube** | OBTENIDO |
| Prueba con cartón | Que el nivel cambie de punta a punta | 78 cm → 29 cm = 0 % → 100 %; el semáforo sigue al sensor | OBTENIDO |
| Ida y vuelta al borde (laptop, sin 5G) | — | 2,5 ms | OBTENIDO (laptop) |
| «El agua sube → la alerta llega a la pantalla» (laptop) | < 1 s | 4,3 ms (p50) | OBTENIDO (laptop) |
| Visión: análisis de un cuadro / del cuadro a la decisión | — | 1,5 ms / 37 ms (p50) | OBTENIDO (módulo cámara) |
| Pruebas automáticas | — | **165 en verde** | OBTENIDO |
| Feed de Waze | Validar contra lo oficial | El JSON cumple la spec CIFS y el XML pasa el XSD oficial | OBTENIDO |
| **Aviso en el XR20 por 5G, con la red cargada** | < 1 s | *pendiente (8-oct): `tools/medir_latencia.py --guia xr20 --ciclos 50`* | PREVISTO |
| **5G contra 4G** (200 muestras de cada uno) | Mostrar la diferencia | *pendiente (8-oct): página `/medir` en el XR20* | PREVISTO |
| **Precisión del nivel** (5 marcas × 10 lecturas) | Error < 5 puntos | *pendiente (8-oct): `tools/medir_precision.py`* | PREVISTO |
| Costo por punto | Por cruce y por año | US$1.135–2.195 instalado y US$305–860 al año | OBTENIDO (estimación con fuentes) |

**Cómo repetir las mediciones** (desde `tools/`):

```bash
../edge/.venv/bin/python medir_latencia.py --borde http://IP-DEL-BORDE:8000 -n 200
../edge/.venv/bin/python medir_latencia.py -n 1 --guia xr20 --ciclos 50
../edge/.venv/bin/python medir_precision.py --marcas 35 45 55 65 75
```

**Video de la prueba (7-oct, 11:42, laboratorio del Testbed):** 85 s; el cartón sobre el sensor real y el tablero pasando entre CUIDADO y CERRADO. Archivo: `entregables/PasoSeguro-prueba-prototipo-7oct-1080p.mp4`.

**Validación externa:** el 7-oct le mostramos la demo al jefe de la Promotora, y él la publicó en YouTube («Uso de sensor para alerta de inundación», https://youtu.be/Aw2mkXoyZ-E). Su frase: «estamos hablando de un desarrollo que podría salvar vidas».

---

## 7. Por qué 5G (y lo que no necesita 5G)

| Necesidad | Por qué no alcanza la red pública | Qué aporta el 5G |
|---|---|---|
| **El aviso tiene que llegar en la tormenta** | La red pública se satura justo cuando más se necesita. Con la tormenta Sara, unos 50.000 clientes del ICE tuvieron el móvil o internet degradado. En Japón 2011 la voz llegó a 50–60 veces lo normal y se bloqueó hasta el 95 % de las llamadas | Red privada o porción reservada con **prioridad** (5QI y ARP de 3GPP); el modelo de FirstNet en EE. UU. y del nuevo Nødnett de Noruega |
| Decidir junto al río, sin depender de internet | Con 4G y nube, el aviso depende de internet | **Borde dentro de la red privada** |
| Muchos sensores río arriba para ganar minutos | — | **mMTC**: hasta 1.000.000 de dispositivos por km² (ITU-R M.2410) |
| Video del módulo cámara o del dron | Hace falta subida ancha y estable | **eMBB** |
| La alarma en el cruce | — | **No necesita 5G, a propósito:** funciona sin ninguna red |

**Lo que decimos con honestidad:**
- El dato del nivel son pocos bytes. Lo que pide 5G es la prioridad en la tormenta, la escala y el video.
- Si la torre se queda sin luz, se cae cualquier red. Por eso la alarma local y el panel solar.
- Donde no hay 5G (un valle sin señal), el sensor manda el dato por LoRa a un punto alto que tiene red.

---

## 8. Planes B

| Si falla… | Qué pasa | Plan B |
|---|---|---|
| El sensor (sin eco, sin corriente) | El borde queda en CUIDADO y no reabre | Flotador como segunda fuente; aviso de mantenimiento |
| La red 5G | La ESP32 pasa a modo local | **La alarma del cruce sigue** |
| Internet | El borde decide igual dentro de la red privada | La lluvia del IMN sale de la caché; Waze se muestra en el tablero |
| El MXIE del operador | — | Laptop-borde dentro de la red 5G (en uso) |
| La cámara 5G | — | No hace falta: el pitch es con el sensor |
| Team Comms (PTT) | — | La página `/guia` hace sirena, voz y vibración |
| La demo en vivo | — | Video de 60 s grabado (en la laptop y en USB) y la animación pública |
| No hay 5G en el vado real | — | 4G de otro operador, un nodo portátil de la CNE o LoRa hasta un cerro con señal |

---

## 9. Seguridad, privacidad y riesgos

| Tema | Hoy (prototipo) | En el piloto |
|---|---|---|
| Acceso a la API del borde | Solo dentro de la red privada; **sin clave por dispositivo** | Una clave por sensor y tráfico cifrado (TLS). Las rutas de demo, apagadas |
| Lecturas falsas | Una lectura que salta no reabre el cruce (reabre de a un escalón) | Dos fuentes y alerta si no coinciden |
| Privacidad | Solo mide el nivel del agua; no hay datos personales | Con cámara o LiDAR: guardar solo eventos («persona en el cruce, 14:32»), no imágenes |
| Responsabilidad | El sistema avisa el peligro; **no autoriza a cruzar** | El verde dirá «sin alerta»; la decisión de la vía es del Conavi o de la municipalidad; cada cambio queda registrado con su hora |
| Mantenimiento | — | 4 visitas al año incluidas. Si un sensor deja de mandar datos, el tablero lo marca |
| Hardware | Cables de prueba; convertidor de nivel sin soldar | Gabinete IP67, poste galvanizado y conexiones soldadas |

---

## 10. Costo por punto y modelo de negocio

**Punto base (sin cámara):**

| Concepto | US$ | Origen |
|---|---:|---|
| ESP32, ultrasónico, flotador, gabinete IP67 y sirena | 60 | CRCibernética (Costa Rica) |
| Panel solar, controlador y batería | 160–403 | LEDXPRES (Costa Rica), NOAA y Bioenno |
| Router 5G industrial (Teltonika RUTX50) | 516–830 | Distribuidores internacionales |
| Poste, herrajes y cableado | 150–400 | Tubo EPA (Costa Rica) más estimación |
| Instalación y traslado | 250–500 | Estimación con el salario mínimo del MTSS 2026 |
| **Total instalado** | **≈ 1.135–2.195** | ₡519.000–1.003.000 (₡457,03 por dólar) |
| **Operación por año** (datos, 4 visitas y repuestos) | **≈ 305–860** | kölbi y Liberty más estimación |

**Comparación:**

| | Costo |
|---|---|
| Santa Ana (CR): alquiler de estaciones de alerta | ₡7,5 millones por estación al año |
| Texas: medidor en un cruce bajo | US$20.000 |
| Texas: barrera automática | US$80.000 |
| Puente nuevo sobre el río Cóbano (Inder, 2026) | ₡363 millones, lo mismo que unos 360 puntos |

**Precio propuesto:** US$120 al mes por punto, todo incluido, con contrato de 5 años (nuestro costo ≈ US$80 al mes). Otra opción: US$2.200 de instalación más US$70 al mes.

**Quién paga:**

| Quién | Dónde | De qué plata |
|---|---|---|
| **Conavi** | Rutas nacionales, como la 623 del río Vainilla | La **Ley 10717 (2025)** da el 15 % del impuesto a los combustibles a «puentes y vados»: 8 % al Conavi, 6 % a las municipalidades y 1 % a Lanamme (≈ ₡94.500 millones al año) |
| Municipalidades | Caminos cantonales | Ley 10717, Ley 8114 y la partida de prevención que exige la Ley 8488 (art. 45) |
| CNE | Cuencas y emergencias | Préstamo del Banco Mundial de US$370 millones, que incluye alertas tempranas locales |
| Operadores turísticos | Senderos y cataratas | El Decreto 39703-S-TUR les exige un plan de emergencias y suspender la actividad si hay riesgo |

Vía de compra del Estado: la compra pública de innovación (Ley 9986).

---

## 11. Mercado, escala y casos

- **Costa Rica:**
  - Puntarenas es el cantón con más declaratorias de emergencia del país (16, entre 2005 y 2023).
  - En 2025 llegaron 2,94 millones de turistas. El 56,5 % hace actividades de aventura y el 32 % camina senderos.
- **Fases (metas nuestras):**
  - piloto de 1 punto (río Vainilla, 2027);
  - 10–20 puntos en Puntarenas y en senderos con muertes recientes;
  - 100 o más en el país, unos US$144.000 al año;
  - Centroamérica, con CONRED, COPECO y el CEPREDENAC.
- **Casos que funcionaron:**
  - **Japón:** tenía 21.000 ríos y medía 3.200. Hoy tiene 9.300 medidores de bajo costo, a un décimo del costo de uno tradicional, que transmiten solo cuando el río sube. En el tifón Hagibis, uno de ellos permitió cerrar un camino 15 minutos antes del desborde.
  - **Corea del Sur:** después de los 14 muertos del paso subterráneo de Osong, puso barreras automáticas en 512 de 564 pasos. Cierran con 5 cm de agua y el estado sale en el navegador.
  - **San Antonio (Texas):** más de 190 cruces mandan su estado a Waze desde 2023.
  - **OMM:** con alerta temprana, la mortalidad es 8 veces menor.
- **Siguientes módulos:**
  - cámara 5G con visión en el borde;
  - LiDAR o radar como segunda fuente de nivel;
  - LiDAR 3D para detectar personas sin identificarlas;
  - dron en base, disparado por el estado CUIDADO, como fase 2.

---

## 12. Hoja de ruta y petición

| Hito | Fecha | Criterio de éxito |
|---|---|---|
| ✅ Sensor real en la red del Testbed | 7-oct-2026 | Nivel real en el borde en 22–60 ms |
| Aviso al XR20 con la red cargada y comparación con 4G | oct-2026 | 50 avisos y 200 muestras de cada red |
| Medir la cobertura y calibrar en el río Vainilla | 2027 | Umbrales ajustados a la forma del vado |
| Piloto con el Conavi y la CNE | Lluvias de 2027 | Una temporada sin vehículos arrastrados |
| Feed publicado con un socio oficial de Waze | 2027 | Cierre visible en Waze |
| Réplica en Centroamérica | 2027–2028 | Un cruce en Honduras o Guatemala |

**Pedimos:**
1. acceso prioritario al Testbed para terminar la medición con la red cargada;
2. el contacto con el **Conavi** y la **CNE** para el piloto en el río Vainilla.

---

## 13. Fuentes principales

- **Repositorio:** `README.md`, `PLAN.md` (secciones 6 y 8), `ESTADO.md` y el código en `edge/` y `esp32/`.
- **Investigación con todas las fuentes y fechas:** `docs/INVESTIGACION-mercado-costos-casos.md` · https://claude.ai/artifact/UejvM95k9G4WHVkTu8fk71
- **La Nación:**
  - río Vainilla, 14-sep-2024: https://www.nacion.com/sucesos/desastres/dueno-de-carro-arrastrado-en-rio-de-lepanto-cuenta/LKUXZKLPFVEXPIGVG26SPPY7ME/story/
  - río Vainilla, 30-oct-2024: https://www.nacion.com/sucesos/accidentes/falta-de-puente-propicio-tragedia-de-odontologo/BK7KKUPPWRGQ7ODATIK3UUQSVE/story/
- **Ley 10717:** https://bufetedecostarica.com/adicion-articulo-5-bis-ley-8114-puentes-y-vados-en-costa-rica-10717/
- **Tormenta Sara y telecomunicaciones:** https://semanariouniversidad.com/?p=332316
- **MLIT (Japón), medidores de crisis:** https://www.mlit.go.jp/river/shishin_guideline/kasen/pdf/kikikanri_tebiki.pdf

---

## Anexo A · Respuestas en mano (imprimir)

**Cifras para decir sin mirar:**

| Tema | Detalle |
|---|---|
| Sensor → borde (Wi-Fi + 5G) | **p50 de 31 ms · p95 de 44 ms** (7-oct) |
| Borde → nube (internet) | p50 de 1.738 ms: el borde es unas **50 veces** más rápido |
| Pruebas automáticas | **165** |
| Alcance del sensor | 25 cm a **4,5 m** |
| Umbrales | CUIDADO 40 % · CERRADO 70 % · subida rápida 15 %/min |
| Costo de un punto | **US$1.135–2.195** · operación **US$305–860 al año** |
| Precio | **US$120 al mes** todo incluido (≈ ₡54.800) |
| Santa Ana paga | ₡7,5 millones por estación al año |
| Ley 10717 | **15 %** del impuesto a los combustibles para puentes y vados |
| Río Vainilla | ~500 personas · 2–3 carros atascados por semana · 1 arrastrado por mes |
| Tormenta Sara | ~50.000 clientes del ICE con el móvil degradado |
| Japón | 9.300 medidores baratos · cierre 15 min antes del desborde |
| Puente del río Cóbano | ₡363 millones = unos 360 puntos |

**Respuestas de una línea:**

1. **¿Por qué 5G?** Para el número no hace falta. Hace falta para la prioridad en la tormenta, para muchos sensores y para el video.
2. **¿Y si se cae la torre?** La sirena del cruce suena sin red y el punto tiene panel solar.
3. **¿Dónde está el 5G si la ESP32 va por Wi-Fi?** El tramo largo es el CPE por la red 5G del Testbed; en el poste va un router 5G.
4. **¿Y si dice verde y alguien se ahoga?** Avisa el peligro, no autoriza a cruzar. Sin datos, nunca vuelve a verde.
5. **¿Falsas alarmas?** Reabre de a un escalón; hay dos fuentes; la precisión medida es [completar].
6. **¿5G contra 4G?** [completar con la medición] o «es la prueba que falta; por eso pedimos el Testbed».
7. **¿Quién paga?** El Conavi o la municipalidad con la Ley 10717; la CNE; el operador turístico.
8. **¿Hay clientes?** Nada firmado: venimos a pedir el contacto con el Conavi y la CNE.
9. **¿Qué tiene de distinto del IMN o la CNE?** Está en el vado, decide ahí y avisa a quien va a cruzar. Cuesta 11 veces menos que lo de Santa Ana.
10. **¿Es un láser?** No, es ultrasónico: mide con sonido, de día y de noche.
11. **¿Hackeo?** Hoy, red privada sin acceso de afuera; en el piloto, una clave por sensor y cifrado.
12. **¿Cuántos vados hay?** No hay inventario; la Ley 10717 obliga a hacerlo. Empezamos con 1, luego 10–20 y después 100.

**Si no sabemos:** «No tengo ese dato exacto. Lo que sí medimos es ___. Se lo hacemos llegar hoy.»

Las 20 preguntas difíciles completas están en `docs/PREGUNTAS-DIFICILES-jurado.md`.
