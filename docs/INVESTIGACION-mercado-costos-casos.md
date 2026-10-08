# Paso Seguro 5G · Investigación de mercado, costos y casos

Grupo 6 (CORA 5G) · Hackatón 5G, PCII Coronado · corte del jueves 8 de octubre de 2026

Página para compartir (misma información, resumida): https://claude.ai/artifact/UejvM95k9G4WHVkTu8fk71

## Cómo leer este documento

Cada cifra lleva su fuente (enlace) y la fecha del dato. La columna «Origen» dice de dónde sale:

| Marca | Significa |
|---|---|
| **CR** | Precio o dato publicado en Costa Rica, con fuente |
| **INT** | Dato internacional con fuente |
| **EST** | Estimación nuestra (no tiene fuente directa) |
| **CALC** | Cálculo nuestro hecho con datos que sí tienen fuente |

- **Tipo de cambio:** ₡457,03 por dólar (venta del 8-oct-2026, [API de Hacienda](https://api.hacienda.go.cr/indicadores/tc/dolar)).
- **Lo que no encontramos** está al final, en la sección 10. No hay cifras inventadas: si algo no tiene fuente, dice EST o «no encontrado».

---

## 1. Resumen para el pitch

### Los 5 datos más fuertes

1. **Un punto cuesta ≈ US$1.135–2.195 (₡519.000–1.003.000) y US$305–860 al año.**
   - Santa Ana alquila hoy estaciones de alerta a ₡7,5 millones por estación al año ([Delfino, 6-feb-2026](https://delfino.cr/2026/02/municipalidad-de-santa-ana-pone-en-marcha-sistema-de-alerta-temprana)).
   - En Texas, un medidor en un cruce bajo cuesta US$20.000 ([Bexar County, 5-ago-2025](https://www.bexar.org/DocumentCenter/View/49132/04g-OCM-Next-Generation-Flood-Warning-System)).
2. **Desde 2025 hay plata por ley.**
   - La Ley 10717 destina el 15 % del impuesto a los combustibles a «puentes y vados»: 8 % al Conavi, 6 % a las municipalidades y 1 % a Lanamme.
   - Son unos ₡94.500 millones al año (CALC: 15 % de ₡630.000 millones de recaudación estimada para 2025).
3. **El vado del río Vainilla ya cobró una vida.** Unas 500 personas viven junto a él; cada semana se atascan 2 o 3 carros y cada mes uno es arrastrado ([La Nación, 14-sep-2024](https://www.nacion.com/sucesos/desastres/dueno-de-carro-arrastrado-en-rio-de-lepanto-cuenta/LKUXZKLPFVEXPIGVG26SPPY7ME/story/)). En 2024 hubo 3 casos en la Ruta Nacional 623 ([La Nación, 30-oct-2024](https://www.nacion.com/sucesos/accidentes/falta-de-puente-propicio-tragedia-de-odontologo/BK7KKUPPWRGQ7ODATIK3UUQSVE/story/)):
   - un carro con 5 personas arrastrado unos 500 m;
   - un 4x4 arrastrado;
   - un hombre de 79 años muerto.
4. **Las cabezas de agua matan en senderos turísticos.**
   - En 2025 hubo 36 muertes en ríos hasta el 13 de octubre (Cruz Roja).
   - En 2026 murió un guía en el río Barú (30-ago) y una turista en Rincón de la Vieja (13-sep).
5. **Cuando más se necesita la red, más falla.**
   - Con la tormenta Sara, unos 50.000 clientes del ICE tuvieron el móvil o internet degradado ([Semanario Universidad, 19-nov-2024](https://semanariouniversidad.com/?p=332316)).
   - En Japón 2011, la voz llegó a 50–60 veces lo normal y se bloqueó el 70–95 % de las llamadas ([MIC Japón](https://www.soumu.go.jp/johotsusintokei/whitepaper/eng/WP2011/part1.pdf)).

### Corregir en el guion antes del viernes

| Dice el guion | Problema | Usar |
|---|---|---|
| «~500 personas» y «un carro arrastrado por mes» | **Están bien.** [La Nación, 14-sep-2024](https://www.nacion.com/sucesos/desastres/dueno-de-carro-arrastrado-en-rio-de-lepanto-cuenta/LKUXZKLPFVEXPIGVG26SPPY7ME/story/): «aproximadamente 500 personas que viven cerca son las más afectadas»; «dos o tres carros quedan atascados en los ríos cada semana, y al menos uno es arrastrado mensualmente»; la ambulancia da «una vuelta de dos horas por Jicaral» | Mantenerlas. Se pueden sumar los 3 casos de 2024, uno mortal (La Nación, 30-oct-2024) |
| «La municipalidad de Puntarenas» instala el primer punto | El vado está en la **Ruta Nacional 623, que es del Conavi** | Pedir el contacto con el **Conavi (MOPT)** y la CNE |
| Lugar de la muerte de oct-2024 | La Nación dice Pilas de Canjel (Lepanto); CRHoy dice Carmona de Nandayure | «En la Ruta 623» |
| Waze para todo | El feed de Waze no admite rutas peatonales | Waze solo para el vado con carros; en senderos, la página del guía y el QR |

---

## 2. Costo de poner un punto

### 2.1 Punto base, sin cámara (ESP32 + ultrasónico + flotador + sirena + 5G + solar)

| Componente | Bajo US$ | Alto US$ | Origen y fuente |
|---|---:|---:|---|
| Placa ESP32 | 14,95 | 14,95 | CR · [CRCibernética](https://www.crcibernetica.com/esp32-wifi-and-bluetooth-dev-board/), 90 en stock |
| Sensor ultrasónico impermeable (zona ciega 25 cm, alcance 4,5 m, cable 2 m, tipo JSN-SR04T) | 19,95 | 19,95 | CR · [CRCibernética](https://www.crcibernetica.com/ultrasonic-waterproof-sensor/) |
| Flotador de nivel (0,5 A, necesita relé) | 4,95 | 4,95 | CR · [CRCibernética](https://www.crcibernetica.com/water-level-float-sensor-switch/) |
| Gabinete IP67 160×160×90 mm | 13,95 | 13,95 | CR · [CRCibernética](https://www.crcibernetica.com/ip67-enclosure-flanged-160/) |
| Sirena con luz 12 V, 115 dB, 300 mA | 5,95 | 5,95 | CR · [CRCibernética](https://www.crcibernetica.com/siren-with-light-12v-115db/) |
| Panel solar (50 W → 100 W) y controlador PWM | 80 | 210 | CR · [LEDXPRES 100 W ₡85.000](https://www.ledxpres.com/producto/panel-solar-100w/) y [controlador desde ₡10.800](https://www.ledxpres.com/producto/controlador-de-carga-solar/) · INT · [Renogy 50 W US$55,99](https://www.renogy.com/products/50-watt-12-volt-monocrystalline-solar-panel) |
| Batería 12 V (plomo-ácido 20 Ah → LiFePO4) | 80 | 193 | INT · [NOAA US$80](https://secoora.org/wp-content/uploads/2023/06/10-Fiorentino-Demos-of-Equipment.pdf) · [Bioenno 20 Ah US$192,99](https://www.bioennopower.com/collections/12v-lifepo4-batteries/escooter-batteries) |
| Router 5G industrial Teltonika RUTX50 | 516 | 830 | INT · [TME vía Findchips US$516–547](https://www.findchips.com/search/RUTX50) · Bits-Mart hasta US$1.054 · [RS UK £413,77](https://uk.rs-online.com/web/p/routers/0428092) |
| Poste galvanizado de 6 m, concreto, herrajes y cableado | 150 | 400 | CR · [tubo EPA 75 mm ₡15.750](https://cr.epaenlinea.com/tubo-para-malla-galvanizado-75-mm-c18-mm-6-m.html) · el resto es EST (en EE. UU. los herrajes cuestan US$500–1.000 según TWDB) |
| Instalación y traslado (2 técnicos × 2 días, cargas sociales y viáticos) | 250 | 500 | EST con [salario mínimo MTSS 2026](https://www.mtss.go.cr/temas-laborales/salarios/lista_salarios_minimos_2026.pdf): técnico especializado ₡16.244,50 por jornada |
| **Total por punto** | **≈ 1.135** | **≈ 2.195** | **₡519.000–1.003.000** |

**Reparto del costo medio** (CALC):

| Parte | % del costo |
|---|---:|
| Router 5G | 40 |
| Instalación | 23 |
| Energía | 17 |
| Poste | 17 |
| Sensores, ESP32 y sirena | 3,6 |

### 2.2 Variantes y repuestos

| Opción | Precio | Fuente |
|---|---|---|
| Sensor sumergible 0–6 m, 4-20 mA, IP68, cable 6,5 m (tercera fuente de nivel) | US$72,95 | CR · [CRCibernética](https://www.crcibernetica.com/submersible-water-level-sensor-0-6m-h2o/) |
| DFRobot A02YYUW, ultrasónico IP67 de 3 a 450 cm | US$15,90 | INT · [DFRobot](https://www.dfrobot.com/product-1935.html) |
| Sensor de nivel sin contacto | US$16,95 | CR · [CRCibernética](https://www.crcibernetica.com/non-contact-liquid-level-sensor/) |
| ESP32-C3 / ESP32-S3 | US$7,95 / 21,95 | CR · CRCibernética |
| Control de nivel hermético 3M Viyilant | ₡16.995 | CR · [EPA](https://cr.epaenlinea.com/control-nivel-hermetico-3m-viyilant.html) |
| Router 4G Teltonika RUT241 (en lugar de 5G) | US$219 | INT · [NTS Direct](https://shop.ntsdirect.com/product/RUT241033000-Z/Teltonika-RUT241033000-UNIVERSAL-PSU.html) |
| Router 5G Teltonika RUTM50 | US$629 | INT · [NTS Direct](https://shop.ntsdirect.com/product/RUTM50000000-Z/Teltonika-RUTM50000000---RUTM50-Cellular-5G-Router.html) |
| Batería LiFePO4 12 V 50 Ah | US$188,99 | INT · [LiTime](https://www.litime.com/products/litime-12v-50ah-lifepo4-lithium-ion-battery) |
| Batería LiFePO4 12 V 100–200 Ah | ₡305.000–635.000 | CR · [LEDXPRES](https://www.ledxpres.com/producto/bateria-de-litio-lifepo4-12v/) |
| Letrero LED programable 40×8 pulgadas | US$99,90 | INT · [VEVOR](https://www.vevor.com/s/cheap-led-signs) |
| Baliza vial solar TAPCO BlinkerBeacon | desde US$1.645 | INT · [TAPCO](https://www.tapconet.com/product/24-7-flashing-led-blinkerbeacon) |

### 2.3 Módulo cámara (siguiente fase)

| Concepto | Costo | Fuente |
|---|---|---|
| Cámara Reolink Go PT Ultra (4G, 4K, batería y solar) | US$229,99 | INT · [Reolink](https://store.reolink.com/us/go-series-cameras/) |
| Cámara exterior 2K con panel solar IP66 (WiFi) | ₡46.450 | CR · [EPA](https://cr.epaenlinea.com/camara-inteligente-para-exterior-2k-con-movimiento-incluye-panel-solar-ip66-vta.html) |
| Webcam para cruce bajo (presupuesto público) | US$200 | INT · [Bexar County](https://www.bexar.org/DocumentCenter/View/49132/04g-OCM-Next-Generation-Flood-Warning-System) |
| Refuerzo de panel y batería | US$250–600 | EST |
| **Total del módulo** | **+ US$450–800** | EST con las filas de arriba |
| Datos de video al año | ≈ US$500 | CALC con el memo de [Chehalis (WA)](https://www.ezview.wa.gov/Portals/_1492/images/Staff%20memo%20--%202025%20Flood%20Warning%20System%20Costs%2011-21-2024.pdf): US$1.500 al año por 3 planes |

### 2.4 Borde compartido por zona

| Concepto | Costo | Fuente |
|---|---|---|
| Mini PC Intel N150 (el N100 ya no se vende) | US$240–385 | INT · [GMKtec G2 Plus](https://www.gmktec.com/products/gmktec-nucbox-g2-plus-mini-pc-intel%C2%AE-twin-lake-n150) · [Beelink EQ14](https://www.bee-link.com/products/beelink-eq14-n150) |
| NVIDIA Jetson Orin Nano Super (si hiciera falta GPU) | US$249 | INT · [NVIDIA, 17-dic-2024](https://blogs.nvidia.com/blog/jetson-generative-ai-supercomputer/) |
| UPS e instalación | US$180–500 | EST |
| **Por zona** | **US$420–885** | |
| **Por punto, con 5 puntos por zona** | **US$85–175** | CALC |

---

## 3. Costo de operación por año (por punto)

| Concepto | Bajo US$ | Alto US$ | Origen y fuente |
|---|---:|---:|---|
| Datos móviles (el punto base usa 1–2 GB al mes) | 65 | 240 | CR · [kölbi: 1 GB por ₡2.500, 3 GB por ₡5.000](https://www.kolbi.cr/wps/portal/kolbi/personas/servicios/postpago/planespostpago/planes/paquetes-internet-postpago) · [Liberty: 5 GB por ₡5.000](https://libertycr.com/web/movil/prepago/ultra-en) · INT · TWDB: US$10–20 al mes |
| Mantenimiento: 4 visitas al año | 150 | 400 | EST · TWDB recomienda visitas cada 2–3 meses |
| Batería y repuestos | 40 | 70 | EST · la batería dura 3–5 años |
| Parte del borde compartido | 50 | 150 | EST |
| **Total por año** | **≈ 305** | **≈ 860** | **₡139.000–393.000** |

Otras referencias de operación:

| Concepto | Cifra | Fuente |
|---|---|---|
| Planes pospago kölbi k1 / k2 / k3 plus / Ilimitado | ₡12.000 / 16.500 / 21.500 / 44.000 al mes | CR · [kölbi, desde 26-mar-2026](https://www.kolbi.cr/wps/wcm/connect/www.kolbi.cr/57b9d68d-2693-472d-af86-d8a371d6c26f/kolbi-terminos-y-condiciones-de-planes-postpago-k-plus+(a+partir+del+26+de+marzo+2026).pdf?MOD=AJPERES) |
| Planes IoT o M2M de kölbi, Claro y Liberty | No tienen precio público; hay que cotizarlos (kölbi 1193) | — |
| Electricidad residencial / comercial | ₡85,9 / ₡107,96 por kWh | INT · [GlobalPetrolPrices, mar-2026](https://www.globalpetrolprices.com/Costa-Rica/electricity_prices/) |
| Taxi rural, referencia por km | ₡940 de banderazo y ₡940 por km | CR · [ARESEP, desde 3-sep-2026](https://aresep.go.cr/taxi-tarifas/tarifas-taxi-base-operacion-regular-flota-roja/) |
| SMS a Costa Rica (Twilio) | US$0,1031 por mensaje | INT · [Twilio](https://www.twilio.com/en-us/sms/pricing/cr) |
| Plataforma IoT Ubidots Professional | US$99 al mes por 50 equipos | INT · [Ubidots](https://ubidots.com/pricing) |
| Salarios mínimos 2026 (Decreto 45303-MTSS), por jornada | Electricista (TOC) ₡13.991,86 · técnico especializado (TOE) ₡16.244,50 · técnico especializado superior (TES) ₡25.209,80 · peón ₡12.436,41 | CR · [MTSS](https://www.mtss.go.cr/temas-laborales/salarios/lista_salarios_minimos_2026.pdf) |

---

## 4. Precio propuesto y precios del mercado

### 4.1 Nuestra propuesta (EST)

| Modelo | Precio | Para quién |
|---|---|---|
| Suscripción todo incluido, contrato de 5 años | **US$120 al mes por punto** (≈ ₡54.800; ₡658.000 al año) | Municipalidad, Conavi u operador turístico que paga con presupuesto de operación |
| Compra con servicio | **US$2.200 de instalación + US$70 al mes** | Quien compra con presupuesto de inversión |

- **Nuestro costo medio a 5 años:** unos US$80 al mes por punto, así que el margen es de un tercio (CALC: instalación media US$1.664, más US$130 de borde, más US$583 al año durante 5 años).
- **Comparación con Santa Ana:** ellos pagan ₡7,5 millones por estación al año, unas 11 veces nuestro precio (CALC).

### 4.2 Lo que cobran o pagan otros

| Caso | Cifra | Fuente | Fecha |
|---|---|---|---|
| **Santa Ana (CR):** 10 estaciones de alerta en las cuencas Uruca y Corrogres, alquiler llave en mano | **₡75 millones al año** | CR · [Delfino](https://delfino.cr/2026/02/municipalidad-de-santa-ana-pone-en-marcha-sistema-de-alerta-temprana) | 6-feb-2026 |
| Galveston County (Texas): 8 sensores con IA, pago inicial | US$49.500 (≈ US$6.190 por sensor) | INT · [GovTech](https://insider.govtech.com/texas/news/ai-flood-warning-system-goes-live-in-galveston-county) | contrato del 9-sep-2025 |
| Galveston: servicio de datos / mantenimiento | US$23 al mes por sensor / US$100 al año | misma | 9-sep-2025 |
| Proveedor con web y telemetría (Texas) | US$200–1.000 al año por medidor | INT · [guía TWDB, p. 16](https://www.twdb.texas.gov/flood/research/early-warning-system/TWDB_Alternative_Flood_Early_Warning_System_Guide_2025.pdf) | 15-sep-2025 |
| HydroVu (In-Situ) | hasta US$35 al mes por equipo | INT · [Frontier Precision](https://frontierprecision.com/news/remote-water-quality-level-monitoring-made-easy/) | 20-ene-2020 |
| Transmisor VuLink celular / satelital | US$795 / 1.495 | misma | 20-ene-2020 |
| FloodFlash (Reino Unido) | £100 + IVA al año por sensor | INT · [Property Insurance Centre](https://www.propertyinsurancecentre.co.uk/faq-items/what-does-the-sensor-fee-cover/) | 18-dic-2024 |
| OneRain, plataforma de 306 sensores | US$7.000 al año | INT · memo de Chehalis | 21-nov-2024 |
| FloodNet NYC: hardware de un sensor ultrasónico | ≈ US$200 | INT · [Eos](https://eos.org/research-spotlights/alerting-communities-to-hyperlocalized-urban-flooding) | 9-may-2024 |
| Levelynx: suscripción con hardware incluido, sin pago inicial | Modelo confirmado; el monto no es público | INT · comunicado (solo lo vimos en el buscador) | 3-jun-2026 |

---

## 5. Comparables de costo por sitio

| Caso | Instalación | Operación al año | Fuente | Fecha |
|---|---|---|---|---|
| **Paso Seguro, punto base** | **US$1.135–2.195** | **US$305–860** | este documento | 8-oct-2026 |
| Sistema «alternativo» de alerta (Texas) | US$2.000–10.000 | US$500–2.000 | INT · [guía TWDB](https://www.twdb.texas.gov/flood/research/early-warning-system/TWDB_Alternative_Flood_Early_Warning_System_Guide_2025.pdf) | 15-sep-2025 |
| Medidor tradicional | US$30.000–60.000 | US$5.000–20.000 | misma guía, p. 6 | 15-sep-2025 |
| SETx (Texas): 73 sitios con sensor de presión, cámara y celular | ≈ US$4.000 cada uno; vida útil de 10 años; plan celular ≈ US$40 al año | — | misma guía, p. 24 | precios de 2021–2023 |
| Amarillo: 8 estaciones tradicionales OTT | US$50.000 por sitio (US$400.000 en total) | — | misma guía, p. 26 | 2025 |
| Bexar County: medidor nuevo en un cruce bajo | US$20.000 | — | INT · [Bexar](https://www.bexar.org/DocumentCenter/View/49132/04g-OCM-Next-Generation-Flood-Warning-System) | 5-ago-2025 |
| Bexar: barrera automática en un cruce bajo | US$80.000 | — | misma | 5-ago-2025 |
| Bexar: programa NextGen | ≈ US$22 millones; ya tiene unos 80 sistemas HALT | — | misma | 5-ago-2025 |
| Condado de Hays: 16 sitios con sensor y 2 señales intermitentes solares | ≈ US$50.000 por sitio (CALC sobre ≈ US$800.000) | — | INT · [FEMA](https://www.fema.gov/node/452588) | 2007–08 |
| Austin: rehacer un cruce bajo | «de cientos de miles a millones» | — | INT · [KUT](https://www.kut.org/transportation/2025-07-16/austin-tx-floods-fix-low-water-crossings-roads-drive-safety) | 16-jul-2025 |
| Austin: piloto de cámaras en Onion Creek | US$24.000 por 2 años | — | INT · [Fox 7](https://www.fox7austin.com/news/austin-looks-to-expand-use-of-surveillance-cameras-against-flash-flooding) | 22-ene-2015 |
| Kansas City: mantener un sitio municipal / uno del USGS | — | US$2.900 / US$5.800 | INT · [OpenGov](https://stories.opengov.com/kansascitymo/published/sSKiLqdb9) | sin fecha |
| Chehalis (WA): 19 medidores y 3 webcams | — | ≈ US$3.700 por medidor (CALC sobre US$70.856) | INT · memo | 21-nov-2024 |
| Medidor del USGS en Montana | ≈ US$7.800 en un sitio fácil; con cable vía, más de US$100.000 | US$18.265 (todo el año) / US$12.800 (por temporada) | INT · [Montana DNRC](https://dnrc.mt.gov/_docs/water/Gage-Work-Group-Meeting-Summary-2020-August-12.pdf) | ago-2020 |
| ICE (CR): modernización de 314 estaciones hidrometeorológicas | US$7,58 millones (≈ US$24.100 por estación, CALC; es modernización, no estación nueva) | — | CR · [Delfino](https://delfino.cr/2025/01/ice-invirtio-758-millones-en-modernizacion-de-314-estaciones-hidrometeorologicas) | 31-ene-2025 |
| Medellín (SIATA): 43 sistemas en 41 quebradas, para más de 44.800 personas | 3.435 millones de pesos colombianos el convenio (≈ 80 millones por sistema, CALC) | — | INT · [Telemedellín](https://telemedellin.tv/?p=196841) | 17-sep-2026 |
| Brasil, e-Noé (USP): sensor de presión, cámara y módem 4G | ≈ R$15.000 por sistema | — | INT · [Pesquisa FAPESP](https://revistapesquisa.fapesp.br/dispositivo-emite-em-tempo-real-alertas-contra-enchentes/) | 7-jul-2022 |
| Kenia, río Muringato: nodo LoRaWAN con ultrasónico y panel, 18 meses en campo | US$90 por nodo | INT · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10050633/) | 17-mar-2023 |
| **Puente nuevo del Inder sobre el río Cóbano (CR)** | **₡363,3 millones (≈ US$795.000), lo mismo que unos 360 puntos base** | — | CR · [Delfino](https://delfino.cr/2026/01/inder-puente-sobre-el-ro-cbano-en-puntarenas-garantiza-conectividad-y-seguridad-para-ms-de-17500-habitantes) | 23-ene-2026 |

**Muertes y retorno de la alerta temprana**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| EE. UU.: muertes por inundación al año / parte que muere en vehículos | ≈ 100 / ≈ 50 % | INT · [NWS](https://www.weather.gov/news/181007-tadd-psa) | 10-jul-2018 |
| Texas: muertes por inundación en cruces bajos o calles inundadas | ≈ 70 % | INT · [Community Impact](https://communityimpact.com/south-central-austin/texas-legislature/its-going-to-reduce-misery-texas-adopts-first-statewide-flood-plan/) | 15-ago-2024 |
| Avisar con 24 horas de anticipación | Reduce el daño un 30 %; relación costo-beneficio de 1 a 9 | INT · [OMM](https://wmo.int/node/25794) | 15-may-2025 |
| Invertir US$800 millones en alerta temprana en países en desarrollo | Evita US$3.000–16.000 millones de pérdidas al año | misma | 15-may-2025 |

---

## 6. Mercado en Costa Rica

### 6.1 Vados y red vial

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| **Inventario nacional de vados** | **No existe uno público.** La Ley 10717 obliga a armarlo, con Lanamme | CR · [Anuario MOPT 2023](https://repositorio.mopt.go.cr/server/api/core/bitstreams/0ed8bf22-b5fe-4817-a0c7-b88e685f51c1/content) · Ley 10717 | 2023 / 2025 |
| Red vial total | 45.899 km: 12.967 pavimentados y 32.931 en lastre o tierra (72 % sin pavimentar, CALC) | CR · Anuario MOPT 2023 | 2023 |
| Red vial nacional | 7.845 km, de los que 2.397 están en lastre o tierra | misma | 2023 |
| **Red vial cantonal** | **38.053 km, de los que 30.534 están en lastre o tierra (80 %, CALC)** | misma, según el inventario SIGVI de 2021 | 2023 |
| Caminos cantonales de lastre en estado malo o muy malo | 12.296 km (40 %) | misma, cuadro 2.4 | 2023 |
| Red cantonal según la UCR | 60 % en estado regular a muy malo | CR · [UCR](https://www.ucr.ac.cr/noticias/2023/4/23/el-60-de-la-red-vial-cantonal-la-mas-extensa-del-pais-se-encuentra-en-estado-de-regular-a-muy-malo.html) | 23-abr-2023 |
| Puentes en rutas cantonales | ≈ 8.200; «se desconoce su estado actual» | CR · [CRHoy](https://crhoy.com/nacionales/directora-de-puentes-del-mopt-sin-interes-ni-presupuesto-no-hay-intervencion/) | 12-sep-2022 |
| Puentes cantonales inspeccionados por Lanamme (600) | 2 de cada 3 tienen deterioro; el 57 % tiene al menos un elemento con daño grave | CR · [Semanario Universidad](https://semanariouniversidad.com/universitarias/dos-de-cada-tres-puentes-cantonales-presentan-deterioro/) | 17-dic-2018 |
| Puentes de la red nacional evaluados (1.927) | 43 % deficientes, 24 % alarmantes y 51 en falla inminente | CR · [Delfino](https://delfino.cr/2024/04/defensoria-investigara-deterioro-de-la-infraestructura-de-puentes-del-conavi) | 16-abr-2024 |
| Ejemplos de cantones | Montes de Oro: 214 km cantonales, 78 % en lastre · Sarapiquí: 1.200 km, 70 % en lastre | CR · planes municipales y [Delfino](https://delfino.cr/2025/04/municipalidad-de-sarapiqui-invierte-570-millones-para-arreglar-su-red-vial) | 2023 / 2025 |

### 6.2 El vado del río Vainilla

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Ubicación | Pilas de Canjel, distrito de Lepanto (Puntarenas), sobre la **Ruta Nacional 623 (Conavi)**, de 13,65 km | CR · [La Nación](https://www.nacion.com/sucesos/accidentes/falta-de-puente-propicio-tragedia-de-odontologo/BK7KKUPPWRGQ7ODATIK3UUQSVE/story/) | 30-oct-2024 |
| Comunidades que pidieron el puente por carta, sin respuesta | 5: Vainilla, Juan de León, Jabillo, Coyote e I Griega | misma | 30-oct-2024 |
| Otros pasos sin puente en la misma ruta | quebradas La Sierra y Balsa; «ni siquiera existen señales de advertencia» | misma | 30-oct-2024 |
| Carro arrastrado (22 de julio) | unos 500 m, con 2 mujeres y 3 niños; todos sobrevivieron | misma | 2024 |
| 4x4 arrastrado | el conductor sobrevivió | CR · [CRHoy](https://crhoy.com/nacionales/video-carro-4x4-fue-arrastrado-por-la-corriente-de-un-rio-en-lepanto) | 7-sep-2024 |
| Muerte de un odontólogo | murió un hombre de 79 años y sobrevivió otro de 73 | CR · La Nación y [CRHoy](https://crhoy.com/nacionales/buscan-a-desaparecido-luego-de-que-carro-quedara-atrapado-en-rio) | 29-oct-2024 |
| Población del distrito de Lepanto | 12.163 habitantes (9.502 en 2011) | INT · Wikipedia, con datos del censo | 2022 |
| **Personas más afectadas y frecuencia** | «aproximadamente 500 personas que viven cerca»; «dos o tres carros quedan atascados en los ríos cada semana, y al menos uno es arrastrado mensualmente»; la ambulancia da «una vuelta de dos horas por Jicaral» | CR · [La Nación](https://www.nacion.com/sucesos/desastres/dueno-de-carro-arrastrado-en-rio-de-lepanto-cuenta/LKUXZKLPFVEXPIGVG26SPPY7ME/story/) | 14-sep-2024 |
| Lepanto entre las zonas más afectadas por inundación según la CNE | sí | CR · [El Observador](https://observador.cr/emergencias-por-inundacion-aumentaron-un-123-los-primeros-seis-meses-del-ano/) | 31-jul-2024 |

### 6.3 Muertes e incidentes

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Muertes por accidentes acuáticos (Cruz Roja), de 2020 a 2025 | 96 · 108 · 119 · 132 · 143 · 128 | CR · [El Observador](https://observador.cr/menos-fallecidos-pero-mas-traslados-criticos-por-accidentes-acuaticos-este-ano-cruz-roja-insiste-en-prevencion/) | 30-dic-2025 |
| 2025, al 13 de octubre | 105 muertes: **36 en ríos**, 42 en playas, 8 en piscinas y 19 en otros lugares | CR · [El Observador](https://observador.cr/cruz-roja-reporta-105-muertes-por-accidentes-acuaticos-dos-ninos-murieron-este-domingo-en-alajuela/) | 13-oct-2025 |
| Ríos con más muertes en 2024 | Medio Queso, Barú y Jiménez, con 2 cada uno | CR · El Observador | 23-dic-2024 |
| **Guía muerto en el río Barú** (Pérez Zeledón) | 2 personas arrastradas, 1 muerto (el guía) y entre 25 y 40 rescatadas | INT · [Tico Times](https://ticotimes.net/2026/08/30/costa-rica-flash-flood-perez-zeledon-hikers-stranded) · CR · [CRHoy](https://crhoy.com/encuentran-sin-vida-a-guia-arrastrado-por-cabeza-de-agua/) | 30-ago-2026 |
| **Catarata Oropéndola, Rincón de la Vieja** | 6 arrastrados; murió una estadounidense de 35 años (fuera del parque, según el SINAC) | CR · [CRHoy](https://crhoy.com/estadounidense-es-la-victima-mortal-de-cabeza-de-agua-en-guanacaste/) | 13-sep-2026 |
| Catarata La Leona (Liberia) | 3 muertos en una excursión | CR · [El Observador](https://observador.cr/tres-personas-mueren-al-ser-arrastradas-por-una-cabeza-de-agua-en-una-catarata-en-liberia/) | 13-sep-2025 |
| Río Chiquito (Tilarán): pickup que cruzaba el río | 1 muerto de 70 años | CR · [Teletica](https://www.teletica.com/amp/sucesos/cabeza-de-agua-cobra-la-vida-de-adulto-mayor-en-tilaran_412812) | 2-jul-2026 |
| Río Parismina y río Costa Rica (Guápiles) | 2 muertos y 1 desaparecido | CR · El Observador y Teletica | 4 y 5-may-2026 |
| Nauyaca (Barú) | murió una turista estadounidense de 30 años (la cabeza de agua no está confirmada) | INT · [Tico Times](https://ticotimes.net/2026/06/20/family-confirms-body-found-in-costa-rica-is-missing-u-s-tourist) | jun-2026 |
| Incidentes por lluvias o inundaciones en 2024 | 7.315, el máximo en 11 años | CR · [Teletica](https://www.teletica.com/7-dias/costa-rica-bajo-agua_390705) | 18-ago-2025 |
| Recomendación de la CNE y el IMN | «Evitar cruzar ríos crecidos o calles inundadas» | CR · [El Observador](https://observador.cr/cne-reporta-mas-de-250-incidentes-por-inundacion-este-ano-en-costa-rica-fuertes-lluvias-siguen-este-martes/) | 3-jun-2025 |
| Emergencia nacional de agosto 2026 | 9 cantones; hasta 360 l/m² en 48 h; 13 sectores de Talamanca incomunicados | CR · [Delfino](https://delfino.cr/2026/08/gobierno-declara-emergencia-nacional-en-nueve-cantones-por-temporales-de-agosto) | 25-ago-2026 |
| Percepción de preparación | 8 de cada 10 personas creen que el país está poco o nada preparado | CR · [Delfino, encuesta UNA](https://delfino.cr/2025/12/estudio-una-8-de-cada-10-ciudadanos-considera-que-el-pais-esta-poco-o-nada-preparado-para-afrontar-un-desastre) | dic-2025 |

### 6.4 Pérdidas por desastres

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Declaratorias de emergencia entre 2005 y 2023 | 38, de las que 26 fueron hidrometeorológicas (68 %) | CR · [Tecnología en Marcha](https://revistas.tec.ac.cr/index.php/tec_marcha/article/download/7889/8158/30799) | 2026 |
| Pérdidas entre 2005 y 2023 | ₡2.341 miles de millones; **carreteras y puentes ₡765.282 millones (33 %)** | misma | 2026 |
| Pérdida hidrometeorológica promedio | ₡117.025 millones al año | misma | 2026 |
| **Cantón con más declaratorias** | **Puntarenas: 16**, el máximo del país | misma | 2005–2023 |
| Pérdidas entre 1988 y 2018 | US$4.592 millones (de 2015), el 0,8 % del PIB anual | CR · [MIDEPLAN](https://www.cepal.org/sites/default/files/presentations/sistema_nacional_de_inversion_publica_en_costa_rica_-_mideplan.pdf) | may-2019 |

### 6.5 Turismo

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Llegadas internacionales | 2.943.991 en 2025 (2.689.278 por avión) | CR · ICT / [La Nación](https://www.nacion.com/economia/visitacion-turistica-en-costa-rica-cierra-2025-con/XWCETNHXI5GZRFGWEE7SEXD62Q/story/) | ene-2026 |
| Actividades de los turistas (encuesta aérea del ICT, promedio 2023–2025) | aventura 56,5 % · caminatas por senderos 32 % · flora y fauna 37,1 % · rafting 8,3 % · canyoning 3,9 % | CR · [ICT](https://ict.go.cr/en/documents/estadísticas/cifras-turísticas/actividades-realizadas/1404-principales-actividades.html) | 2023–2025 |
| Turistas por avión que hicieron aventura en 2025 | ≈ 1,52 millones | CALC | 2025 |
| Visitas a áreas silvestres protegidas | 2.970.516 en 2025, de las que más de 1,2 millones son de residentes | CR · [El Mundo CR](https://elmundo.cr/tendencias/casi-3-millones-de-visitas-al-ano-dependen-del-cuidado-de-las-areas-protegidas/) | 29-sep-2026 |
| Empresas con declaratoria turística del ICT | 2.088 (139 son actividades temáticas) | CR · [Delfino](https://delfino.cr/2026/08/ict-digitaliza-el-tramite-de-declaratoria-turistica-para-empresas-del-sector) · [Memoria ICT 2025](https://ict.go.cr/en/documents/memorias-institucionales/3320-memoria-institucional-2025/file.html) | 13-ago-2026 |
| Credenciales de guías de turismo tramitadas | 916 en 2025 | CR · Memoria ICT 2025 | 2025 |

### 6.6 Escenario de crecimiento

Los números de puntos son metas nuestras, no un inventario.

| Fase | Puntos | Dónde | Ingreso al año (a US$1.440 por punto) |
|---|---|---|---|
| Piloto 2027 | 1 | Vado del río Vainilla, Ruta 623, con el Conavi | US$1.440 |
| Zona 2027–2028 | 10–20 | Vados de Puntarenas y senderos con muertes recientes: Barú, Curubandé y Rincón de la Vieja | US$14.400–28.800 |
| País | 100 o más | 1 o 2 por cantón en los 84 cantones, según el inventario de la Ley 10717 | ≈ US$144.000 (el 0,07 % de la plata anual de la Ley 10717, CALC) |
| Región | — | Guatemala y Honduras, con CONRED y COPECO, por medio del CEPREDENAC | — |

---

## 7. Quién paga

### 7.1 Leyes con plata para esto

| Ley | Qué dice | Monto | Fuente | Fecha |
|---|---|---|---|---|
| **Ley 10717** (exp. 23.562), «puentes y vados» | 15 % del impuesto a los combustibles: 8 % al Conavi, 6 % a las municipalidades y 1 % a Lanamme para inventarios. El 6 % municipal se reparte en un 60 % según los puentes y vados inventariados y en un 40 % según el Índice de Desarrollo Social | ≈ ₡94.500 millones al año (CALC) | CR · [Bufete de Costa Rica](https://bufetedecostarica.com/adicion-articulo-5-bis-ley-8114-puentes-y-vados-en-costa-rica-10717/) · [texto final](https://proyectos.conare.ac.cr/asamblea/23562%20REDACCION%20FINAL.pdf) | La Gaceta 115, Alcance 77, 24-jun-2025 |
| Ley 8114 / 9329 (red vial cantonal) | 22,25 % del impuesto a las municipalidades. La red cantonal incluye por definición la «infraestructura de seguridad vial» y el «señalamiento» | ₡131.764 millones por ley en 2025 (se presupuestaron ₡119.119 millones); ≈ ₡115.000 millones al año reales | CR · [Delfino](https://delfino.cr/2024/09/agrupaciones-municipales-denuncian-recortes-a-recursos-para-vias-cantonales-en-presupuesto-2025) · [La Nación](https://www.nacion.com/el-pais/10-municipalidades-se-reparten-el-27-de-los/3XXFJWZWWNBPLOGTT3GD7YGOBA/story/) | 2025 |
| Recaudación del impuesto a los combustibles | — | ≈ ₡630.000 millones estimados para 2025 | CR · Delfino | 18-sep-2024 |
| **Ley 8488**, art. 45 | Todas las instituciones y **gobiernos locales** deben tener una partida presupuestaria para prevención | — | CR · [Ley 8488](https://www.mep.go.cr/sites/default/files/2026-09/LeyNacionalEmergenciasPrevencionRiesgoN8488.pdf) | vigente |
| Ley 8488, art. 46 / 46 bis | Las instituciones giran a la CNE el 3 % de su superávit; las municipalidades se quedan con ese 3 % para gestión del riesgo | — | misma | vigente |
| Ley 8228, art. 40 (Bomberos) | 4 % de las primas de todos los seguros va al fondo de Bomberos | > ₡44.400 millones en 2024 | CR · [CRHoy](https://www.crhoy.com/aseguradoras-cuestionan-proyecto-que-impondria-nuevas-cargas-a-seguros/) | 2024 |

### 7.2 Quién compra

| Quién | Para qué | Plata disponible | Fuente |
|---|---|---|---|
| **Conavi (MOPT)** | Rutas nacionales: **el vado del río Vainilla está en la Ruta 623** | 8 % de la Ley 10717. Presupuesto 2026: ₡165.562 millones (₡59.870 millones para mantenimiento) | [Diario Extra](https://www.diarioextra.com/noticia/gobierno-recorta-millones-a-mantenimiento-de-carreteras/) |
| **Municipalidades** | Caminos cantonales | 6 % de la Ley 10717, la Ley 8114 y la partida de prevención de la Ley 8488 | ver 7.1 |
| **CNE** | Cuencas vulnerables y emergencias | Fondo Nacional de Emergencias: ₡55.691 millones en 2025. Préstamo del Banco Mundial de US$370 millones que incluye alertas tempranas locales | [Semanario Universidad](https://semanariouniversidad.com/pais/costa-rica-tuvo-que-cuadruplicar-recursos-para-atender-emergencias-en-ultima-decada/) · [Delfino](https://delfino.cr/2024/03/banco-mundial-aprueba-credito-a-costa-rica-por-350-millones-para-infraestructuras-y-servicios-resilientes-al-clima) |
| **Operadores turísticos** | Senderos, cataratas y ríos de sus tours | Pago por sendero | ver 7.3 |
| **Lanamme-UCR** | Inventario nacional de vados | 1 % de la Ley 10717 | Ley 10717 |
| COSEVI | Seguridad vial | Presupuesto de algo más de ₡21.000 millones | [La Nación](https://www.nacion.com/el-pais/cosevi-acumula-117391-millones-en-multas-sin/6FXQYI5BGNF7XAKEFW2FXORRBI/story/) |
| ICT | Turismo seguro | Presupuesto 2026: ₡48.377 millones. En su FODA anota «poco conocimiento sobre la prevención del riesgo» | [ICT, PAO 2026](https://www.ict.go.cr/en/documents/instituto-costarricense-de-turísmo-ict/planificacion/3238-ict-pao-2026/file.html) |

### 7.3 Turismo de aventura: qué exige la norma

| Norma | Qué exige | Fuente | Fecha |
|---|---|---|---|
| **Decreto 39703-S-TUR** | **Plan de emergencias**, manuales de operación y seguridad, pólizas de responsabilidad civil y riesgos del trabajo, **suspender la actividad si hay riesgo** y, en rafting y barranquismo, **«niveles o marcas» del agua por sección**, con un descenso de reconocimiento después de una crecida | [Binasss](https://www.binasss.sa.cr/opac-ms/media/digitales/Turismo%20aventura.pdf) | 6-jun-2016 |
| INTE/ISO 21101:2019 (gestión de seguridad), 21103 y 20611 | Se pueden usar para certificarse; ninguna obliga a monitorear crecidas | [CRHoy](https://crhoy.com/economia/turistas-de-aventuras-cuentan-con-nueva-normativa-de-seguridad/) | 8-ago-2019 |

Lectura nuestra: ninguna norma obliga a tener un sensor. Paso Seguro le da al operador la evidencia de que cumple su plan de emergencias y de que suspende la actividad cuando hay riesgo.

### 7.4 Cómo compra el Estado

| Vía | Dato | Fuente |
|---|---|---|
| Compra pública de innovación | Tiene base en la Ley 9986 (Contratación Pública, art. 22) y en el reglamento 43808-H. Hay una guía de criterios de innovación de 2024. El Decreto 45763 que la reglamenta **no está verificado** | [Guía](https://ricg.org/wp-content/uploads/2025/01/Guia-de-criterios-de-Innovacion.pdf) · [Delfino](https://delfino.cr/2025/05/costa-rica-impulsa-transformacion-del-sistema-de-salud-con-foro-sobre-compra-publica-innovadora) |
| INNOVATECH 2026 (PCII, Fondo PROPYME) | Hasta ₡7.375.000 por proyecto (cubre el 80 %); la convocatoria cerró el 8-jul-2026 | [Delfino](https://delfino.cr/2026/05/pymes-podran-recibir-hasta-73-millones-para-proyectos-de-innovacion-y-desarrollo-tecnologico) |
| Waze for Cities | **Sin costo** para autoridades que administran vías. San José fue uno de sus primeros 10 socios | [Waze](https://www.waze.com/es-419/wazeforcities) |

### 7.5 Cooperación internacional

| Fuente de plata | Monto | Qué cubre | Fuente | Fecha |
|---|---|---|---|---|
| **Banco Mundial, préstamo que ejecuta la CNE** | **US$370 millones** (350 de préstamo + 20 en condiciones blandas) | Infraestructura resiliente y **alertas tempranas locales en cuencas vulnerables** | [Delfino](https://delfino.cr/2024/03/banco-mundial-aprueba-credito-a-costa-rica-por-350-millones-para-infraestructuras-y-servicios-resilientes-al-clima) | 2024 |
| Banco Mundial, Cat DDO II | US$160 millones | Se desembolsa tras una declaratoria de emergencia | [Banco Mundial](https://www.worldbank.org/en/news/press-release/2023/03/22/costa-rica-tendra-acceso-160-millones-dolares-de-banco-mundial-para-reduccion-riesgo-desastres) | 23-mar-2023 |
| BID CR-O0015, préstamo contingente | US$400 millones (en solicitud) | Desastres y emergencias de salud | [GTAI](https://www.gtai.de/de/trade/costa-rica/entwicklungsprojekte/absicherung-von-klima-und-gesundheitsrisiken-in-costa-rica-2006870) | 24-jun-2026 |
| BID PRVC-II, red vial cantonal | US$144 millones (US$92 millones desembolsados) | Caminos cantonales | [BID](https://ewsdata.rightsindevelopment.org/files/documents/85/IADB-CR-T1285.pdf) | 2024 |
| BCIE, PROERI (502 obras) | US$700 millones (concretado el 8,5 % a enero de 2026) | Reconstrucción | Semanario Universidad | ene-2026 |
| Fondo de Adaptación (OMM), Costa Rica y Panamá | US$13,9 millones solicitados (preconcepto) | **Sistemas de alerta temprana** y herramientas de decisión; lo ejecutan el IMN y el ICE | [Fondo de Adaptación](https://adaptation-fund.org/wp-content/uploads/2024/07/WMO_Costa-Rica_Panama_Pre-Concept.pdf) | jul-2024 |
| Fondo Verde del Clima FP174 (Corredor Seco, 7 países) | US$174,3 millones | Sin un componente explícito de alerta temprana | [GCF](https://www.greenclimate.fund/project/fp174) | 2021 |
| JICA BOSAI fase 1 (6 países de Centroamérica) | US$6,06 millones | Gestión de riesgo con la CNE | [JICA](https://www.jica.go.jp/costarica/espanol/activities/PCT_BOSAI.html) | 2007–2012 |
| Japón, Valle de Sula (Honduras) | 247 millones de yenes | Pluviómetros, radares y transmisión de datos | [La Prensa HN](https://www.laprensa.hn/honduras/japon-dona-fondos-mitigar-inundaciones-valle-sula-JI28643578) | 16-dic-2025 |
| SAT comunitarios en Costa Rica | Sarapiquí: piloto de ≈ US$230.000 (2012–2013) · Upala: estación en el río Zapote · Aguas Zarcas: lo maneja la municipalidad · UE (ECHO): más de 20 comunidades | — | [OMM](https://old.wmo.int/extranet/pages/prog/drr/projects/CostaRica/Documents/CostaRicaProject_esp.pdf) · [Teletica](https://www.teletica.com/277606_moderno-sistema-busca-alertar-sobre-inundaciones-en-la-zona-norte) | 2013–2021 |
| CREWS / Early Warnings for All | Nada para Costa Rica. Guatemala lanzó EW4All en marzo de 2024 | — | [UNDRR](https://www.undrr.org/news/guatemala-launches-early-warnings-all-initiative) | 2024 |

---

## 8. Lo técnico: por qué 5G

### 8.1 Las redes públicas se caen o se saturan en los desastres

| Evento | Cifra | Fuente | Fecha |
|---|---|---|---|
| Huracán María, Puerto Rico | 95,6 % de los sitios celulares fuera de servicio (90,3 % cinco días después) | [FCC DIRS](https://docs.fcc.gov/public/attachments/DOC-346860A1.pdf) | 23-sep-2017 |
| Huracán Ian, condado de Lee (Florida) | 259 de 394 sitios caídos (66 %) | [FCC](https://docs.fcc.gov/public/attachments/DOC-387727A1.pdf) | 29-sep-2022 |
| Huracán Helene, Carolina del Norte | 707 de 1.452 sitios caídos (49 %); récord de 4.562 sitios caídos en total | [FCC](https://docs.fcc.gov/public/attachments/DOC-406055A1.pdf) · [Wireless Estimator](https://wirelessestimator.com/articles/2024/unprecedented-outage-no-hurricane-has-knocked-out-more-cell-sites-than-category-4-helene/) | 1-oct-2024 |
| Huracán Milton, Florida | 1.953 de 15.877 sitios caídos (12 %); 1.351 por falta de energía | [Inside Towers](https://insidetowers.com/milton-pummels-floridas-west-coast-cell-sites) | 10-oct-2024 |
| Huracán Otis, Acapulco | 98 de 384 radiobases de Telcel funcionando (≈ 74 % caídas) | [El CEO](https://elceo.com/negocios/telmex-y-telcel-de-carlos-slim-avanzan-en-el-restablecimiento-de-su-servicio-tras-el-paso-del-huracan-otis/) | 26-oct-2023 |
| Sismo del 19S en México | El IFT reconoce que las redes se saturaron por el alza de tráfico de voz y datos | [IFT](https://www.ift.org.mx/sites/default/files/comunicacion-y-medios/comunicados-ift//comunicadoift120reportedesismo220920171.pdf) | 22-sep-2017 |
| **Terremoto de Japón 2011** | **Voz 50–60 veces lo normal; los operadores bloquearon hasta el 90 % (DoCoMo), 95 % (KDDI) y 70 % (SoftBank) de las llamadas** | [MIC Japón, White Paper 2011](https://www.soumu.go.jp/johotsusintokei/whitepaper/eng/WP2011/part1.pdf) | 2011 |
| Inundaciones en el sur de Alemania (GSMA) | voz +275 %, SMS +350 % | [Developing Telecoms](https://developingtelecoms.com/telecom-business/humanitarian-communications/506-text-dont-talk-after-disasters-gsma.html) | 2005 |
| **Costa Rica, tormenta Sara** | **≈ 50.000 clientes del ICE con el móvil o internet degradado**; 135 averías de telecom | [Semanario Universidad](https://semanariouniversidad.com/?p=332316) | 19-nov-2024 |
| Costa Rica, huracán Otto | Un corte de fibra en Pocosol dejó sin teléfono, internet ni móvil a Los Chiles, Upala, Guatuso y otras zonas; más de 20.000 personas afectadas | [Tico Times](https://ticotimes.net/?p=100595) | 24-nov-2016 |
| Costa Rica, tormenta Nate | 47 puntos con fallas de telecom del ICE (89 % por fibra cortada o falla eléctrica); Claro sin internet móvil | [Presidencia](https://presidencia.gobiernocarlosalvarado.cr/comunicados/2017/10/cuadrillas-del-ice-atienden-averias-de-telecomunicaciones-en-47-puntos-del-pais-2/) · [CRHoy](https://crhoy.com/nacionales/tormenta-nate-deja-a-usuarios-de-claro-sin-internet/) | oct-2017 |
| Costa Rica, tormenta Bonnie | 17 averías de telecom; sin voz ni datos en Upala, Los Chiles, Liberia y La Cruz | [El Observador](https://observador.cr/ice-arreglo-12-000-averias-electricas-que-se-produjeron-a-causa-de-la-tormenta-bonnie/) | 3-jul-2022 |
| Averías móviles registradas por la SUTEL en 2025 | kölbi 17.059 · Claro 2.131 · Liberty 2.118; la mayoría por clima o accidentes | [Semanario Universidad](https://semanariouniversidad.com/?p=372940) | 2025 |

### 8.2 Prioridad en redes de misión crítica

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| FirstNet (EE. UU.) | Prioridad y preferencia «siempre activas» y banda 14 dedicada a seguridad pública; la ley de 2012 le asignó US$7.000 millones y 20 MHz | [FirstNet](https://www.firstnet.gov/about) | vigente |
| FirstNet: contrato con AT&T | 25 años; US$6.500 millones federales; AT&T invierte ≈ US$40.000 millones | [NACo](https://www.naco.org/articles/att-wins-public-safety-contract) | 15-abr-2017 |
| FirstNet: conexiones | más de 7 millones | [AT&T](https://www.att.com/es-us/sdabout/story/2025/firstnet-expands-coverage.html) | 31-mar-2025 |
| FirstNet: preempción | Con la red saturada, el tráfico comercial se mueve a otro espectro (las llamadas al 911 no) | [RCR Wireless](https://rcrwireless.com/20171213/carriers/att-launches-preemption-firstnet-customers) | dic-2017 |
| FirstNet en el huracán Irma | prioridad para más de 15.000 rescatistas | [AT&T](https://about.att.com/inside_connections_blog/florida_firstnet) | 2017 |
| FirstNet: núcleo 5G SA con slicing por aplicación | activo desde el 30-jul-2026 | [Tech Times](https://www.techtimes.com/articles/322516/20260731/firstnet-5g-standalone-core-goes-live-per-app-slicing-public-safety-only-infrastructure.htm) | 31-jul-2026 |
| Wireless Priority Service (CISA) | 95 % de llamadas completadas pese a la congestión | [CISA](https://www.cisa.gov/wps) | vigente |
| 3GPP TS 23.501: clases de servicio de misión crítica | 5QI 65 (voz MCPTT, 75 ms) · 5QI 69 (señalización, 60 ms, error de 10⁻⁶) · 5QI 70 (datos, 200 ms) · ARP con 15 niveles y preempción | [3GPP vía itecspec](https://www.itecspec.com/3gpp/23.501/s/5.7.4) | vigente |
| ITU-R M.2410 (requisitos de 5G) | URLLC: 1 ms y 99,999 % de fiabilidad · **mMTC: 1.000.000 de dispositivos por km²** · plano de control de 20 ms | [UIT](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-M.2410-2017-PDF-E.pdf) | nov-2017 |
| Redes móviles privadas en el mundo (GSA) | 2.003 organizaciones en 88 países | [Advanced Television](https://www.advanced-television.com/2026/06/16/data-2003-organisations-now-deploying-private-mobile-networks/) | primer trimestre de 2026 |
| Istres (Francia), seguridad urbana | costo por cámara: €30.000 con fibra contra €5.000 con 5G privada | [Ericsson](https://www.ericsson.com/en/news/2025/6/istres) | 4-jun-2025 |
| Madrid y Orange | primera red privada 5G SA para emergencias de España | [DPL News](https://dplnews.com/espana-ayuntamiento-de-madrid-y-orange-impulsan-la-primera-red-privada-5g-sa-para-emergencias-en-espana/) | feb-2025 |

### 8.3 5G en Costa Rica

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Subasta 5G de la SUTEL | US$34.082.995 en total; fase nacional US$32.519.940 (Claro y Liberty, US$16.259.970 cada uno); 3.104 radiobases comprometidas; bandas de 700 / 2.300 / 3.500 MHz y 26/28 GHz | [SUTEL](https://sutel.go.cr/noticias/comunicados-de-prensa/subasta-regional-de-5g-logro-colocar-frecuencias-en-31-cantones-del) · [El Observador](https://observador.cr/sutel-recauda-32-millones-en-subasta-de-las-bandas-para-internet-5g-acuerdan-instalacion-de-3-104-radiobases/) | 23–24-ene-2025 |
| Fase regional (5 cooperativas y Ring Centrales; 31 cantones) | US$1.563.055 | SUTEL | 24-ene-2025 |
| Claro 5G | más de 1,8 millones de personas cubiertas en 7 provincias | [Delfino](https://delfino.cr/2026/05/cobertura-5g-de-claro-se-expande-en-costa-rica-y-supera-18-millones-de-personas) | 26-may-2026 |
| Liberty 5G | primer 5G comercial (1-jul-2024); sitios 5G SA en Guanacaste, Pacífico Central y Zona Norte | [Ericsson](https://www.ericsson.com/en/press-releases/latin-america/2026/liberty-and-ericsson-enhance-5g-coverage-to-key-regions-and-tourist-communities-in-costa-rica) | 3-mar-2026 |
| Líneas 5G de operadores privados | 1,6 millones; el ICE todavía no vende 5G | [CRHoy](https://crhoy.com/tecnologia/mientras-operadoras-privadas-suman-16-millones-de-lineas-5g-ice-sigue-sin-comercializar-el-servicio/) | 16-abr-2026 |
| Medición de la SUTEL (ene–jun 2026) | Claro 186,6 Mbps contra Liberty 34,1 Mbps; sin señal 5G de Liberty en Cartago, Guanacaste, Puntarenas ni Limón | [DPL News](https://dplnews.com/?p=330040) | 2026 |
| **ICE adjudica a Ericsson su red 5G** | **5G SA con Open RAN y network slicing, ≈ US$220 millones**, al menos 12 meses de construcción | [Ericsson](https://www.ericsson.com/es/press-releases/latin-america/2026/ice-selecciona-a-ericsson-para-desplegar-la-red-5g-de-costa-rica) | 28-abr-2026 |
| Acuerdo ICE–RACSA aprobado por la SUTEL | US$65 millones, ≈ 200 radiobases, hasta 600.000 usuarios | [DPL News](https://dplnews.com/sutel-aprueba-acuerdo-ice-racsa-ofrecer-5g-costa-rica/) | 22-ago-2025 |
| RACSA con Nokia | primera red 5G SA del país (30 sitios iniciales); vende redes privadas como servicio | [BNamericas](https://bnamericas.com/en/news/racsa-launches-costa-ricas-first-5g-network) | 2024 |
| Reforma del Plan Nacional de Atribución de Frecuencias | incluye «redes privadas», D2D y 26 GHz; publicada en La Gaceta el 29-abr-2026. En el borrador, el espectro IMT queda para redes públicas | [MICITT](https://www.micitt.go.cr/el-sector-informa/costa-rica-moderniza-el-plan-nacional-de-atribucion-de-frecuencias-para-impulsar) · [borrador](https://www.micitt.go.cr/sites/default/files/2026-02/Decreto_Ejecutivo_Reforma_Parcial_PNAF_CMR_2023_vFINAL2_Limpio.pdf) | may-2026 |
| Testbed 5G de la PCII (proyecto de la UE) | lanzado en el edificio de la PCII en Coronado | [UE](https://www.eeas.europa.eu/delegations/costa-rica/costa-rica-lanza-su-primer-banco-de-pruebas-testbed-5g-con-cooperaci%C3%B3n-de-la-uni%C3%B3n-europea_und_es) | 24-jun-2025 |
| Hackatón 5G | 46 participantes en 8 equipos; uno de los ejes es «gestión del riesgo» | [Delfino](https://delfino.cr/2026/10/hackaton-reune-en-costa-rica-a-46-participantes-para-desarrollar-soluciones-con-tecnologia-5g) | 7-oct-2026 |

### 8.4 Para el jurado técnico

- **El punto base manda pocos bytes**, y eso también lo lleva 4G o NB-IoT. Un router 4G cuesta US$219, contra US$516–830 uno 5G.
- **El 5G aporta tres cosas:**
  - una porción de red reservada con prioridad durante la tormenta (slicing, 5QI y ARP);
  - muchos sensores río arriba (mMTC);
  - ancho de subida para el módulo cámara.
- **Si la torre se queda sin luz, se cae cualquier red.** Por eso la alarma local funciona sin red, y la probamos así.
- **La red «privada» tendría que montarse sobre un operador.** En el borrador del Plan Nacional de Frecuencias, el espectro 5G queda para redes públicas. Para Paso Seguro sería una porción reservada de RACSA o del ICE, o la red del Testbed.
- **Waze solo sirve para el vado con carros.** El feed CIFS no admite rutas peatonales, exige que todos los carriles estén cerrados y los cierres sin hora de fin vencen a las 2 semanas ([Google](https://developers.google.com/waze/data-feed/road-closure-information?hl=es-419)).

---

## 9. Casos internacionales que funcionaron (Japón, Noruega y otros)

### 9.1 Japón: lo más parecido a Paso Seguro

Después del tifón de 2016, Japón llenó sus ríos de **medidores de nivel baratos** que solo transmiten cuando el agua sube. Es la misma idea que Paso Seguro. «Verificado» quiere decir que el dato está en el texto de la fuente; «resumen» quiere decir que solo lo vimos en el buscador.

**Medidores de nivel de bajo costo para crisis (危機管理型水位計, MLIT)**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Antes del programa | Las prefecturas medían solo unos **3.200 de unos 21.000 ríos**, en unos 5.200 puntos (verificado) | [MLIT, guía](https://www.mlit.go.jp/river/shishin_guideline/kasen/pdf/kikikanri_tebiki.pdf) | dato de dic-2017; guía de mar-2026 |
| Lo que lo disparó | Tifón 10 de 2016 en Iwaizumi: 24 muertos, 9 de ellos en un hogar de ancianos junto al río Omoto, que tenía un solo medidor, aguas abajo (verificado) | misma guía | mar-2026 |
| Requisitos | Menos de 1 millón de yenes por unidad; 5 años sin cambiar batería ni dar mantenimiento (verificado) | misma guía | mar-2026 |
| Cómo funciona | En vigilancia no transmite. Cuando el agua pasa un umbral, cambia solo a medición y transmite cada 10 minutos o menos (verificado). **Es la lógica de Paso Seguro** | misma guía | mar-2026 |
| Meta inicial | unos 5.800 puntos para el año fiscal 2020 (verificado) | [MLIT](https://www.mlit.go.jp/river/shinngikai_blog/suiikansoku/dai03kai/pdf/doc_4a.pdf) | 20-dic-2017 |
| **Instalados** | **unos 9.300** en todo el país (gobierno nacional y prefecturas) (verificado) | MLIT, guía | 2025 |
| **Costo** | **unos 2 millones de yenes instalado, contra unos 20 millones de un medidor tradicional**; comunicación de unos 1.000 yenes al mes; solar y 5 años sin mantenimiento (verificado) | [Prefectura de Kagoshima](https://www.pref.kagoshima.jp/ah06/event/documents/64796_20191202180059-1.pdf) | ~dic-2019 |
| Costo según Miyagi | «1/10 o menos» del tradicional: 1–1,5 millones de yenes por unidad (verificado) | [Prefectura de Miyagi](https://www.pref.miyagi.jp/documents/13688/755329.pdf) | sin fecha |
| **Funcionó en el tifón Hagibis (2019)** | **En Ochi (Kochi), el dato de un medidor barato permitió cerrar un camino municipal 15 minutos antes de que el río llegara al nivel de desborde** (verificado). Es exactamente el CERRADO de Paso Seguro | [MIC, Libro Blanco 2021](https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r03/html/nd135210.html) | 2021 |

**Cámaras simples de río (簡易型河川監視カメラ)**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Precio objetivo | 300.000 yenes o menos la inalámbrica y 100.000 o menos la cableada (verificado) | [MLIT](https://www.mlit.go.jp/river/gijutsu/inovative_project/pdf/ip3_03_1.pdf) | mar-2019 |
| Cantidad en 2023 | unas 5.000 con red celular, de unas 10.000 cámaras de río; 337 se apagaron por indicios de acceso no autorizado (verificado). **La seguridad importa** | [MLIT](https://www.mlit.go.jp/report/press/mizukokudo03_hh_001168.html) | 31-mar-2023 |
| **Cantidad en 2025** | **unas 9.000**, para transmitir con imágenes la «sensación de urgencia» de la crecida (verificado) | [MLIT, guía](https://www.mlit.go.jp/river/shishin_guideline/kasen/pdf/kanigata_tebiki.pdf) | sep-2025 |

**El peligro es el camino: tifón Hagibis 2019**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Muertos o desaparecidos | 88; el 72 % murió por inundación (la proporción más alta desde 1999) y el 58 % al aire libre (verificado) | [Ushiyama y otros, JSNDS](https://www.jsnds.org/ssk/ssk_40_1_081.pdf) | 2021 |
| **Muertes dentro de autos** | **28 personas, el 54 % de las que murieron al aire libre.** Entre 1999 y 2018 esa proporción fue menor al 30 %. 25 de los 28 casos fueron por inundación o por el río; 11 cayeron porque cedió la orilla de un camino junto al río; **24 de los 28 estaban en su zona de todos los días** (verificado) | mismo estudio | 2021 |
| Koga | más de 10.000 personas evacuaron tras una orden de madrugada con sirena (resumen) | [Ciudad de Koga](https://www.city.ibaraki-koga.lg.jp/material/files/group/1/gougai11.pdf) | 2019 |
| Tendencia de largo plazo | Ise-wan 1959: 5.098 muertos; después, decenas a cientos por año (resumen) | [Gabinete, Libro Blanco](https://www.bousai.go.jp/kaigirep/hakusho/r05/honbun/t1_1s_05_01.html) | 2023 |

**Alerta por niveles y 5G local**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| **Nivel de alerta de 5 niveles (警戒レベル)** | se creó tras las lluvias de julio de 2018; el nivel 4 significa «todos evacúan». **Es parecido a LIBRE, CUIDADO y CERRADO** | [Gabinete](https://www.bousai.go.jp/oukyu/hinankankoku/pdf/guideline_kaitei.pdf) | 29-mar-2019 |
| Reforma de 2021 | el nivel 4 pasa a ser una orden de evacuar | [Gabinete](https://www.bousai.go.jp/oukyu/hinanjouhou/r3_hinanjouhou_guideline/pdf/point.pdf) | 20-may-2021 |
| Alerta de inundación al celular | mensaje automático, gratis y sin registro, al llegar a nivel 4 o 5 (resumen) | [MLIT Kanto](https://www.ktr.mlit.go.jp/shimodate/shimodate00244.html) | 5-sep-2016 |
| L-Alert | empezó en jun-2011 y operaba en todas las prefecturas en abr-2019 | MIC, Libro Blanco 2021 | 2021 |
| **5G local en Tochigi (demostración del MIC)** | ríos Uzuma y Nagano; bandas de 4,7 GHz (SA) y 28 GHz (NSA); cámara 4K con IA y video en vivo a los vecinos | [MIC](https://www.soumu.go.jp/main_content/000739017.pdf) | pruebas desde ene-2021 |
| Precisión de la IA en Tochigi | ±3,6 cm según la empresa Araya (en un medio). El PDF del MIC da otra prueba: 13 cm sobre imágenes generadas y 35 cm sobre fotos reales. **Aclarar antes de citar** | [AI Smiley](https://aismiley.co.jp/ai_news/araya-ai-local-5g-river/) | 2021 |

**Para el pitch (Japón)**

1. **De 3.200 ríos medidos a 9.300 sensores baratos.** En 2017 Japón medía unos 3.200 de sus 21.000 ríos; para 2025 había instalado unos 9.300 medidores de bajo costo (MLIT).
2. **Un décimo del costo:** unos 2 millones de yenes contra 20 millones. Solo transmiten cuando el río sube, como Paso Seguro (Kagoshima, MLIT).
3. **El peligro es el camino:** en el tifón Hagibis, el 54 % de los que murieron al aire libre murió dentro de su auto, y 24 de los 28 estaban en su zona de todos los días (Ushiyama y otros, 2021).
4. **CERRADO 15 minutos antes:** en Ochi, un medidor barato permitió cerrar un camino antes de que el río se desbordara (MIC, 2021).
5. **Japón ya usa un semáforo nacional de 5 niveles** desde 2019 (Gabinete).

### 9.2 Noruega

**Alerta de inundaciones de la NVE (varsom.no) y la tormenta Hans**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Niveles de alerta | **amarillo, naranja y rojo**; el rojo es el más alto y casi nunca se emite. Es un semáforo como el nuestro | [Statsforvalteren](https://www.statsforvalteren.no/portal/nyheter/2023/08/flom-og-jordskredfare-pa-rodt-niva-for-store-deler-av-sor-norge/) | ago-2023 |
| Alertas emitidas en 2025 | 70: 60 amarillas, 9 naranjas y 1 roja | [TU](https://www.tu.no/nyhetsstudio/101071) | 2025 |
| Red de medición de la NVE | 351 estaciones de nivel o caudal en ríos no regulados y 184 en regulados (toda la red, no solo la de alerta) | [NVE](https://publikasjoner.nve.no/rapport/2017/rapport2017_63.pdf) | 2016 |
| **Hans: anticipación** | aviso el 4 de agosto, naranja el 5 y **rojo el 6**; la tormenta golpeó entre el 7 y el 9 | [Evaluación Trøndelag](https://prep.statsforvalteren.no/siteassets/sf-trondelag/dokument-fmtl/samfunnssikkerhet-og-beredskap/evaluering-ekstremvaret-hans---knut-bakstad.pdf) | 2023–24 |
| Hans: la alerta que no llegó | **9 de 30 municipios** de Trøndelag no estaban suscritos a las alertas de varsom.no | misma | 2023–24 |
| Hans: evaluación oficial (DSB) | «manejado de forma muy buena»; 43 hallazgos y 34 actores entrevistados | [DSB](https://www.dsb.no/siteassets/rapporter-og-publikasjoner/rapporter/evalueringsrapport_hans.pdf) | sep-2024 |
| Hans: evacuados | unos 1.600 evacuados y 1.200 aislados solo en Innlandet | [Statsforvalteren Innlandet](https://www.statsforvalteren.no/innlandet/samfunnssikkerhet-og-beredskap/krisehandtering-og-samordning/evaluering-etter-uvaret-hans--tidlig-og-god-innsats/) | 2023 |
| Hans: daños | más de 14.000 reclamos y al menos 3.200 millones de NOK pagados por seguros; costo para la sociedad de más de 7.000 millones de NOK | [informe de If](https://www.io.kommune.no/_f/p1/i98b9c4c5-fe61-4a41-b913-ea58753c5ce4/if-ekstremvaerrapporten-2025.pdf) | 2025 |
| Después de Hans | propuesta de 300 millones de NOK para obras de protección y 25 millones para reforzar la alerta | [TU](https://www.tu.no/nyhetsstudio/87826) | presupuesto 2026 |

**Nødnett: la red de emergencias pasa a 5G (argumento de misión crítica)**

| Dato | Cifra | Fuente | Fecha |
|---|---|---|---|
| Red actual (TETRA) | unas 2.100 estaciones base, 86 % del territorio y unos 60.000 usuarios (cifras posiblemente viejas) | [DSB](https://www.statsforvalteren.no/contentassets/469e4eccdc7742759258bb9208e10c44/knut-abrahamsen-dsb---nodnett.pdf) | s/f |
| **Nuevo Nødnett sobre 5G** | el regulador Nkom firmó con **Telenor, Telia y Lyse** para probar Nødnett sobre 5G, con video, sensores e IA | [Altinget](https://www.altinget.no/helse/artikkel/inngaar-historisk-avtale-om-aa-flytte-noednettet-over-paa-5g) | mar-2026 |
| Calendario | primeros usuarios a fines de 2029 y todos migrados a fines de 2031; 100 millones de NOK más, el doble de lo presupuestado | [Gobierno de Noruega](https://www.regjeringen.no/no/aktuelt/foreslar-100-millioner-kroner-for-a-styrke-arbeidet-med-nytt-nodnett/id3159129/) | 2026 |
| Mantener TETRA mientras tanto | contrato con Motorola de 1.780 millones de NOK (2027–2031) | [CFOtech](https://cfotech.co.uk/story/motorola-secures-nok-1-78-billion-contract-in-norway-deal) | dic-2024 |
| **Por qué hace falta prioridad** | según la DSB, «pocas o ninguna» red comercial cumple la cobertura y la robustez de misión crítica; Nkom propone extender la prioridad a datos y redes nuevas | [Nkom](https://nkom.no/aktuelt/prioritet-i-mobilnett-horing-om-endring-i-forskrift/) | s/f |
| Hans y la red móvil | cortes «extensos» de móvil y banda ancha en Innlandet y Buskerud | [Security World Market](https://www.securityworldmarket.com/no/Nyheter/Bedriftsnyheter/ny-rapport-kartlegger-svakheter-i-digital-infrastruktur) | s/f |
| **Por qué se caen las antenas** | más de 9 de cada 10 caídas en clima extremo son por **falta de electricidad** (lo dice el CEO de Telia en una columna; no es una medición independiente) | [TU](https://www.tu.no/artikler/hvis-kraftnettet-ikke-taler-storm-hvordan-skal-det-tale-sabotasje/569648) | 2026 |

**Sensores IoT de nivel en Noruega**

| Caso | Cifra | Fuente | Fecha |
|---|---|---|---|
| Sauda (Rogaland) | 5 sensores ultrasónicos LoRa, 4 bajo puentes; miden 2 veces por minuto y envían cada 30 minutos (no hubo crecida ese año) | [TU](https://www.tu.no/artikler/sensorteknologi-skal-verne-mot-villere-vaer-lokalt/501912) | 8-nov-2020 |
| Statens vegvesen, carretera E6 | sensores de nivel en alcantarillas, sobre la red NB-IoT de Telenor, con alarma por SMS | [Statens vegvesen](https://www.vegvesen.no/om-oss/presse/aktuelt/nasjonalt/nytt-smart-tiltak-mot-varflommen/) | 2020 |
| SINTEF | sensores hidrológicos IoT sobre la red móvil pública, para alerta de deslizamientos | [SINTEF](https://hdl.handle.net/11250/2995850) | 2022 |

### 9.3 Otros casos

| Caso | Cifra | Fuente | Fecha |
|---|---|---|---|
| **Corea del Sur, paso subterráneo de Osong** | **14 muertos y 16 heridos** el 15-jul-2023; desde 2020 se habían prometido barreras automáticas que ahí no se instalaron | [Asia Economy](https://view.asiae.co.kr/en/article/2026071317152096948) | 13-jul-2026 |
| **Corea, la respuesta** | barreras en **512 de 564 pasos**; el cierre ahora se activa con **5 cm de agua en lugar de 15**; en 83 pasos piloto el estado aparece en las apps de navegación. **Es nuestro CERRADO más el aviso a Waze** | misma | 13-jul-2026 |
| **Kerr County, Texas (julio de 2025)** | sin sirenas; un bombero pidió la alerta CodeRED a las 4:22 a. m. y a las 5:11 a. m. todavía no salía; una petición por sirenas juntó cerca de 40.000 firmas | [ABC News 4](https://abcnews4.com/news/nation-world/calls-for-accountability-grow-as-delayed-flood-alert-costs-120-lives-in-texas-kerrville-kerr-county-hunt-fourth-of-july-codered-emergency-alert-system-dispatch-audio-warning-sirens-petition-timeline-governor-greg-abbott-camp-mystic) | 10-jul-2025 |
| Kerr County, un año después | **más de 130 muertos**, 27 en Camp Mystic. Ya hay 6 de 8 sirenas con sensores (de unas 30 previstas por la ley SB3); el mantenimiento cuesta US$700–1.000 por sirena al año | [KSAT](https://www.ksat.com/news/local/2026/07/03/one-year-after-deadly-hill-country-flood-where-recovery-investigations-and-camp-mystic-stand/) | 3-jul-2026 |
| **San Antonio y Bexar County** | **más de 190 sensores en cruces bajos; el estado (seguro, subiendo o cerrado) se manda a Waze** desde diciembre de 2023. Es un precedente directo de Paso Seguro | [KSAT](https://ksat.com/news/local/2023/12/16/san-antonio-river-authority-waze-partnership-brings-real-time-low-water-crossing-data-to-drivers) | 16-dic-2023 |
| Bexar County, la falla | 2 muertos en Graytown Road (2021), donde la barrera había sido retirada por falta de recursos; más de una docena de sensores estaban inactivos. **El mantenimiento importa tanto como la instalación** | [KENS 5](https://kens5.com/article/news/community/flood-barricades-return-to-east-bexar-county-where-two-people-drowned-in-2021/273-c2d424ed-51f2-4965-baa4-7673cc3f8e97) | s/f |
| Austin | 67 cruces bajos monitoreados; al ritmo actual, arreglarlos todos tomaría más de 200 años | [Texas Standard](https://texasstandard.org/stories/austin-low-water-crossings-repairs-flooding-atx-texas/) | jul-2025 |
| EE. UU., «Turn Around Don't Drown» | más de la mitad de los ahogados en inundaciones entraron con un vehículo; 30 cm de agua en movimiento arrastran un auto pequeño y 60 cm, camionetas y SUV | [NWS](https://www.weather.gov/lmk/AdairCountyKYBeginsDeploymentof16NewTurnAroundDontDrownTADDSignsAcrosstheCounty) | s/f |
| **Bangladesh, ciclones** | 1970: entre 300.000 y 1 millón de muertos; 1991: unos 138.000; **ciclón Mocha 2023: 750.000 evacuados y 0 muertos** en Bangladesh; Remal 2024: unos 800.000 evacuados y al menos 10 muertos | [PreventionWeb](https://www.preventionweb.net/quick/10852) · [CBS](https://www.cbsnews.com/news/cyclone-mocha-myanmar-bangladesh-few-deaths-mass-evacuations) · [Al Jazeera](https://www.aljazeera.com/news/2024/5/27/cyclone-remal-slams-into-india-bangladesh-what-we-know) | 2019–2024 |
| Bangladesh, programa de voluntarios | 76.000 voluntarios, la mitad mujeres; las muertes bajaron un 75 % en 25 años | [PreventionWeb](https://www.preventionweb.net/quick/10852) · [TBS](https://www.tbsnews.net/thoughts/50-years-cyclone-preparedness-success-saving-lives-not-livelihood-368398) | 2019–21 |
| Reino Unido, Environment Agency | unas 1,05 millones de propiedades inscritas después de la inscripción automática (57 % de las que están en riesgo; en 2008 era el 14 %) | [Yorkshire Post](https://www.yorkshirepost.co.uk/news/flood-risk-householders-being-signed-up-to-warning-service-1988591) | s/f |
| Reino Unido, tormenta Bert | más de 35.700 propiedades protegidas en una semana; unas 1.375 se inundaron | [GOV.UK](https://www.gov.uk/government/news/the-latest-updates-on-storm-bert) | nov-2024 |
| **OMM: mortalidad** | los países con buena alerta temprana tienen una mortalidad por desastres **8 veces menor**; el secretario general de la ONU dice «al menos 6 veces menor» | [OMM](https://wmo.int/media/news/climate-ambition-summit-un-agencies-and-ifrc-kickstart-major-initiative-towards-realizing-early) · [ONU](https://www.un.org/sg/en/content/sg/statements/2025-10-22/secretary-generals-remarks-the-high-level-event-early-warnings-for-all-the-extraordinary-session-of-the-world-meteorological-congress) | 2023 / 22-oct-2025 |

### 9.4 Lo que enseñan estos casos

1. **Barato y automático funciona.** Japón llegó a 9.300 medidores a un décimo del costo y Corea cierra los pasos solos con 5 cm de agua. Paso Seguro va en la misma línea: sensor barato que decide solo.
2. **El aviso tiene que salir sin esperar a una persona.** En Kerr County la alerta esperó al menos 49 minutos. En Noruega, 9 de 30 municipios no estaban suscritos y no la recibieron. Paso Seguro cierra solo y avisa por varios caminos a la vez: sirena, guía, QR y Waze.
3. **Hay que mandar el estado a la app de navegación.** San Antonio lo manda a Waze desde 2023 y Corea en 83 pasos piloto.
4. **Las antenas se caen por falta de luz.** En Noruega es más de 9 de cada 10 caídas. Por eso la **alarma local funciona sin red** y el punto tiene **energía solar propia**. La prioridad 5G sirve cuando la red está viva pero saturada (Japón 2011); Noruega la está construyendo para su red de emergencias.
5. **El mantenimiento salva vidas.** En Bexar murieron 2 personas donde la barrera había sido retirada y había sensores inactivos. Por eso el precio de Paso Seguro incluye 4 visitas al año.

### 9.5 Para el pitch: las 5 frases más fuertes de los casos

1. «Japón midió el problema: tenía 21.000 ríos y medía 3.200. Hoy tiene 9.300 sensores baratos, a un décimo del costo, que transmiten solo cuando el río sube» (MLIT).
2. «En el tifón Hagibis, uno de cada dos que murieron al aire libre murió dentro de su carro, en su camino de todos los días» (Ushiyama y otros, 2021).
3. «Corea perdió 14 personas en un paso sin barrera. Hoy cierra 512 pasos con 5 cm de agua y lo muestra en el navegador. Eso es Paso Seguro» (Asia Economy, 2026).
4. «En Texas murieron más de 130 personas en un lugar sin sirenas, mientras la alerta esperaba una aprobación» (ABC, KSAT).
5. «La OMM calcula que con alerta temprana se muere 8 veces menos» (OMM).

---

## 9.7 Opción dron en base: DJI Matrice 4TD + Dock 3

Idea: cuando el sensor pasa a CUIDADO, un dron despega solo de su base, vuela río arriba y manda video normal y térmico para confirmar la crecida y ver si hay personas o carros cerca.

| Dato | Cifra | Fuente |
|---|---|---|
| Vuelo | 54 min como máximo; radio de operación de 10 km | [DJI, specs](https://enterprise.dji.com/dock-3/specs) |
| Lluvia y viento | **2 mm/h de lluvia como máximo**; viento de 12 m/s; dron IP55 y base IP56 | specs · [FAQ](https://enterprise.dji.com/dock-3/faq) |
| Cámaras | térmica de 640×512 (1280×1024 en modo UHR), zoom híbrido de 112x, telémetro láser de 1.800 m y luz infrarroja para la noche | specs |
| Carga en la base | 27 min (de 15 a 95 %) | FAQ |
| Enlace | radio O4+ Enterprise; 4G con un accesorio (Cellular Dongle 2). **No trae 5G**; la base se conecta por Ethernet, así que puede salir por un router 5G (DJI recomienda 10 Mbps o más de subida) | specs |
| Integración con nuestro borde | **DJI Cloud API** (MQTT y HTTPS): un sistema propio puede lanzar la misión y recibir el video en vivo (RTMP, WebRTC o Agora) | [DJI Developer](https://developer.dji.com/doc/cloud-api-tutorial/en) |
| Detección de personas con IA | solo lo dice un distribuidor; no hay documento oficial de DJI | [Advexure](https://advexure.com/products/dji-matrice-4td-for-dock-3) |
| Precio del kit Dock 3 + M4TD | **US$23.550–27.308** (con garantía) | [Dronefly](https://www.dronefly.com/products/dji-dock-3-matrice-4td-with-care-enterprise-plus) · [DSLRPros](https://dslrpros.com/collections/shop-dji-dock-series) |
| Software FlightHub 2 | US$3.280 al año en la nube, o €9.882 + €540 al año en servidor propio | [Advexure](https://advexure.com/products/dji-flighthub-2-enterprise) · [Drone Parts Center](https://drone-parts-center.com/en/product/dji-flighthub-2-on-premises-basic-1-device/) |
| Reglas en Costa Rica (DGAC) | máximo 120 m de altura, **solo de día y con buena visibilidad** (de noche hace falta aprobación) y fuera de zonas pobladas. No hay una norma para vuelos fuera de la línea de vista desde una base, así que haría falta un permiso especial | [DGAC, AIC Serie C](https://sub.dgac.go.cr/wp-content/uploads/2026/03/AIC-Serie-C-RPAS-INGL--S.pdf) |
| **El Conavi ya es operador autorizado de drones** | aparece en la lista de la DGAC | [DGAC, rev. 33](https://sub.dgac.go.cr/wp-content/uploads/2025/11/Empresas-autorizadas-operaciones-RPAS-Rev.33-16-10-2025.pdf) |
| Restricciones de EE. UU. | desde dic-2025 no se puede usar plata federal de EE. UU. para comprar DJI o Autel. No encontramos restricciones del Banco Mundial ni del BID | [Akin Gump](https://www.akingump.com/en/insights/alerts/fcc-adds-all-foreign-made-uas-and-uas-critical-components-to-covered-list) · [UC Davis](https://research.ucdavis.edu/new-drone-prohibitions-for-federal-grants/) |
| Alternativas | Skydio X10 con base (EE. UU.): unos US$57.700 la base. Parrot ANAFI UKR con base DBOX (Francia): **5G con doble SIM**. Autel EVO Max 4T con Nest: US$9.000 el dron y US$16.000–20.000 la base | [Adorama](https://www.adorama.com/psdr4kitdokd.html) · [Dronenerds](https://www.dronenerds.com/products/dbox-docking-station-for-parrot-anafi-ukr) · [Autel](https://auteldrones.com/products/evo-max-4t) |
| Casos | Chula Vista (EE. UU.): más de 25.000 llamadas; el dron llegó primero en 17.170, en unos 97 s de promedio. Dock 2 en el mar Báltico: despega en menos de 60 s. Dock 3 en la laguna Palcacocha (Perú), para riesgo de aluvión. Yunnan (China): 56 bases y unos 300 vuelos por día | [DroneXL](https://dronexl.co/2026/05/15/chula-vista-pd-dfr-drone-program-25000/) · [DJI](https://enterprise-insights.dji.com/blog/how-drones-enhance-different-stages-of-a-water-rescue) · [DJI Perú](https://www.mynewsdesk.com/uk/dji/pressreleases/dji-dock-3-enhances-glacier-monitoring-for-avalanches-and-floods-in-the-peruvian-andes-3421736) |

**Tres opciones**

| Opción | Cómo | Lo bueno | Lo malo | Costo |
|---|---|---|---|---|
| 1. Base fija en una zona crítica | El borde dispara la misión por la Cloud API cuando el sensor pasa a CUIDADO | Video y térmica en minutos; busca personas río arriba | **No vuela con lluvia fuerte** (más de 2 mm/h) ni con viento de más de 12 m/s, justo en la tormenta. Pide permiso especial de la DGAC. Si hay fondos de EE. UU., DJI queda fuera | US$24–27 mil + US$3.300 al año |
| 2. Base en un vehículo (CNE, Conavi o Cruz Roja) | Va al vado cuando hay alerta; con un piloto en el sitio | Un equipo para muchos vados; cabe en la regla actual; sirve para rescate | No es automático; hay que esperar el traslado | lo mismo + el vehículo |
| 3. «Listo para dron» | Paso Seguro publica el evento CUIDADO para que un operador autorizado (como el Conavi) vuele con cualquier marca | Barato; no se ata a DJI; no promete vuelos sin piloto | Sin video automático; depende de otro | casi solo el desarrollo |

**Recomendación:** para mañana, la opción 3, con la 1 como piloto de una fase 2. El dron **complementa** al sensor y no lo reemplaza: el sensor funciona con cualquier lluvia y el dron no. **Aporte a la historia del 5G:** el video del dron necesita más subida (10 Mbps o más), justo lo que da el 5G.

## 9.8 LiDAR y radar: qué le suman al proyecto

| Opción | Para qué | Datos | Precio | Fuente |
|---|---|---|---|---|
| **LiDAR puntual Benewake TF02-Pro** | Segunda fuente de nivel, con otra física distinta del ultrasónico; alcanza más allá de 4,5 m | 40 m con un blanco que refleja el 90 % y 13,5 m con uno que refleja el 10 %; ±5 cm hasta 5 m; IP65; haz angosto (no lo engañan las paredes, como al ultrasónico) | US$90–145 | [RobotShop](https://ca.robotshop.com/products/benewake-tf02-pro-lidar-led-rangefinder-ip65-40m) · [GetFPV](https://www.getfpv.com/benewake-tf02-pro-ip65-lidar.html) |
| LiDAR TF02-Pro-W | La versión para medir nivel, con limpiaparabrisas para el lente | hasta 25 m; RS485 | ≈ ₹10.700 (India) | [RobotShop](https://RobotShop.com/products/tf02-pro-w-material-level-detection-lidar-rs485) |
| **Radar de nivel VEGAPULS C 21 (80 GHz)** | El que usan las estaciones de ríos de verdad; para el piloto real | 15–20 m; no le afectan la lluvia, la neblina ni el calor; SDI-12 para equipos con batería | £717 + IVA · €857 + IVA · desde SGD 1.300 | [VEGA](https://www.vega.com/en/products/product-catalog/level/radar/vegapuls-c-21) · [RS](https://uk.rs-online.com/web/p/level-sensors/2067074?gb=s) · [caso en un río](https://www.vega.com/company/blog/2021/vegapuls-c-21-ueberwacht-zuverlaessig-flusspegel?amp=true) |
| **LiDAR 3D Livox Mid-360** | Ver personas y carros que se acercan al vado, de día y de noche, **sin identificar caras** (alternativa a la cámara) | 360°; 70 m con un blanco que refleja el 80 % | ≈ US$1.092 (un solo vendedor, sin stock) | [rcdrone](https://rcdrone.top/products/livox-mid-360-lidar) |
| LiDAR aéreo (dron o avión) | Mapa en 3D del vado y del cauce: fijar bien los umbrales y ayudar al **inventario de vados de la Ley 10717** (Lanamme) | — | — | — |

**El problema del LiDAR sobre agua:** el agua quieta funciona como un espejo. El láser rebota de lado y no vuelve, salvo que apunte casi vertical. En un estudio sobre el Rin, el LiDAR infrarrojo **dejó huecos sin datos a más de 5–7° de inclinación**. El agua clara, además, deja pasar el láser verde ([ISPRS 2020](https://isprs-archives.copernicus.org/articles/XLIII-B1-2020/57/2020/) · [ISPRS 2018](https://isprs-annals.copernicus.org/articles/IV-1/109/2018/)). El agua de una crecida es café y con olas, y suponemos que devuelve mejor la señal, pero hay que probarlo antes de confiar.

**Recomendación:**
1. **El ultrasónico se queda:** es barato y ya funciona.
2. **Sumar un LiDAR puntual (US$130) como segunda fuente**, apuntado derecho hacia abajo. Sube el costo del punto un 6 % y refuerza la frase «dos fuentes».
3. **Radar en el piloto real**, cuando el río tenga más de 4 m de variación o mucha lluvia.
4. **LiDAR 3D como módulo para ver personas sin cámara**; no identifica a nadie.

**¿El LiDAR 3D distingue personas, animales y otras cosas?** Sí, pero solo **qué tipo de cosa es**, no **quién es**. Lo reconoce por la forma, el tamaño y el movimiento:
- **Peatones, vehículos y ciclistas:** hay clasificadores publicados, por ejemplo el de [la U. de Virginia](https://arxiv.org/pdf/1906.11899).
- **Animales que cruzan la vía:** en un piloto con LiDAR al costado de la carretera ([informe para el DOT de EE. UU.](https://rosap.ntl.bts.gov/view/dot/44347/dot_44347_DS1.pdf)).
- **96 % de acierto** al detectar peatones en tráfico real, en un estudio de Fraunhofer ([publicación](https://publica.fraunhofer.de/entities/publication/089a498b-c8db-4c39-b8ef-e623c3c30990)).
- **Privacidad:** el LiDAR solo guarda distancias: sin caras, sin ropa y sin placas ([Blickfeld](https://www.blickfeld.com/blog/3d-lidar-for-gdpr-compliant-security), [Outsight](https://www.outsight.ai/insights/people-analytics-without-personal-data-how-lidar-meets-gdpr/)).
- **Ojo:** con muchos puntos acumulados en el tiempo, la forma de caminar podría identificar a alguien ([patente de Ford](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12449541)). Por eso **guardar solo eventos y conteos, no las nubes de puntos**.
- **Límites:** lejos hay pocos puntos y cuesta separar a una persona de un perro grande. Un animal chico se puede confundir con una rama. La lluvia fuerte y la neblina lo empeoran.
- **El LiDAR puntual (TF02-Pro) no clasifica nada:** solo mide la distancia.

## 9.6 Crecidas en Costa Rica y dónde va el sensor

**Cuánto y qué tan rápido suben los ríos.** Casi no hay cifras medidas. Ninguna fuente pública da una subida del tipo «X metros en Y minutos» para un río pequeño o un vado. La CNE declara alertas por lluvia, suelo saturado y daños, no por metros de nivel.

| Río | Subida o nivel | Velocidad | Evento | Fuente |
|---|---|---|---|---|
| Zapote / «río de Upala» | El agua llegó al pecho de un vecino; hubo gente en los techos en Bijagua | «En 20 minutos cuando mucho, el río creció» | Huracán Otto, 24-nov-2016 | [Semanario Universidad](https://semanariouniversidad.com/pais/rio-upala-sepulto-casas-arranco-vidas-cuestion-minutos/) |
| Cuenca de Upala | unos 300 mm de lluvia en 6 h; crecidas súbitas sobre 74 km² | — | Otto 2016 | [UCR](https://kimuk.conare.ac.cr/Record/KUCR_223719b1dac8330d6cd4fbddfc64c70c) |
| Zapote, estación Canalete del IMN | un sensor bajo un puente mide la distancia hasta el agua (como Paso Seguro); no publica umbrales | aviso de hasta 1 h | 2021 | [Teletica](https://www.teletica.com/amp/nacional/moderno-sistema-busca-alertar-sobre-inundaciones-en-la-zona-norte_277606) |
| Sixaola (río grande, frontera) | 7,2 m en la regla (nivel de alarma); se desborda a los 8 m. Otro registro: 6,1 m en ene-2017 | «en la madrugada» | 2015 / 2017 | [Panamá América](https://www.panamaamerica.com.pa/provincias/autoridades-ticas-y-panamenas-reunidas-se-mantiene-alerta-verde-981531/amp) · CRHoy (resumen) |
| Barú (Pérez Zeledón) | no encontrado | estas crecidas suelen llegar «en menos de un minuto» (descripción general) | 30-ago-2026 | [Tico Times](https://ticotimes.net/2026/08/30/costa-rica-flash-flood-perez-zeledon-hikers-stranded) |
| Sarapiquí | sin metros; más de 330 personas en albergues; el agua subió hacia las 4 a. m. | hasta 85 mm de lluvia en 6 h | jul-2026 | [Tico Times](https://ticotimes.net/2026/07/23/costa-rica-flooding-yellow-alert-saturated-ground) |
| Escondido (Nicaragua, referencia regional) | +6,4 m sobre lo normal | en horas | jul-2022 | [La Prensa NI](https://www.laprensani.com/2022/07/12/nacionales/3019615-nivel-del-rio-escondido-sube-mas-de-seis-metros-por-paso-de-la-onda-tropical-14) |
| Tiempo de concentración de cuencas pequeñas | 9,4–19,5 min en cuencas empinadas; 79 min en una de 3 km² | — | estudios de Panamá (Kirpich) | [MiAmbiente PA](https://documentoesia.miambiente.gob.pa/58199.pdf) |
| Tempisque | sin datos: la estación de caudal de Guardia cerró en 2010 | — | nota de 2016 | [Tico Times](https://ticotimes.net/2016/08/02/tempisque-river-history-of-neglect-threatens-guanacaste-people-and-environment) |

**Conclusión (nuestra lectura, sin una cifra que lo pruebe):**
- **Ríos de vado:** los 4,5 m del sensor alcanzan. El peligro empieza en el primer metro: 30 cm de agua en movimiento arrastran un auto pequeño (NWS).
- **Ríos grandes de llanura**, como el Sixaola: no alcanzan, pero esos ríos no tienen vados. Ahí va el sensor sumergible de 0 a 6 m.
- **El tiempo de reacción** se mide en minutos (los 20 de Upala, 10–20 en cuencas chicas). Por eso conviene un segundo sensor río arriba.

**Dónde va el sensor:**
- **Poste:** de acero galvanizado, con concreto, en la orilla alta y en un tramo recto.
- **Caja, batería, router y panel:** arriba del poste, más de 1 m por encima de la crecida más alta que se conozca (marcas de barro o lo que digan los vecinos).
- **Brazo:** lleva la sonda sobre agua mansa, mirando hacia abajo; a 30 cm o más sobre la crecida máxima y a 4,5 m o menos del fondo seco.
- **Señal:** medirla con un teléfono en el punto exacto, a la altura del poste; si es débil, antena externa en la punta. Si en el valle no hay señal, la sonda le pasa el dato por LoRa (varios km) a una caja en un punto alto con 5G o 4G.
- **Avisar a tiempo:** un sensor río arriba da los minutos de ventaja y otro en el vado confirma. La sirena y la luz van en las dos entradas del vado, entre 50 y 100 m antes del agua.
- **Panel:** mirando al sur, con unos 10–15° de inclinación (Costa Rica está a unos 10° al norte del ecuador).
- **Antes del piloto:** medir qué red llega al río Vainilla, porque Liberty no tiene 5G en Puntarenas (SUTEL, 2026).

**Pedir para tener datos medidos:** al IMN, la serie de la estación Canalete; al ICE, los registros de una estación en un río de montaña.

---

## 10. No encontrado o por verificar

**No encontrado**

- Inventario nacional de vados y conteo de comunidades sin puente.
- La población exacta de Pilas de Canjel (las «~500 personas» sí están en La Nación del 14-sep-2024).
- Muertes por cruzar ríos o vehículos arrastrados como cifra nacional aparte; la Cruz Roja solo da el total de accidentes acuáticos.
- Número de operadores de turismo de aventura con declaratoria del ICT.
- Presupuesto de la CNE para sistemas de alerta temprana y número de sistemas comunitarios instalados.
- Monto del rubro de alerta temprana dentro del préstamo de US$370 millones del Banco Mundial.
- Monto 2026 de la transferencia de la Ley 8114 a las municipalidades.
- Planes IoT o M2M de kölbi, Claro y Liberty (hay que cotizarlos) y planes de Claro.
- Gabinete IP65 de 20×30 cm, paneles de 20–60 W y mini PC N100/N150 en tiendas de Costa Rica.
- Radiobases caídas por operador en Otto, Eta, Iota o Sara (no hay informe de la SUTEL).
- Precio de una red 5G privada pequeña de una fuente independiente.
- Japón: un número de «vidas salvadas» atribuido a los medidores o al nivel de alerta; resultados de los medidores en las lluvias de Kyushu de 2020; latencia medida en las pruebas de 5G local para ríos.
- Noruega: el número de estaciones que usa la alerta de la NVE, el número oficial de muertos por Hans, el costo total del nuevo Nødnett sobre 5G y sensores 5G de nivel de ríos.
- Un estudio independiente con muertes antes y después de las barreras o de «Turn Around Don't Drown» en Texas.
- La hora exacta en que salió la alerta CodeRED y el número final de muertos solo de Kerr County.

**Por verificar**

- El Decreto 45763 de compra pública de innovación (solo lo vimos citado en LinkedIn).
- El texto final del Plan Nacional de Frecuencias publicado el 29-abr-2026 (solo leímos el borrador).
- Los precios del RUTX50 en algunas tiendas, los US$75.000 de TxDOT y el monto de Levelynx (solo los vimos en el buscador).
- Los totales de la Cruz Roja, que no cuadran entre notas: 2023 aparece como 132 o 133, y 2024 como 140 o 143.
