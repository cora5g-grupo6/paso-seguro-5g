# Paso Seguro 5G · Qué falta para el pitch del viernes 9

Grupo 6 (CORA 5G) · armado el jueves 8 de octubre a las 9:00 (hora de Costa Rica).

Esta lista junta los requisitos y pendientes de todos los documentos del proyecto:
- el plan de trabajo (PLAN.md);
- la base del pitch (docs/PITCH-viernes-9.md), que armó la sesión del análisis con la guía de Oscar;
- el estado del prototipo (ESTADO.md);
- la investigación de mercado (docs/INVESTIGACION-mercado-costos-casos.md).

**Estado del equipo a las 8:58:** la placa no está conectada a la Mac y el borde está apagado. El sensor quedó **sin corriente** desde el miércoles a las 12:17, y sin corriente no hay demo, ni video, ni mediciones.

---

## 1. Requisitos del hackatón y cómo estamos

✅ listo · ⚠️ a medias · ❌ falta

| # | Requisito | De dónde sale | Estado | Qué falta |
|---|---|---|---|---|
| 1 | Exposición de 10 min (meta 9:00–9:30) y unos 5 min de preguntas. Sesiones desde las 9:30 a. m., 4 grupos por sesión | Guía de Oscar · reglas | ⚠️ El guion está listo (≈ 1.250 palabras) | Ensayar 3 veces con cronómetro. Confirmar a qué hora nos toca |
| 2 | Rúbrica: innovación, pertinencia, viabilidad técnica y escalabilidad (25 % cada una, nota de 1 a 5) | Reglas | ✅ El guion cubre los 4 criterios | — |
| 3 | Propuesta técnica con implementación: **mostrar el flujo completo funcionando**, ojalá con equipos del Testbed | Reglas del 5-oct | ⚠️ Funcionó el 7-oct: sensor → ESP32 → Wi-Fi FastMile → borde, en 22–60 ms | Devolverle la corriente al sensor, conectar la placa y prender el borde |
| 4 | **Entregables del jueves (hoy):** documento técnico (arquitectura, latencias medidas, planes B y costo por punto), idea de negocio, presentación y **video del prototipo** | PLAN, sección 3 | ⚠️ La idea de negocio y el costo por punto están listos. La presentación está actualizada sin cámara | **Documento técnico** (lo armo yo), **video** (falta) y cifras nuevas en la presentación. **La hora y el formato de entrega no están confirmados** |
| 5 | Evidencia de que esto debería existir | Mentor (U Latina) | ✅ Río Vainilla con 500 personas, 2–3 carros atascados por semana y 1 arrastrado por mes (La Nación, 14-sep-2024); Barú y Rincón de la Vieja (2026); Cruz Roja | — |
| 6 | **Tres indicadores medidos** | Mentor | ⚠️ El costo por punto está listo. El tiempo de aviso solo está medido en la laptop (4,3 ms). La precisión falta | Medir el aviso en el XR20 y la precisión (sección 2) |
| 7 | Medir en el Testbed: latencia, throughput, cobertura, movilidad y confiabilidad, y **5G contra 4G** con evidencia repetible | Mentor | ⚠️ Solo está la latencia del sensor (22–60 ms) | XR20 por 5G y comparación con 4G. Throughput y cobertura: decir «pregunta abierta» |
| 8 | **Probar con un usuario** | Mentor | ❌ | 10 min con alguien que no conozca el sistema |
| 9 | Viabilidad: quién paga, quién opera, regulación y escala | Mentor | ✅ Ley 10717, Conavi, CNE y operador turístico; precio de US$120 al mes | — |
| 10 | Escala en Centroamérica con aliados | Mentor | ✅ CEPREDENAC, COPECO y CONRED, y casos en Honduras y Guatemala | — |
| 11 | No prometer slicing | Grupo CCC | ✅ | — |
| 12 | Plan B si falla la demo en vivo | Guía de Oscar | ⚠️ La animación pública está lista (plan C) | **Grabar el video** (plan B) |
| 13 | Evidencia de que funciona fuera del equipo | — | ✅ El jefe de la Promotora filmó y publicó la demo del 7-oct ([YouTube](https://youtu.be/Aw2mkXoyZ-E)) | Citarlo en el pitch (ya está en el guion) y darle el crédito de la placa a Ricardo Jiménez Guido |

### Lo que el guion dice que pasa y hay que asegurar que pase en la demo

| El guion dice | Realidad hoy | Qué hacer |
|---|---|---|
| «un flotador lo confirma» (dos fuentes) | **El flotador no está conectado** (el programa tiene `PIN_FLOTADOR = -1`) | Elegir: conectarlo hoy (15 min con un cable a un pin libre y GND; yo cambio el programa y lo cargo) o cambiar la frase a «el punto real lleva flotador; en la demo, el ultrasónico» |
| «suena la alarma en el cruce» | No lo probamos con la placa actual | Ver que el zumbador o las luces de la placa respondan al pasar a CERRADO |
| «cortamos internet: el aviso local sigue igual» | No lo ensayamos esta semana | Ensayarlo y que quede en el video |
| «el guía recibe la alerta con sirena y voz» | Funciona en la página `/guia` | Abrirla en el XR20 y tocar «Activar alertas» |
| «queda registrado minuto a minuto» (Grafana) | **Grafana no está instalado en la laptop** | Mostrar la lista de eventos del tablero (ya cambiado en el guion) |
| «157 pruebas» | Ahora son **165** | Cambiarlo en la presentación (en el doc del pitch ya está) |

---

## 2. Qué hacer hoy, en orden

Los responsables salen del reparto de PLAN.md y se pueden cambiar entre todos. Lo que dice «Claude» lo hago yo.

### Ahora (9:00–10:00)

| # | Tarea | Quién | Tiempo |
|---|---|---|---|
| 1 | Preguntarle a la PCII (Carlos, CeNAT): **hora y formato de la entrega de hoy**, turno de mañana, mesa y corriente, y si tienen Grafana | Stuart o Randall | 10 min |
| 2 | Armar el equipo:<br>• placa conectada a la Mac por USB<br>• **adaptador enchufado y botón verde encendido**<br>• cable morado en 5VDC del bloque LCD y negro en GND, bien apretados<br>• sonda apuntando a una superficie a más de 30 cm | Wlady o Jorge | 10 min |
| 3 | Prender el borde en modo real y confirmar que el sensor mide. **Avísenme cuando esté el paso 2** | Claude | 2 min |

### Antes del almuerzo (10:00–12:30): las mediciones

| # | Tarea | Cómo | Quién | Tiempo |
|---|---|---|---|---|
| 4 | **Precisión del nivel**: 5 marcas × 10 lecturas | `cd tools && ../edge/.venv/bin/python medir_precision.py`: poner el cartón a 35, 45, 55, 65 y 75 cm (medidos con cinta) y apretar Enter en cada marca. Da el error en puntos contra la meta de menos de 5 | Jorge | 15 min |
| 5 | **Aviso en el XR20 por 5G**, con la red cargada | En el XR20 abrir `/guia?id=xr20` y tocar «Activar alertas». En la laptop: `../edge/.venv/bin/python medir_latencia.py -n 1 --guia xr20 --ciclos 50`. Mientras mide, 2 o 3 teléfonos ven video en la misma red | Wlady | 15 min |
| 6 | **Ping 5G contra 4G** desde el XR20 | Abrir `/medir` en el XR20. En 5G: «Medir al borde» y «Medir a la nube». Pasar a 4G: «Medir a la nube». Volver a 5G: «Enviar» | Wlady | 10 min |
| 7 | **Decidir el aviso por 4G** (ver la sección 4) | — | Wlady | — |
| 8 | **Prueba con un usuario** | Alguien que no conozca el sistema hace de guía con el XR20. Pasar el cruce a CERRADO y medir cuántos segundos tarda en decir qué hay que hacer. Después, 3 preguntas: ¿qué entendió?, ¿qué le faltó?, ¿lo usaría con un grupo? | Aina o Stuart | 10 min |
| 9 | Flotador: conectarlo o cambiar la frase (ver arriba) | — | Jorge decide | 15 min |
| 10 | Probar la alarma local de la placa | Pasar a CERRADO y ver el zumbador o las luces | Jorge | 5 min |
| 11 | Pasar las cifras medidas a la tabla de indicadores del pitch y al documento | — | Claude | 10 min |

### Tarde (13:00–17:00)

| # | Tarea | Quién | Tiempo |
|---|---|---|---|
| 12 | **14:00: congelar el código.** Desde ahí, solo arreglos | Todos | — |
| 13 | **Ya hay un video de respaldo:** el del 7-oct (85 s, sensor real con cartón, CUIDADO ↔ CERRADO en el laboratorio del Testbed), en `entregables/PasoSeguro-prueba-prototipo-7oct-1080p.mp4`. Copiarlo al USB. Si da tiempo, grabar uno de 60 s con la lista de tomas de la sección 3 (página del guía y corte de internet, que el del 7-oct no tiene) | Aina; Wlady opera | 10–45 min |
| 14 | **Actualizar la presentación** ([deck](https://claude.ai/artifact/PP6pp8pVLqyLWHBApphKPA)) con 4 cambios:<br>• las cifras medidas, 165 pruebas y el costo por punto;<br>• quién paga: Ley 10717, Conavi y US$120 al mes;<br>• 1 diapositiva o frase con casos (Japón y Corea);<br>• la petición al **Conavi** en lugar de la municipalidad, y la lista de eventos en lugar de Grafana | Aina, o la sesión del análisis | 30 min |
| 15 | ✅ **Documento técnico listo:** `docs/DOCUMENTO-TECNICO-jurado.md` y el PDF `entregables/PasoSeguro5G-Documento-tecnico.pdf` (9 páginas, con el anexo «Respuestas en mano» para imprimir). Falta completar las 3 mediciones de hoy y volver a generar el PDF | Claude | 10 min al tener las cifras |
| 16 | **Entregar** lo que pida la PCII (respuesta del paso 1) | Randall | — |

### Noche

| # | Tarea | Quién |
|---|---|---|
| 17 | Nombres en los roles (presentador, técnico, negocio y tiempo) y una credencial por persona | Todos |
| 17b | Repasar las 20 preguntas difíciles y los puntos débiles ([PREGUNTAS-DIFICILES-jurado.md](PREGUNTAS-DIFICILES-jurado.md)). Cada quien ensaya las suyas (T, N o P) | Todos |
| 18 | **3 ensayos con cronómetro:** uno normal, uno con falla simulada (pasar al video en menos de 10 s) y uno «cortando internet» | Todos |
| 19 | Preparar el bolso de mañana (sección 5) | Wlady |

---

## 3. Video de respaldo: tomas (60 s)

Un teléfono filma todo: la sonda, el cartón o el agua, la pantalla de la laptop y el XR20. Grabar con el código ya congelado.

| Segundo | Qué se ve | Qué se dice (voz en off o texto) |
|---|---|---|
| 0–8 | La sonda sobre el agua o el cartón, y el tablero en verde (LIBRE) con la latencia en vivo | «Este es el cruce. Está libre.» |
| 8–20 | Sube el agua o se acerca el cartón: el tablero pasa a **CUIDADO** | «Sube rápido: avisa antes del límite.» |
| 20–32 | **CERRADO**: el tablero y el mapa en rojo; suena la alarma de la placa | «Cerrado. Suena la alarma en el cruce.» |
| 32–42 | El XR20 en `/guia`: alerta con sirena y voz | «El guía recibe la alerta.» |
| 42–50 | La página del turista, en español y en inglés (QR) | «El turista la lee en su idioma.» |
| 50–60 | Se corta internet: sigue en CERRADO y la lista de eventos muestra las horas | «Sin internet, sigue avisando. Todo queda registrado.» |

Ojo: al bajar el agua, el semáforo baja un escalón cada 30 s, a propósito. No hace falta mostrar la bajada.

---

## 4. Decisiones que son de Wlady

| Decisión | Opciones | Recomendación |
|---|---|---|
| Aviso por 4G pública | **1.** Abrir el borde a internet con un túnel solo durante la medición (unos 10 min), y cerrarlo. **2.** Comparar con `/medir` (ping 5G al borde contra 4G a la nube) sin túnel. **3.** No medir 4G y decir «es la prueba que falta» | **1**: da la cifra que pidió el mentor. Mientras está abierto, cualquiera con el enlace podría tocar los botones de demo |
| Flotador | **1.** Conectarlo hoy. **2.** Cambiar la frase del guion | **1** si Jorge tiene el flotador y un cable; si no, **2** |
| Guardar el trabajo en git | Hay muchos cambios sin guardar desde el lunes: el programa de la ESP32, las herramientas de medición, `/medir`, los documentos y 8 pruebas nuevas | Guardar hoy, antes de congelar el código a las 14:00. Solo lo hago si lo piden |

---

## 5. Mañana viernes: montaje (llegar temprano)

**Llevar:**
- laptop cargada y su cargador;
- placa con el adaptador, el cable USB y la sonda;
- regleta;
- XR20 cargado;
- cartón o tubo con agua;
- cinta;
- batería USB;
- USB con el video.

**Antes de entrar (5 min):**
- [ ] Borde arriba: `http://localhost:8000/salud` responde.
- [ ] La ESP32 manda datos y el sensor mide (el tablero muestra la distancia).
- [ ] La alarma local suena al pasar a CERRADO.
- [ ] XR20 en `/guia` con «Activar alertas».
- [ ] Página del turista abierta (QR).
- [ ] Video de respaldo abierto y pausado en el segundo 0.
- [ ] Animación pública abierta (plan C): https://claude.ai/artifact/1Ar5y331s8UtbxXoHehog1
- [ ] Regla de oro: si algo falla, pasar al video en menos de 10 s, sin disculpas largas.

---

## 6. Lo que ya está listo

- **Sensor real de punta a punta (7-oct):** ESP32 con ultrasónico → Wi-Fi FastMile → borde, en 22–60 ms, probado con cartón.
- **165 pruebas automáticas** en verde.
- **Herramientas de medición:**
  - `medir_precision.py`;
  - `medir_latencia.py --guia`, probado de punta a punta;
  - la página `/medir`.
- **Costos y mercado:**
  - un punto cuesta US$1.135–2.195 y US$305–860 al año; precio de US$120 al mes;
  - quién paga: Ley 10717 (Conavi y municipalidades), CNE y operador turístico;
  - el mercado de Costa Rica;
  - los casos de Japón, Noruega, Corea, Texas y Bangladesh.
  - Página: https://claude.ai/artifact/UejvM95k9G4WHVkTu8fk71. Documento: docs/INVESTIGACION-mercado-costos-casos.md.
- **Guion minuto a minuto y banco de 22 preguntas**, actualizados hoy con costos, quién paga, el Conavi y los casos.
- **Presentación sin cámara**, hecha por la sesión del análisis.
- **Feed de Waze** validado contra el formato oficial.
- **Validación externa:** el jefe de la Promotora publicó nuestra demo del 7-oct ([YouTube](https://youtu.be/Aw2mkXoyZ-E)): «un desarrollo que podría salvar vidas». Pedirle el archivo original del video: sirve como respaldo extra si falla todo.
