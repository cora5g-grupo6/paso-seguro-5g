# Paso Seguro 5G · Base del pitch (viernes 9 de octubre)

Grupo 6 · CORA 5G · Hackatón Centroamericano de Innovación 5G · PCII Coronado.
Armado el jueves 8 con la guía de trabajo de Oscar Chacón («Cómo defender su proyecto ante el jurado»), el código y ESTADO.md del repo, PLAN.md, las presentaciones oficiales del lunes 5 y las transcripciones del 5 y 6 de octubre.

**Formato:** 15 minutos por equipo, 10 de exposición (meta 9:00–9:30, entre 1.150 y 1.350 palabras) y el resto preguntas. Sesiones desde las 9:30 a. m., cuatro grupos por sesión. Rúbrica: innovación, pertinencia, viabilidad técnica y escalabilidad, 25 % cada una, nota de 1 a 5.

**Regla de oro de la guía:** lo que no tiene fuente o medición se dice como pregunta abierta. En este documento cada cifra dice si está **OBTENIDA** o **PREVISTA**.

---

## 1. Ficha

| Campo | Respuesta |
|---|---|
| Proyecto | Paso Seguro 5G |
| Equipo | Grupo 6 · CORA 5G |
| Vertical | Turismo, movilidad y riesgo (3 de los 7 sectores del mentor) |
| Capacidad 5G principal | **Comunicación de misión crítica** (URLLC: confiable y de baja latencia) en una red privada con borde; mMTC para muchos sensores a lo largo del río |
| Tipo de propuesta | Técnica con implementación (demostrar el flujo completo) |
| Exposición | 10 min (meta 9:00–9:30) |
| Preguntas | ~5 min |
| Modalidad | Presencial, PCII Coronado |
| Defensa | Viernes 9-oct, desde las 9:30 a. m. (confirmar turno) |

**Roles (completar con nombres antes del primer ensayo):**

| Rol | Sección | Preguntas que responde |
|---|---|---|
| Presentador principal | Gancho, problema, cierre | Visión e impacto |
| Responsable técnico | Solución, arquitectura, demo | Red, latencia, IA, seguridad |
| Responsable de negocio | Impacto, quién paga, próximos pasos | Costos, mercado, escala |
| Tiempo y soporte | Reloj y demo de respaldo | Pasa al video en menos de 10 s |

---

## 2. Gran Idea y SCQA

**Gran Idea (25 palabras):**
> Un sensor en el río avisa al guía, al turista y a Waze que el cruce está cerrado antes de que alguien entre, por una red 5G que no puede fallar.

| | Frase |
|---|---|
| **S — Situación** | En Costa Rica miles de turistas y vecinos cruzan ríos sin puente, en vados y senderos rurales. |
| **C — Complicación** | Una cabeza de agua sube en minutos: en las últimas seis semanas mató a un guía en el río Barú y a una turista en Rincón de la Vieja. |
| **Q — Pregunta** | ¿Cómo se entera alguien de que el río creció antes de meterse? |
| **A — Respuesta** | Paso Seguro mide el río con sensores, decide en el borde y avisa en menos de un segundo al guía, al turista y al mapa, por una red de misión crítica. |

**Tres argumentos:**
1. **Es real y es ahora:** casos con fuente en 2024, 2025 y 2026, y el mismo problema en Honduras y Guatemala.
2. **Ya funciona:** el sensor real manda el nivel por la red y el sistema decide y avisa; 165 pruebas automáticas.
3. **No hay que instalar nada:** el guía abre una página, el conductor ya usa Waze y el turista escanea un QR.

---

## 3. El problema

**En una frase, sin jerga:**
> Cuando un río crece de golpe, quien está por cruzarlo no se entera hasta que el agua ya lo tiene encima.

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Quién sufre? | Guías y grupos de turismo en ríos y cataratas; conductores y vecinos que cruzan vados sin puente; ambulancias | Casos abajo |
| ¿Cuántos? | Vado del río Vainilla (Ruta 623, Lepanto): unas 500 personas dependen de esa ruta. Cifra nacional de cruces: **pregunta abierta** | La Nación, 14-sep-2024 |
| ¿Cuánto cuesta? | Vidas: 140 muertes por accidentes acuáticos en 2024, ríos y mar juntos, la más alta desde 2020 | Cruz Roja vía El Observador |
| ¿Con qué frecuencia? | En el Vainilla: 2 o 3 carros atascados por semana y uno arrastrado por mes; ambulancias con 2 h de desvío | La Nación, 2024 |
| ¿Cómo lo resuelven hoy? | Mirar el río a ojo, preguntar a vecinos, rótulos fijos; nadie ve la crecida que viene de río arriba | Observación y casos |
| ¿Por qué ahora? | Barú (30-ago-2026), Rincón de la Vieja (12-sep-2026), Guápiles (4-may-2026); Honduras (25-sep-2026) y Guatemala (16-ago-2026) | Teletica, El Observador, CRHoy, La Tribuna, Infobae |
| ¿Validado con usuarios? | **Pendiente:** prueba con una persona que haga de guía con el XR20 (lo pidió el mentor) | — |

**Respuesta a «¿Qué evidencia tienen de que esto debería existir?»** (la pregunta del mentor de la U Latina):
> En las últimas seis semanas, dos cabezas de agua mataron a un guía de turismo en el río Barú y a una turista en Rincón de la Vieja, y en el vado del río Vainilla la comunidad cuenta un carro arrastrado por mes.

---

## 4. La solución y por qué 5G

**En una frase:** un sensor mide el nivel del río; el servidor de borde decide si el cruce está LIBRE, en CUIDADO o CERRADO (y detecta cuando el agua sube rápido), y avisa al guía, al turista en su idioma y al mapa, aunque no haya internet.

**La cámara es un módulo adicional** (siguiente fase): suma ver el río y a la persona que se acerca. El pitch y la demo van con el sensor.

**Insight:** el peligro no es el río alto, es el río que sube mientras nadie lo mira. La crecida llega de río arriba, y justo en una tormenta o emergencia la red pública se satura o se cae. Un aviso del que depende una vida no puede competir con el resto del tráfico.

**Por qué 5G y no 4G: es misión crítica, ahí se puede perder una vida.** La inducción del Testbed tiene una lámina entera («Sí, pero todo eso se puede hacer sin 5G…»), así que la van a hacer.

| Requisito | Valor | ¿4G pública o Wi-Fi? | Capacidad 5G |
|---|---|---|---|
| El aviso tiene que llegar siempre | Entrega confiable, con prioridad sobre el resto del tráfico | En una tormenta o emergencia la 4G pública se satura (todos llaman a la vez) y el aviso compite con todo; el Wi-Fi no llega al río | **URLLC** (misión crítica: confiable y de baja latencia) en una **red privada** con espectro propio |
| Decidir junto al río, sin depender de nadie | Decisión en milisegundos aunque se caiga internet | 4G con nube depende de internet y del operador | **Computación en el borde** dentro de la red privada |
| Avisar antes: sensores río arriba | Muchos sensores a lo largo del río, minutos de ventaja | 4G no escala igual a miles de sensores por zona | **mMTC** (hasta un millón de dispositivos por km²) |
| Red de emergencia propia | La CNE o los bomberos levantan su nodo y todos se conectan | Depende de la red pública | Red privada 5G portátil (ejemplo del Grupo CCC) |
| La alarma local en el cruce | Funcionar aunque todo se caiga | — | **No necesita 5G, a propósito** |

**Frase para decir:** «Cuando la vida de alguien depende de un aviso, el aviso no puede competir con las fotos de todo el mundo. En una tormenta la red pública se satura. Una red privada 5G le da prioridad al aviso, decide junto al río y sigue funcionando sin internet. Por eso es 5G y no 4G: es misión crítica.»

**Lo que dijo el Grupo CCC (Nokia), martes 6:** «Cuando la vida humana está por medio, la tecnología no puede fallar»; en un estadio o un evento la radiobase pública se satura; la red privada tiene hardware y frecuencia dedicados.

**Slicing: no prometerlo.** En el laboratorio hay un solo slice con prioridad por tipo de tráfico. Decir: «prioridad del aviso en la red privada; slicing con el operador cuando se escale».

**Comparación con alternativas:**

| Criterio | Paso Seguro | Mirar el río a ojo | Rótulo fijo o sensor que pita |
|---|---|---|---|
| Costo para el usuario | Nada: página web, Waze, QR | Nada | Bajo |
| Desempeño | Avisa antes de llegar, aunque la red pública esté saturada | Ve solo lo que tiene enfrente | Avisa solo a quien está ahí |
| Adopción | Nadie instala nada | Ya se hace | Fácil |
| Lo distinto | Detecta la subida rápida y lo avisa a distancia, en el mapa y con prioridad | — | — |

---

## 5. Arquitectura, método y riesgos

**Arquitectura en una línea:** ESP32 con sensor ultrasónico y flotador → red privada 5G del Testbed → servidor de borde (reglas de decisión) → guía (XR20), turista (QR), tablero y Waze/Google. *(Módulo adicional: cámara 5G.)*

| # | Etapa | Qué se hace | Componente | Cómo se valida |
|---|---|---|---|---|
| 1 | Mide | El ultrasónico mide la distancia al agua cada segundo; el flotador confirma el nivel alto | ESP32 + ultrasónico impermeable + flotador | Cartón y tubo con marcas conocidas |
| 2 | Transmite | El nivel viaja por la red privada con prioridad | NDAC n78, CPE FastMile | Latencia medida en vivo en el tablero |
| 3 | Decide | Decide LIBRE, CUIDADO o CERRADO, detecta la subida rápida y reabre de a un escalón | Servidor de borde (FastAPI) | 157 pruebas automáticas |
| 4 | Avisa | Guía con sirena, voz y vibración; turista ES/EN; mapa; feed de Waze; alarma local | Páginas web, ESP32, feed CIFS | Feed validado contra el esquema oficial de Waze |

**Indicadores (KPI):**

| KPI | Meta | Resultado | Estado |
|---|---|---|---|
| Sensor real → borde (por la red, Wi-Fi FastMile + 5G) | < 100 ms | **p50 de 31 ms, p95 de 44 ms** (tablero, 7-oct, 11:42); en la prueba con cartón, 22–60 ms | OBTENIDO |
| Borde → nube (pedido HTTPS a internet) | Comparar | p50 de 1.738 ms, unas 50 veces más que decidir en el borde (7-oct) | OBTENIDO |
| Acción → alerta en pantalla | < 1 s | **4,3 ms p50** (laptop) | OBTENIDO en laptop |
| Pruebas automáticas | — | **165** en verde (8-oct) | OBTENIDO |
| Salida a internet por la red 5G | Funciona | OK (prueba de conectividad) | OBTENIDO |
| Teléfono del guía (XR20) ↔ borde por 5G | < 50 ms | — | PREVISTO: medir hoy |
| 5G con borde vs 4G con nube | Mostrar la diferencia | — | PREVISTO: 200 muestras de cada uno |
| Precisión de la lectura del nivel | Error < 5 puntos | — | PREVISTO: 5 marcas × 10 lecturas |
| Costo por punto | Por cruce y por año | **US$1.135–2.195 instalado y US$305–860 al año** (precios de Costa Rica; ver docs/INVESTIGACION-mercado-costos-casos.md) | OBTENIDO (estimación con fuentes) |

**Riesgos y mitigación:**

| Riesgo | Tipo | Prob. | Mitigación |
|---|---|---|---|
| No hay cobertura 5G en el cruce real | Técnico | Alta | Red privada portátil o 5G regional (operador regional, CNE); la alarma local funciona sin red |
| Falsas alarmas: la gente deja de creer | Técnico | Media | Dos fuentes (ultrasónico + flotador) y reapertura de a un escalón |
| Basura o ramas frente al sensor | Técnico | Media | El flotador confirma; el borde avisa si la lectura salta sin sentido |
| Nadie paga la operación | Financiero | Media | Pago por cruce y por año (propuesta: US$120 al mes por punto, todo incluido). La Ley 10717 (2025) da el 15 % del impuesto a los combustibles a «puentes y vados»: Conavi 8 %, municipalidades 6 %. En senderos, el operador turístico; Compra Pública Innovadora |
| Se va la luz y se cae la antena | Técnico | Media | Panel solar y batería propios en cada punto; la alarma local suena sin red. En Noruega, más de 9 de cada 10 antenas caídas en tormenta son por falta de luz |
| Publicar en Waze requiere socio oficial | Regulatorio | Alta | El feed ya está en el formato oficial; lo publica el MOPT o la municipalidad, socios de Waze |
| Privacidad | Ético | Baja | Solo mide el nivel del agua; con la cámara (módulo adicional) no se identifica a nadie y los clips quedan en el borde |

---

## 6. Resultados y demo

**Validación externa (miércoles 7):** le mostramos la demo con el cartón al jefe de la Promotora, y él la publicó el mismo día en YouTube ([«Uso de sensor para alerta de inundación»](https://youtu.be/Aw2mkXoyZ-E), 2:16). Su frase al final: «estamos hablando de un desarrollo que podría salvar vidas». La placa es «Agricultura IoT», de **Ricardo Jiménez Guido**: darle el crédito.

**Titulares de resultados (frase completa):**
- «El sensor real ya manda el nivel por la red y el sistema decide en 22 a 60 milisegundos.»
- «Si se corta internet, el aviso local sigue igual.»
- «El aviso sale en el formato oficial de Waze y pasa su validación.»

**Plan de la demo (60–90 s):**

| Elemento | Respuesta |
|---|---|
| Qué muestra | Sube el agua → el tablero pasa a CUIDADO y a CERRADO → suena la alarma, el guía recibe la alerta y el mapa se pone rojo |
| Plan A | En vivo: tubo o cartón frente al ultrasónico + tablero + página del guía en el XR20 |
| Plan B | **Video grabado de 60 s** (sensor real → tablero → guía → lista de eventos → cortar internet), en la laptop y en USB, sin internet |
| Plan C | La animación pública: https://claude.ai/artifact/1Ar5y331s8UtbxXoHehog1 |
| Quién la opera | El responsable técnico; los demás no tocan nada |
| Regla | Si algo falla, se pasa al video en menos de 10 s, sin disculpas largas |

**Guion de la demo (lo que se dice mientras se ve):**
1. «Este es el tablero del cruce. Está en verde y aquí se ve la latencia en vivo.»
2. «Ahora sube el agua.» → CUIDADO: «avisa antes del umbral, porque sube rápido».
3. → CERRADO: «suena la alarma en el cruce, el guía recibe la alerta con sirena y voz, el turista la lee en su idioma y el mapa se pone rojo».
4. «Y cada cambio queda registrado con su hora», mostrar la lista de eventos del tablero. (Grafana no está instalado en la laptop; usarlo solo si la PCII da el suyo.)

---

## 7. Impacto y quién paga

| Nivel | A quién | Cifra | Cómo se mide |
|---|---|---|---|
| Inmediato (piloto) | Vado del río Vainilla, Lepanto (Ruta Nacional 623, del Conavi) | ~500 personas que viven cerca (La Nación, 14-sep-2024); meta: cero vehículos arrastrados en una temporada de lluvias | Registro de cierres y alertas atendidas |
| A escala | Vados y senderos turísticos de Costa Rica | **Pregunta abierta:** inventario de vados con la CNE y el MOPT | Inventario + piloto |
| Sistémico | Turismo rural y respuesta a emergencias | Menos rescates; turismo de naturaleza más seguro (el 64,6 % de los turistas de 2025 vino de EE. UU. y Canadá) | Datos de Cruz Roja y CNE |

**Quién paga:** un costo por cruce y por año. Propuesta: **US$120 al mes por punto, todo incluido** (nuestro costo ≈ US$80). Santa Ana ya paga ₡7,5 millones por estación de alerta al año.
- En rutas nacionales, como la 623 del río Vainilla: el **Conavi**. La **Ley 10717 (2025)** da el 15 % del impuesto a los combustibles a «puentes y vados»: 8 % al Conavi, 6 % a las municipalidades y 1 % a Lanamme (≈ ₡94.500 millones al año).
- En caminos cantonales: la municipalidad (Ley 10717, Ley 8114 y la partida de prevención de la Ley 8488).
- En senderos y cataratas: el operador turístico (el Decreto 39703 le exige un plan de emergencias y suspender si hay riesgo).
- En emergencias: la CNE (préstamo del Banco Mundial de US$370 millones que incluye alertas tempranas locales).
- Camino de compra: Compra Pública Innovadora de la Promotora.

**Mercado de abajo hacia arriba:** no hay inventario nacional de vados (la Ley 10717 obliga a hacerlo). Piloto de 1 punto → 10–20 puntos en Puntarenas y senderos con muertes recientes → 100 o más en el país (≈ US$144.000 al año, el 0,07 % de la plata de la Ley 10717). No decir «el 1 % de un mercado gigante». Detalle y fuentes: docs/INVESTIGACION-mercado-costos-casos.md.

**Ética:** solo mide el nivel del agua, los datos quedan en el borde, y la alarma local avisa también a quien no tiene teléfono.

**Alineación:** turismo seguro y conectividad rural; ODS 3 (salud y vidas), 9 (infraestructura e innovación) y 11 (comunidades resilientes).

---

## 8. Equipo, próximos pasos y petición

| Integrante | Credencial (completar en el ensayo) |
|---|---|
| [ ] | [ ] |

**Próximos pasos:**

| Hito | Fecha | Criterio de éxito |
|---|---|---|
| ✅ Sensor real en la red del Testbed | 7-oct-2026 | Nivel real en el borde en 22–60 ms |
| XR20 medido; 5G vs 4G con la red cargada | Oct 2026 | Latencia y entrega del aviso con 200 muestras de cada una |
| Módulo adicional: cámara 5G | 2027 | Ver el río y a la persona que se acerca |
| Piloto en el vado del río Vainilla | Temporada de lluvias 2027 | Una temporada sin vehículos arrastrados |
| Feed publicado con un socio oficial de Waze | 2027 | Cierre visible en Waze en tiempo real |
| Réplica en Centroamérica | 2027–2028 | Un cruce en Honduras o Guatemala con la agencia de emergencias |

**Petición concreta al jurado:**
> Ya probamos el flujo con el sensor real en la red del Testbed. Pedimos dos cosas: acceso prioritario al Testbed para medir la entrega del aviso con la red cargada, y el contacto con la CNE y el Conavi, que administra la Ruta Nacional 623, para instalar el primer punto en el vado del río Vainilla en la temporada de lluvias de 2027.

**Cierre memorable:**
> Hoy el conductor de Lepanto se entera de que el río creció cuando el agua ya le llega a la puerta. Con Paso Seguro, lo sabe antes de llegar.

---

## 9. Guion minuto a minuto (≈1.250 palabras)

| Tramo | Sección | Diapositiva del deck | Quién |
|---|---|---|---|
| 0:00–0:30 | Gancho | Portada | Presentador |
| 0:30–1:45 | Problema y evidencia | El problema · Por qué pasa | Presentador |
| 1:45–3:15 | Solución y por qué 5G | Mira, decide, avisa · Por qué 5G | Técnico |
| 3:15–4:45 | Arquitectura y riesgos | Cómo funciona · Lo que usamos del Testbed | Técnico |
| 4:45–6:30 | Resultados y demo (sensor + tablero, o video) | Demo · Resultados | Técnico |
| 6:30–7:45 | Impacto y quién paga | Para todos · Quién paga | Negocio |
| 7:45–8:45 | Próximos pasos y petición | El plan | Negocio |
| 8:45–9:15 | Cierre | Cierre | Presentador |
| 9:15–10:00 | Margen | — | — |

**Puntos de control:** 3:15 terminando la solución; 6:30 terminando los resultados; 8:45 en la petición. Si van 20 s tarde, saltar a la petición y decir: «Para respetar el tiempo, lo resumo en tres frases».

**0:00 — Gancho (memorizar)**
«El 30 de agosto, en el río Barú, un guía llevaba a más de 25 personas. En minutos, una cabeza de agua bajó por el río. Rescataron a más de veinte. El guía no salió. Doce días después pasó lo mismo en Rincón de la Vieja, con una turista. Somos el Grupo 6 y les presentamos Paso Seguro 5G.»

**0:30 — Problema**
«En Costa Rica miles de turistas y vecinos cruzan ríos sin puente. En el vado del río Vainilla, en Lepanto, la comunidad cuenta dos o tres carros atascados por semana y uno arrastrado cada mes. En septiembre de 2024 el río se llevó una camioneta 500 metros con el conductor adentro. Las ambulancias dan una vuelta de dos horas cuando el río crece. La Cruz Roja contó 140 muertes en el agua en 2024, la cifra más alta desde 2020. Y no es solo Costa Rica: en septiembre, en Honduras, y en agosto, en Guatemala, el río se llevó un carro y un bus con veinte pasajeros. El problema no es el río alto. Es el río que sube mientras nadie lo está mirando, porque la crecida viene de río arriba. Entonces, ¿cómo se entera alguien de que el río creció antes de meterse?»

**1:45 — Solución y por qué 5G**
«Paso Seguro hace tres cosas: mide, decide y avisa. Un sensor mide el nivel del río cada segundo y un flotador lo confirma. En el servidor de borde, junto al río, el sistema decide si el cruce está libre, en cuidado o cerrado, y se da cuenta cuando el agua sube rápido, antes de llegar al límite. Y avisa: el guía recibe una alerta con sirena y voz; el turista lee el aviso en su idioma con un código QR; y el mapa marca el cruce cerrado, en el formato oficial de Waze. Nadie instala nada. ¿Por qué 5G y no 4G? Porque es misión crítica: aquí se puede perder una vida. Cuando la vida de alguien depende de un aviso, el aviso no puede competir con las fotos de todo el mundo. En una tormenta o una emergencia, la red pública se satura justo cuando más se necesita. Una red privada 5G le da prioridad al aviso, lo decide junto al río y sigue funcionando aunque se caiga internet. Y permite poner muchos sensores río arriba, para avisar con minutos de ventaja.»

**3:15 — Arquitectura y riesgos**
«Así funciona con los equipos del Testbed: el sensor entra a la red privada 5G; el servidor de borde decide; y la alerta sale al teléfono del guía, a la página del turista, al tablero y al mapa. Todo dentro de la red privada: si se cae internet, el aviso local sigue funcionando. Y la alarma del cruce no necesita ninguna red: si todo falla, igual suena. Sabemos dónde puede fallar. Una rama o basura frente al sensor puede dar una lectura falsa; por eso el flotador confirma y el sistema reabre el cruce de a un escalón, nunca de golpe. No prometemos network slicing: en el laboratorio hay prioridad por tipo de tráfico; el slicing llega con el operador cuando se escale. Y la cámara 5G es el siguiente módulo: suma ver el río y a la persona que se acerca.»

**4:45 — Resultados y demo** (video de 60 s o en vivo)
«Esto no es una maqueta en papel. Desde el miércoles, el sensor real manda el nivel por la red del Testbed y el sistema decide en 22 a 60 milisegundos. Ese mismo día se lo mostramos al jefe de la Promotora, y su frase fue: "un desarrollo que podría salvar vidas". Véanlo. [Demo o video] El cruce está libre. Sube el agua: pasa a cuidado, antes del límite, porque sube rápido. Sigue subiendo: cerrado. Suena la alarma en el cruce, el guía recibe la alerta y el mapa se pone en rojo. Cortamos internet: el aviso local sigue igual. Y cada lectura queda registrada minuto a minuto. Tenemos 165 pruebas automáticas en verde y el aviso de Waze pasa la validación del formato oficial. Lo que todavía estamos midiendo: la entrega del aviso al teléfono del guía con la red cargada, frente a 4G.»

**6:30 — Impacto y quién paga**
«El primer punto es el vado del río Vainilla: unas 500 personas dependen de esa ruta. La meta es una temporada de lluvias sin un solo vehículo arrastrado. Quién paga: un costo por cruce y por año, unos 120 dólares al mes. En caminos, el Conavi o la municipalidad: desde 2025 la ley les da el 15 % del impuesto a los combustibles para puentes y vados. En senderos y cataratas, el operador turístico, porque un tour seguro vende más. Y el camino para que el Estado lo compre ya existe: la Compra Pública Innovadora de la Promotora. El sistema no recoge datos personales: solo mide el nivel del agua, y los datos se quedan en el borde.»

**7:45 — Próximos pasos y petición**
«Ya probamos el flujo con el sensor real en la red del Testbed. Lo siguiente es medir la entrega del aviso con la red cargada, frente a 4G, y salir del laboratorio. Pedimos dos cosas: acceso prioritario al Testbed para terminar esa medición, y el contacto con la CNE y el Conavi para instalar el primer punto en el río Vainilla en la temporada de lluvias de 2027. Y como funciona con estándares abiertos, lo podemos replicar en Honduras y Guatemala con sus agencias de emergencia.»

**8:45 — Cierre (memorizar)**
«Hoy el conductor de Lepanto se entera de que el río creció cuando el agua ya le llega a la puerta. Con Paso Seguro, lo sabe antes de llegar. Que nadie cruce un río sin saberlo. Gracias.»

**Frases puente:**
- Problema → solución: «Entonces, ¿cómo se entera alguien antes de meterse?»
- Solución → método: «Así funciona con los equipos del Testbed.»
- Método → resultados: «Esto no es una maqueta en papel.»
- Resultados → impacto: «¿Y dónde empieza?»
- Impacto → petición: «Ya lo probamos en el laboratorio; ahora hay que sacarlo al río.»

---

## 10. Banco de preguntas (respuesta en 30–45 s)

Las 20 más difíciles, con la respuesta para decir en voz alta y los puntos débiles: **[PREGUNTAS-DIFICILES-jurado.md](PREGUNTAS-DIFICILES-jurado.md)**.

| # | Pregunta | Tipo | Respuesta en una frase | Prueba |
|---|---|---|---|---|
| 1 | ¿Por qué 5G y no 4G o Wi-Fi? | Temida | Es misión crítica: en una tormenta la 4G pública se satura y el aviso compite con todo; la red privada 5G le da prioridad, decide en el borde y funciona sin internet. La alarma local no necesita 5G, a propósito | Tabla de la sección 4 · Grupo CCC |
| 2 | ¿Qué latencia midieron y dónde? | Difícil | Sensor real → decisión 22–60 ms por la red del Testbed; la entrega al teléfono del guía con la red cargada la estamos midiendo | Tablero y logs |
| 3 | ¿Lo compararon con 4G? | Difícil | Si está medido, dar las dos cifras; si no: «es la prueba que falta, con 200 muestras de cada una» | `medir_latencia.py` |
| 4 | ¿Qué pasa si no hay 5G en el cruce real? | Temida | Red privada portátil o 5G regional, y la alarma local funciona sin red | Operador regional, CNE |
| 5 | ¿Y el network slicing? | Difícil | No lo prometemos: hoy prioridad por tipo de tráfico en la red privada; slicing con el operador al escalar | Grupo CCC, 6-oct |
| 6 | ¿Dónde está la inteligencia? | Fácil | En el borde: detecta la subida rápida (alerta temprana), cruza dos fuentes y reabre de a un escalón; la visión con cámara es el siguiente módulo | Código y pruebas |
| 7 | ¿Y de noche o con lluvia? | Fácil | El sensor ultrasónico mide igual de día y de noche | Diseño |
| 8 | ¿Falsas alarmas? | Difícil | Dos fuentes y reapertura de a un escalón; la precisión la medimos con 5 marcas × 10 lecturas | Plan de medición |
| 9 | ¿Quién paga y cuánto? | Temida | US$1.135–2.195 por punto instalado y US$305–860 al año; propuesta de US$120 al mes todo incluido. Paga el Conavi o la municipalidad con la Ley 10717 (15 % del impuesto a los combustibles para puentes y vados), la CNE o el operador turístico. Santa Ana ya paga ₡7,5 millones por estación al año | docs/INVESTIGACION-mercado-costos-casos.md |
| 10 | ¿Quién lo opera y mantiene? | Fácil | La municipalidad o el MOPT en caminos, la CNE en emergencias, el operador en senderos | Plan sección 9 |
| 11 | ¿Cómo llega a Waze? | Fácil | El aviso sale en el formato oficial (CIFS) y lo publica un socio oficial, como el MOPT | Feed validado |
| 12 | ¿Cómo escala del Testbed a una red comercial? | Difícil | Todo cumple 3GPP: lo que funciona en la red privada funciona en una pública | Grupo CCC |
| 13 | ¿Quién más lo hace? | Temida | Afuera, por partes: Japón tiene 9.300 medidores baratos, Corea cierra 512 pasos solos con 5 cm de agua y San Antonio (Texas) manda 190 cruces a Waze. En Costa Rica hay estaciones del IMN y SAT por cuenca, pero nadie une sensor, decisión en el borde y aviso al guía, al turista y a Waze en vados | Investigación, sección 9 |
| 14 | ¿Privacidad? | Fácil | Solo mide el nivel del agua; los datos quedan en el borde | Diseño |
| 15 | ¿Qué pasa si se va la luz? | Difícil | Cada punto lleva panel solar y batería (están en el costo) y la alarma local suena sin red. En Noruega, más de 9 de cada 10 antenas caídas en tormenta son por falta de luz | Autonomía en horas: pregunta abierta |
| 16 | ¿Lo probaron con usuarios? | Difícil | Decir con honestidad lo hecho; si no: «es el próximo paso, con un guía real» | Prueba del mentor |
| 17 | ¿Cuántos cruces hay en el país? | Difícil | «No existe un inventario nacional: la Ley 10717 obliga a armarlo con Lanamme. Hay 30.534 km de caminos cantonales en lastre o tierra» | Anuario MOPT 2023 |
| 23 | ¿El sensor es un láser? (en el video de la Promotora se dijo «infrarrojo») | Difícil | No: es **ultrasónico**. Mide con sonido, de día y de noche, y la lluvia y la neblina no lo ciegan como a un láser. Zona ciega de 25 cm y alcance de 4,5 m. La placa es de Ricardo Jiménez Guido | Ficha del sensor (CRCibernética) |
| 24 | ¿Y un dron? | Fácil | Es una fase 2. La señal de CUIDADO de Paso Seguro puede lanzar un dron en base (por ejemplo, DJI Dock 3, unos US$25–30 mil) para confirmar con video y térmica. El dron complementa y no reemplaza: no vuela con lluvia fuerte (más de 2 mm/h) y el sensor sí mide. El Conavi ya es operador autorizado de drones por la DGAC | Investigación, sección 9.7 |
| 22 | ¿Esto funcionó en algún lado? | Difícil | Japón: un medidor barato permitió cerrar un camino 15 minutos antes del desborde en el tifón Hagibis. Corea: tras 14 muertos en Osong, barreras automáticas en 512 pasos. Bangladesh: de 138.000 muertos en 1991 a 0 en 2023 con alerta temprana | Investigación, sección 9 |
| 18 | ¿Qué le falta al equipo? | Temida | Experiencia en ventas al Estado; la cubrimos con la Compra Pública Innovadora y mentoría | — |
| 19 | ¿Qué harían en 6 meses? | Fácil | Entrega del aviso medida con red cargada, inventario de vados, piloto listo para lluvias 2027 y módulo de cámara | Próximos pasos |
| 21 | ¿Y la cámara? | Fácil | Es el módulo siguiente: suma ver el río y a quien se acerca; el sistema ya está preparado para recibirla | Plan |
| 20 | ¿Por qué Centroamérica? | Fácil | Mismo problema en Honduras y Guatemala; estándares abiertos; CEPREDENAC y agencias de emergencia | Casos |

**Si no saben la respuesta:** «No tengo ese dato exacto; lo que sí sabemos es ___. Se lo hacemos llegar hoy mismo.» Nunca inventar.

---

## 11. Lista para hoy jueves

La lista completa, en orden, con responsables, la lista de tomas del video y el checklist de mañana, está en **[PENDIENTES-pitch-viernes-9.md](PENDIENTES-pitch-viernes-9.md)**. En resumen:

- [ ] Confirmar con la PCII la hora y el formato de la entrega de hoy.
- [ ] Devolver la corriente al sensor y prender el borde.
- [ ] Medir la precisión (5 × 10), el aviso al XR20 por 5G con la red cargada y 5G contra 4G.
- [ ] Prueba con un usuario.
- [ ] Flotador conectado, o la frase del guion cambiada.
- [ ] Grabar el video de 60 s (sin Grafana: lista de eventos).
- [ ] Actualizar la presentación: cifras, 165 pruebas, costo por punto, Ley 10717, Conavi y casos.
- [ ] Documento técnico para el jurado.
- [ ] Nombres en los roles y 3 ensayos con cronómetro.
- [x] Costo por punto y modelo de negocio: docs/INVESTIGACION-mercado-costos-casos.md.

## Fuentes

- Guía de trabajo y presentación «Cómo defender su proyecto ante el jurado», Oscar Chacón Alvarez (materiales del hackatón).
- Inducción del Testbed 5G y presentación de la Promotora, 5-oct-2026.
- Transcripciones: reglas (Carlos, CeNAT, 5-oct), Testbed (Víctor, 5-oct), operador regional (5-oct), U Latina y Grupo CCC (6-oct). Las tiene el equipo (no están en este repositorio).
- Casos y cifras con enlace: PLAN.md, sección 8. Lepanto: [La Nación](https://www.nacion.com/sucesos/desastres/dueno-de-carro-arrastrado-en-rio-de-lepanto-cuenta/LKUXZKLPFVEXPIGVG26SPPY7ME/story/) · Barú: [Teletica](https://www.teletica.com/sucesos/encuentran-sin-vida-a-guia-que-fue-arrastrado-por-cabeza-de-agua_416369) · Rincón de la Vieja: [CRHoy](https://crhoy.com/nacionales/estadounidense-es-la-victima-mortal-de-cabeza-de-agua-en-guanacaste/) · Cruz Roja 2024: [El Observador](https://observador.cr/2024-rompe-record-de-muertes-por-accidentes-acuaticos-en-los-ultimos-cuatro-anos-segun-cruz-roja/) · Honduras: [La Tribuna](https://www.latribuna.hn/2026/09/25/vehiculo-es-arrastrado-por-crecida-del-rio-cuyamapa-en-yoro-video/) · Guatemala: [Infobae](https://www.infobae.com/guatemala/2026/08/16/momentos-de-terror-en-guatemala-luego-que-un-bus-fuera-arrastrado-por-una-correntada-con-20-pasajeros-a-bordo/)
- Mediciones: ESTADO.md (7-oct) y PLAN.md, sección 6.
