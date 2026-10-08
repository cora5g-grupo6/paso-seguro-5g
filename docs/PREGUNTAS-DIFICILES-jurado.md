# Paso Seguro 5G · Preguntas difíciles del jurado y puntos débiles

Para el pitch del viernes 9 de octubre. Complementa el banco de preguntas de [PITCH-viernes-9.md](PITCH-viernes-9.md), sección 10.

**Cómo responder (30–45 s):**
1. Una frase directa que responda la pregunta.
2. Un dato con fuente.
3. El próximo paso.

Si no está medido, decir «es una pregunta abierta» y nunca inventar. Al jurado no se le discute: se le agradece la pregunta y se responde.

**Quién responde:** T = responsable técnico · N = responsable de negocio · P = presentador.

---

## A. Las 20 preguntas más difíciles y más probables

Están ordenadas por probabilidad y por cuánto daño hacen si se responden mal.

### 1. «Un sensor manda pocos bytes. ¿Para qué 5G? Con 4G, NB-IoT o LoRa alcanza.» (T)
- **Por qué la hacen:** es la más probable. La inducción del Testbed tiene una lámina entera que dice «Sí, pero todo eso se puede hacer sin 5G…».
- **Respuesta:** «Tiene razón: para mandar el nivel no hace falta 5G. Lo necesitamos por tres cosas.
  - **Prioridad:** en una tormenta la red pública se satura. Con la tormenta Sara, unos 50.000 clientes del ICE tuvieron el móvil degradado, y una red 5G privada, o una porción reservada, le da prioridad al aviso.
  - **Muchos sensores** a lo largo del río, en la misma celda.
  - **Subir video** cuando se sume la cámara o el dron.

  Y donde no hay 5G, el sensor manda el dato por LoRa a un punto alto que sí tiene red.»
- **Dato:** Semanario Universidad, 19-nov-2024. Japón 2011: la voz llegó a 50–60 veces lo normal y se bloqueó hasta el 95 % de las llamadas (MIC).
- **No decir:** «el 4G no sirve» ni «latencia de 1 ms» (URLLC no está probado aquí).

### 2. «Su ESP32 se conecta por Wi-Fi. ¿Dónde está el 5G en lo que midieron?» (T)
- **Respuesta:** «El tramo largo es 5G: el CPE FastMile del Testbed sale por la red privada 5G hasta el borde. La ESP32 no trae módem 5G. En el punto real, el router 5G va en el poste, igual que el CPE. Los 22–60 ms incluyen el Wi-Fi y el 5G.»
- **No decir:** «la ESP32 tiene 5G».

### 3. «¿Midieron 5G contra 4G? ¿Cuánto tarda el aviso en llegar al teléfono del guía?» (T)
- **Si se midió hoy:** dar las dos cifras (p50 y p95) y cuántas muestras.
- **Si no:** «La medición está armada: 50 avisos al XR20 y 200 muestras de ping por cada red. Es la prueba que falta, y por eso pedimos acceso prioritario al Testbed.»

### 4. «En una tormenta se cae la torre por falta de luz. Su 5G no sirve.» (T)
- **Respuesta:** «Correcto. Por eso el aviso más importante no depende de ninguna red: la sirena y la luz del cruce suenan solas, y cada punto tiene panel solar. En Noruega, más de 9 de cada 10 antenas que se caen en tormenta es por falta de luz. La prioridad 5G sirve cuando la red está viva pero saturada, como en Japón en 2011.»

### 5. «Si el semáforo dice LIBRE y alguien se ahoga, ¿quién responde?» (N)
- **Por qué la hacen:** es responsabilidad legal, y los jurados del sector público la piensan.
- **Respuesta:** «El sistema avisa el peligro; no autoriza a cruzar. Por eso en la versión real el verde dice "sin alerta", no "pase". Si se pierde el dato del sensor, nunca vuelve a verde: se queda en cuidado. Cada decisión queda registrada con su hora. Abrir o cerrar la vía lo decide el Conavi o la municipalidad.»
- **Dato del código:** sin datos de nivel, el estado «nunca baja y queda al menos en CUIDADO» (`edge/app/estado.py`).

### 6. «¿Qué tan preciso es? ¿Cuántas falsas alarmas?» (T)
- **Si se midió hoy:** «Con 5 marcas y 10 lecturas en cada una, el error máximo fue de X puntos; la meta es menos de 5.»
- **Además:** «No reabre de golpe: baja un escalón cada 30 s. Sin dato, no reabre.» Si el flotador está conectado: «el flotador confirma».
- **Si no se midió:** «La prueba está armada (5 × 10) y es la próxima medición.»

### 7. «¿Ya hablaron con el Conavi, la CNE, una municipalidad o un operador? ¿Alguien dijo que lo compraría?» (N)
- **Es un punto débil:** no hay ningún compromiso.
- **Respuesta:** «Todavía no hay nada firmado, y es lo que venimos a pedir. Lo que sí hay:
  - desde 2025, la Ley 10717 da plata para vados (15 % del impuesto a los combustibles);
  - el Conavi ya es operador autorizado de drones, o sea que tiene equipo técnico;
  - el jefe de la Promotora vio la demo y la publicó.

  Por eso pedimos el contacto con el Conavi y la CNE.»

### 8. «¿Qué tiene de distinto de lo que ya hacen el IMN, la CNE o Santa Ana?» (N)
- **Respuesta:** «Ellos miden cuencas para alertar a una comunidad. Nosotros estamos en el vado: decidimos ahí mismo y avisamos a quien va a cruzar, que es el guía, el turista, el conductor en Waze y quien oye la sirena. Además cuesta mucho menos: Santa Ana paga ₡7,5 millones por estación al año y nosotros cobraríamos unos ₡660 mil.»

### 9. «Una cabeza de agua llega en menos de un minuto. ¿Su aviso llega a tiempo?» (T)
- **Respuesta:** «En el vado, la sirena suena en cuanto el agua sube, sin esperar a nadie. Para ganar minutos va un segundo sensor río arriba: en Upala, con el huracán Otto, el río tardó unos 20 minutos en crecer. Además, el sistema detecta cuando el agua sube rápido, antes de llegar al límite.»

### 10. «¿Quién lo mantiene? En Texas murieron dos personas donde había sensores apagados.» (N)
- **Respuesta:** «El precio incluye 4 visitas al año. Y el sistema se vigila solo: si un sensor deja de mandar datos, el tablero lo marca y el cruce no vuelve a verde.»

### 11. «¿Alguien puede hackearlo y poner en verde un cruce peligroso?» (T)
- **Es un punto débil:** en el prototipo, el borde no le pide clave a quien manda datos.
- **Respuesta:** «En el prototipo todo corre dentro de la red privada del Testbed, que no acepta conexiones de afuera. Para el piloto, cada sensor lleva su propia clave y el tráfico va cifrado. Además, una lectura que salta sin sentido no abre el cruce, porque reabre de a un escalón.»
- **Dato:** Japón tuvo que apagar 337 cámaras de río por accesos no autorizados (MLIT, 2023). Nos lo tomamos en serio.

### 12. «¿Hay 5G en el río Vainilla?» (T)
- **Respuesta:** «Todavía no lo sabemos, y es lo primero que vamos a medir. Según la SUTEL, Liberty no tiene 5G en Puntarenas. Las opciones son Claro o kölbi, un nodo portátil de la CNE, o LoRa hasta un cerro con señal. La alarma local funciona igual.»

### 13. «¿Cuántos vados hay? ¿De qué tamaño es el mercado?» (N)
- **Respuesta:** «No hay un inventario nacional; la Ley 10717 obliga a hacerlo con Lanamme. Hay 30.534 km de caminos cantonales en lastre o tierra. Vamos de 1 punto a 10–20 en Puntarenas, que es el cantón con más declaratorias de emergencia, y después a 100 en el país.»
- **No decir:** «el 1 % de un mercado gigante».

### 14. «Quitaron la cámara. ¿Dónde está la inteligencia?» (T)
- **Respuesta:** «En el borde. Detecta la subida rápida antes del límite, cruza las fuentes, no reabre sin datos y reabre de a un escalón. La visión con IA ya está en el código, probada a 1,5 ms por cuadro, y es el módulo siguiente.»

### 15. «¿Qué hicieron ustedes y qué ya existía?» (P)
- **Respuesta:** «La placa es de Ricardo Jiménez Guido. Nosotros hicimos el programa de la ESP32, el servidor de borde con la lógica de decisión, las páginas del guía y del turista, y el aviso en el formato oficial de Waze. Tiene 165 pruebas automáticas.»

### 16. «¿Por qué no construir puentes?» (N)
- **Respuesta:** «Hay que construirlos. Pero el puente del Inder sobre el río Cóbano costó ₡363 millones, lo mismo que unos 360 puntos de Paso Seguro. Esto avisa mientras el puente llega.»

### 17. «¿Esos 22–60 ms son repetibles? ¿Cuántas muestras?» (T)
- **Respuesta honesta:** «El tablero calcula los percentiles en vivo. El miércoles a las 11:42 daba p50 de 31 ms y p95 de 44 ms de la ESP32 al borde, y se ve en el video. En la prueba con cartón hubo picos de 150 a 210 ms. Ir a un servidor en internet tardaba 1,7 s: por eso decidimos en el borde.»
- **No decir:** «siempre menos de 60 ms».

### 18. «¿Qué pasa si un tronco o basura queda bajo el sensor?» (T)
- **Respuesta:** «Una lectura que salta sin sentido no reabre el cruce. Con dos fuentes (flotador, o LiDAR en el piloto) se detecta el desacuerdo, y la visita de mantenimiento limpia el punto.»

### 19. «¿Y el turista sin datos ni señal?» (P)
- **Respuesta:** «Para eso están la sirena y la luz en la entrada del vado, que no necesitan teléfono. El QR es un extra para quien tiene señal.»

### 20. «¿Ya está en Waze?» (N)
- **Respuesta:** «Todavía no. El aviso ya sale en el formato oficial de Waze y pasa su validación. Waze for Cities no tiene costo, pero lo publica un socio oficial, como el Conavi o el MOPT. San Antonio, en Texas, hace esto mismo con 190 cruces desde 2023.»

---

## B. Puntos débiles: qué decir y qué hacer hoy

| # | Debilidad | Gravedad | Qué decir si sale | Qué hacer hoy |
|---|---|---|---|---|
| 1 | El hardware es frágil: el sensor se quedó sin corriente; los cables son puentes sueltos; el convertidor no está soldado (el Echo de 5 V entra directo a la ESP32) | **Alta** | — (que no se note) | Arreglarlo, fijar los cables con cinta y tener el video de respaldo listo |
| 2 | No medimos 5G contra 4G ni el aviso en el XR20, y el mentor lo pidió | **Alta** | Pregunta 3 | Medirlo |
| 3 | No hay ningún cliente ni usuario que lo haya validado: ni el Conavi, ni un guía | **Alta** | Pregunta 7 | Prueba con un usuario (10 min) |
| 4 | El guion dice «el flotador confirma» y el flotador no está conectado | Media | «El punto real lleva flotador; en la demo, el ultrasónico» | Conectarlo o cambiar la frase |
| 5 | El 5G llega al CPE; la ESP32 va por Wi-Fi | Media | Pregunta 2 | Decirlo con precisión |
| 6 | «LIBRE» suena a garantía | Media | Pregunta 5 | Decir «sin alerta» en las respuestas |
| 7 | No hay clave por dispositivo en el prototipo | Media | Pregunta 11 | — (es para el piloto) |
| 8 | No sabemos qué cobertura hay en el vado real | Media | Pregunta 12 | — |
| 9 | El borde es una laptop, no el MXIE | Media | «Es el mismo código; corre en el MXIE con un contenedor» | — |
| 10 | Los umbrales (40 % y 70 %) son de la maqueta | Media | «En el río se calibran con la forma del vado y las crecidas que se conocen» | — |
| 11 | Parte de los costos son estimaciones y precios de EE. UU. | Baja | «La electrónica es de tiendas de Costa Rica; lo estimado está marcado» | — |
| 12 | La latencia del 7-oct tuvo picos de 150–210 ms | Baja | Pregunta 17 | Medir los percentiles |
| 13 | Grafana no está instalado | Baja | «La historia queda en la lista de eventos con hora» | — |
| 14 | En el video de la Promotora se dijo «láser» | Baja | «Es ultrasónico» (pregunta 23 del banco) | — |

---

## C. Frases salvavidas

- «No tengo ese dato exacto. Lo que sí medimos es ___. Se lo hacemos llegar hoy.»
- «Esa es la prueba que falta, y por eso pedimos acceso al Testbed.»
- «Es justo el riesgo que más nos preocupa, y así lo cubrimos: ___.»
- «Para respetar el tiempo, lo resumo en una frase: ___.»
