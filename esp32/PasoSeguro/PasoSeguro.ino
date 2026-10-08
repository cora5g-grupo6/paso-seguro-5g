/*
  Paso Seguro 5G · ESP32 del flotador
  Grupo 6 (CORA 5G) · Hackatón Centroamericano de Innovación 5G 2026
  Placa: ESP32 Dev Module (Arduino IDE, paquete "esp32 by Espressif"). No necesita librerías extra.
  Basado en CORA_demo.ino del kit del grupo.

  Qué hace:
  1. Lee el flotador y el sensor de agua cada 200 ms.
  2. Cada segundo manda la lectura al servidor de borde (POST /api/sensor, JSON).
     La respuesta trae el estado que decidió el borde (LIBRE, CUIDADO o CERRADO), que junta
     cámara, flotador y lluvia del IMN. Ese estado es el que muestran las luces.
  3. Si el flotador se activa, pone ROJO y suena al instante, sin esperar al borde.
  4. Si el borde no responde en 5 s (sin Wi-Fi, sin 5G o borde apagado), pasa a MODO LOCAL:
     decide solo con su sensor y su flotador. La luz parpadea para que se note, y el aviso sigue.
  5. Mide la ida y vuelta de cada envío y la manda en el siguiente (rtt_ms): el tablero la muestra.
  6. Página local http://IP-DEL-ESP32/ y /estado (JSON), como en CORA_demo.
  7. Opcional: MQTT en vez de HTTP (USAR_MQTT 1), con un cliente mínimo incluido.

  Luces y zumbador:
    VERDE = LIBRE · AMARILLO = CUIDADO · ROJO + pitido = CERRADO
    Luz parpadeando = MODO LOCAL (sin borde) · pitido rápido = persona en el cruce cerrado

  Conexiones (las del kit CORA):
    Flotador ............ GPIO 14 y GND (cierra a GND cuando el agua lo levanta)
    Sensor de agua (S) .. GPIO 34 · (+) a 3V3 (nunca 5 V) · (-) a GND
    Semáforo LED ........ R a GPIO 25 · Y a GPIO 26 · G a GPIO 33 · GND a GND
    Buzzer (activo) ..... I/O a GPIO 32 · VCC a 3V3 · GND a GND
  El relé (GPIO 13) y el sensor magnético (GPIO 27) son del caso de huéspedes: aquí no se usan.

  Calibrar: abrir el Monitor Serie (115200), anotar "agua=" en seco y con el sensor mojado
  hasta la marca de arriba, y poner esos números en AGUA_SECO y AGUA_LLENO.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#if __has_include(<ESPmDNS.h>)
#include <ESPmDNS.h>
#define HAY_MDNS 1
#endif

// ---------- Red ----------
// El nombre y la clave del Wi-Fi van en secretos.h (copiar secretos.h.example). No se suben al repo.
#if __has_include("secretos.h")
#include "secretos.h"
#else
const char* WIFI_NOMBRE  = "NOMBRE_DE_LA_RED";   // Wi-Fi del CPE 5G (CPxx503e) o del router
const char* WIFI_CLAVE   = "CLAVE_DE_LA_RED";
#endif
const char* BORDE_HOST   = "192.168.1.142";      // IP del borde si no lo encuentra por nombre
const char* BORDE_NOMBRE = "Gordo";              // nombre Bonjour de la laptop-borde (Gordo.local): sigue a la Mac aunque cambie de IP
String bordeIp = BORDE_HOST;
const int   BORDE_PUERTO = 8000;
const char* DISPOSITIVO  = "esp32-flotador-1";

// ---------- MQTT opcional (Mosquitto del borde) ----------
#define USAR_MQTT 0                    // 1 = publica por MQTT y recibe el estado por MQTT
const int   MQTT_PUERTO = 1883;
const char* MQTT_BASE   = "pasoseguro";
const char* CRUCE_ID    = "vado-ruta-623";   // el "id" de config/cruce.json del borde

// ---------- Sensor de nivel ----------
// 1 = ultrasónico RCWL (Trig/Echo) mirando el agua desde arriba; 0 = sensor de agua analógico en PIN_AGUA.
#ifndef USAR_ULTRASONICO
#define USAR_ULTRASONICO 1
#endif
int PIN_TRIG = -1;   // -1 = lo busca solo al arrancar entre los pines de abajo
int PIN_ECHO = -1;
const int PINES_TRIG[] = {2, 4, 5, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33};
const int PINES_ECHO[] = {2, 4, 5, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39};
const int D0_MM   = 800;   // distancia del sensor al agua con el nivel en 0 %
const int D100_MM = 300;   // distancia con el nivel en 100 % (el sensor no ve a menos de ~250 mm)
bool sinEco = false;

// ---------- Pines ----------
int PIN_FLOTADOR  = -1;   // -1 = sin flotador conectado (en esta placa todavía no sabemos el pin)
const int PIN_AGUA      = 34;
int PIN_LED_ROJO  = 25;
int PIN_LED_AMAR  = 26;
int PIN_LED_VERDE = 33;
int PIN_BUZZER    = 32;

// ---------- Ajustes ----------
int AGUA_SECO  = 0;      // lectura del sensor de agua en seco
int AGUA_LLENO = 2000;   // lectura con el sensor mojado hasta la marca de arriba
const int UMBRAL_AMARILLO = 40;   // mismos umbrales que el borde
const int UMBRAL_ROJO     = 70;
const int HISTERESIS      = 10;   // para bajar, el nivel tiene que bajar 10 puntos más
const bool BUZZER_ACTIVO_EN_ALTO   = true;   // si el buzzer suena al revés, poner false
const bool FLOTADOR_CIERRA_EN_BAJO = true;   // si el flotador funciona al revés, poner false
const unsigned long LECTURA_MS      = 200;
const unsigned long ENVIO_MS        = 1000;   // con borde
const unsigned long ENVIO_LOCAL_MS  = 5000;   // sin borde: reintenta más espaciado para no trabar las luces
const unsigned long BORDE_VENCE_MS  = 5000;   // sin respuesta del borde en este tiempo: modo local
const unsigned long BAJADA_LOCAL_MS = 10000;  // modo local: tiempo sostenido para bajar un escalón (demo; en un río real 900000)

enum Estado { LIBRE = 0, CUIDADO = 1, CERRADO = 2 };

WebServer servidor(80);
WiFiClient clienteHttp;

Estado estadoBorde = LIBRE;
Estado estadoLocal = LIBRE;
Estado estadoMostrado = LIBRE;
bool modoLocal = true;
bool hayBorde = false;
bool alarmaPersona = false;
unsigned long ultimoBordeMs = 0;
bool bajando = false;
unsigned long bajadaDesdeMs = 0;
int nivelPct = 0;
int lecturaAgua = 0;
bool flotadorActivo = false;
long rttMs = -1;
unsigned long seq = 0;

const char* nombreEstado(Estado e) {
  if (e == CERRADO) return "CERRADO";
  if (e == CUIDADO) return "CUIDADO";
  return "LIBRE";
}

const char* colorEstado(Estado e) {
  if (e == CERRADO) return "ROJO";
  if (e == CUIDADO) return "AMARILLO";
  return "VERDE";
}

void buzzer(bool encendido) {
  if (PIN_BUZZER < 0) return;
  digitalWrite(PIN_BUZZER, (encendido == BUZZER_ACTIVO_EN_ALTO) ? HIGH : LOW);
}

void escribir(int pin, bool v) {
  if (pin >= 0) digitalWrite(pin, v ? HIGH : LOW);
}

void luces(Estado e, bool encendidas) {
  escribir(PIN_LED_ROJO,  encendidas && e == CERRADO);
  escribir(PIN_LED_AMAR,  encendidas && e == CUIDADO);
  escribir(PIN_LED_VERDE, encendidas && e == LIBRE);
}

#if USAR_ULTRASONICO
long ecoUs(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(4);
  digitalWrite(trig, HIGH);
  delayMicroseconds(20);
  digitalWrite(trig, LOW);
  return pulseIn(echo, HIGH, 30000);
}

// Prueba cada par de pines candidatos hasta que uno devuelve eco. Necesita algo enfrente a más de 30 cm.
bool probarPar(int t, int e) {
  pinMode(e, INPUT);
  pinMode(t, OUTPUT);
  long us = ecoUs(t, e);
  if (us == 0) { delay(30); us = ecoUs(t, e); }
  if (us > 0) {
    PIN_TRIG = t;
    PIN_ECHO = e;
    Serial.printf("Sensor encontrado: Trig=GPIO%d Echo=GPIO%d (%ld us)\n", t, e, us);
    return true;
  }
  pinMode(t, INPUT);
  return false;
}

bool buscarPinesSensor(bool completa) {
  // Primero los pines probables: SCL/SDA de «Especial pins» (22/21), OUTPUTS 16 y 4, y la entrada A0 (GPIO36).
  const int pares[][2] = {{22, 21}, {21, 22}, {16, 4}, {4, 16}, {16, 36}, {22, 36}};
  for (auto& par : pares)
    if (probarPar(par[0], par[1])) return true;
  if (!completa) return false;
  const int nt = sizeof(PINES_TRIG) / sizeof(int), ne = sizeof(PINES_ECHO) / sizeof(int);
  for (int j = 0; j < ne; j++) pinMode(PINES_ECHO[j], INPUT);
  for (int i = 0; i < nt; i++) {
    for (int j = 0; j < ne; j++) {
      int t = PINES_TRIG[i], e = PINES_ECHO[j];
      if (t == e || t == PIN_FLOTADOR || e == PIN_FLOTADOR) continue;
      pinMode(t, OUTPUT);
      long us = ecoUs(t, e);
      if (us == 0) { delay(30); us = ecoUs(t, e); }
      if (us > 0) {
        PIN_TRIG = t;
        PIN_ECHO = e;
        Serial.printf("Sensor encontrado: Trig=GPIO%d Echo=GPIO%d (%ld us)\n", t, e, us);
        int* salidas[] = {&PIN_LED_ROJO, &PIN_LED_AMAR, &PIN_LED_VERDE, &PIN_BUZZER};
        for (int* s : salidas)
          if (*s == t || *s == e) *s = -1;  // ese pin ahora es del sensor: esa luz o el zumbador quedan apagados
        for (int jj = 0; jj < ne; jj++)
          if (PINES_ECHO[jj] != t) pinMode(PINES_ECHO[jj], INPUT);
        pinMode(t, OUTPUT);
        pinMode(e, INPUT);
        return true;
      }
      pinMode(t, INPUT);
      delay(10);
    }
  }
  Serial.println("Sensor ultrasónico: no encontré eco en ningún par de pines. Revisar cables y apuntarlo a algo a más de 30 cm.");
  return false;
}

// Distancia en mm (mediana de 5), o -1 si no hay eco.
int distanciaMm() {
  if (PIN_TRIG < 0) return -1;
  long v[5];
  int k = 0;
  for (int i = 0; i < 5; i++) {
    long us = ecoUs(PIN_TRIG, PIN_ECHO);
    if (us > 0) v[k++] = us;
    delay(12);
  }
  if (k < 3) return -1;
  for (int a = 0; a < k; a++)
    for (int b = a + 1; b < k; b++)
      if (v[b] < v[a]) { long x = v[a]; v[a] = v[b]; v[b] = x; }
  return (int)(v[k / 2] * 0.343 / 2);  // mm, sonido a ~20 °C
}
#endif

void leerSensores() {
#if USAR_ULTRASONICO
  int d = distanciaMm();
  sinEco = d < 0;
  lecturaAgua = d;  // en el JSON va como nivel_raw (mm)
  if (!sinEco) nivelPct = constrain(map(d, D0_MM, D100_MM, 0, 100), 0, 100);
#else
  long suma = 0;
  for (int i = 0; i < 4; i++) suma += analogRead(PIN_AGUA);
  lecturaAgua = suma / 4;
  nivelPct = constrain(map(lecturaAgua, AGUA_SECO, AGUA_LLENO, 0, 100), 0, 100);
#endif
  if (PIN_FLOTADOR < 0) {
    flotadorActivo = false;
  } else {
    int f = digitalRead(PIN_FLOTADOR);
    flotadorActivo = FLOTADOR_CIERRA_EN_BAJO ? (f == LOW) : (f == HIGH);
  }
}

// Misma regla que el borde: sube al cruzar el umbral; para bajar hay que quedar 10 puntos abajo.
Estado objetivoLocal(Estado actual) {
  if (flotadorActivo || nivelPct >= UMBRAL_ROJO) return CERRADO;
  if (sinEco) return actual == CERRADO ? CERRADO : CUIDADO;  // sin datos nunca baja y queda al menos en CUIDADO
  if (actual == CERRADO && nivelPct >= UMBRAL_ROJO - HISTERESIS) return CERRADO;
  if (nivelPct >= UMBRAL_AMARILLO) return CUIDADO;
  if (actual != LIBRE && nivelPct >= UMBRAL_AMARILLO - HISTERESIS) return CUIDADO;
  return LIBRE;
}

// Sube al instante; baja de a un escalón y solo si la mejora se sostiene BAJADA_LOCAL_MS.
void actualizarLocal(unsigned long ahora) {
  Estado objetivo = objetivoLocal(estadoLocal);
  if (objetivo > estadoLocal) {
    estadoLocal = objetivo;
    bajando = false;
  } else if (objetivo < estadoLocal) {
    if (!bajando) {
      bajando = true;
      bajadaDesdeMs = ahora;
    }
    if (ahora - bajadaDesdeMs >= BAJADA_LOCAL_MS) {
      estadoLocal = (Estado)(estadoLocal - 1);
      bajadaDesdeMs = ahora;
    }
  } else {
    bajando = false;
  }
}

String jsonLectura() {
  String j = "{";
  j += "\"id\":\"" + String(DISPOSITIVO) + "\",";
  if (!sinEco) j += "\"nivel_pct\":" + String(nivelPct) + ",";
  j += "\"nivel_raw\":" + String(lecturaAgua) + ",";
  j += "\"flotador\":" + String(flotadorActivo ? "true" : "false") + ",";
  j += "\"semaforo_local\":\"" + String(colorEstado(estadoLocal)) + "\",";
  j += "\"modo\":\"" + String(modoLocal ? "local" : "borde") + "\",";
  j += "\"rssi\":" + String((int)WiFi.RSSI()) + ",";
  j += "\"seq\":" + String(seq) + ",";
  j += "\"uptime_s\":" + String(millis() / 1000);
  if (rttMs >= 0) j += ",\"rtt_ms\":" + String(rttMs);
  j += "}";
  return j;
}

// Busca "clave": valor en un JSON plano (sin librerías). Devuelve el valor sin comillas.
bool valorJson(const String& json, const char* clave, String& valor) {
  String buscada = "\"" + String(clave) + "\"";
  int i = json.indexOf(buscada.c_str());
  if (i < 0) return false;
  i = json.indexOf(':', i + buscada.length());
  if (i < 0) return false;
  i++;
  while (i < (int)json.length() && (json[i] == ' ' || json[i] == '"')) i++;
  int fin = i;
  while (fin < (int)json.length() && json[fin] != '"' && json[fin] != ',' && json[fin] != '}') fin++;
  valor = json.substring(i, fin);
  return true;
}

bool leerRespuestaBorde(const String& json) {
  String estado, persona;
  if (!valorJson(json, "estado", estado)) return false;
  if (estado == "CERRADO") estadoBorde = CERRADO;
  else if (estado == "CUIDADO") estadoBorde = CUIDADO;
  else if (estado == "LIBRE") estadoBorde = LIBRE;
  else return false;
  alarmaPersona = valorJson(json, "alarma_persona", persona) && persona == "true";
  ultimoBordeMs = millis();
  hayBorde = true;
  return true;
}

bool enviarPorHttp() {
  HTTPClient http;
  String url = String("http://") + bordeIp + ":" + String(BORDE_PUERTO) + "/api/sensor";
  http.setConnectTimeout(800);
  http.setTimeout(1500);
  if (!http.begin(clienteHttp, url)) return false;
  http.addHeader("Content-Type", "application/json");
  unsigned long t0 = millis();
  int codigo = http.POST(jsonLectura());
  unsigned long t1 = millis();
  bool ok = false;
  if (codigo == 200) ok = leerRespuestaBorde(http.getString());
  http.end();
  rttMs = ok ? (long)(t1 - t0) : -1;
  return ok;
}

#if USAR_MQTT
// ---------- Cliente MQTT mínimo (MQTT 3.1.1, QoS 0): conectar, publicar, suscribir, ping ----------
WiFiClient clienteMqtt;
unsigned long ultimoIntentoMqtt = 0;
unsigned long ultimoPingMqtt = 0;

int leerByteMqtt(unsigned long esperaMs) {
  unsigned long t0 = millis();
  while (!clienteMqtt.available()) {
    if (millis() - t0 > esperaMs || !clienteMqtt.connected()) return -1;
    delay(1);
  }
  return clienteMqtt.read();
}

void escribirLargo(uint8_t* p, int& n, unsigned long largo) {
  do {
    uint8_t b = largo % 128;
    largo /= 128;
    if (largo > 0) b |= 0x80;
    p[n++] = b;
  } while (largo > 0);
}

void escribirTexto(uint8_t* p, int& n, const char* texto) {
  int largo = strlen(texto);
  p[n++] = largo >> 8;
  p[n++] = largo & 0xFF;
  memcpy(p + n, texto, largo);
  n += largo;
}

bool conectarMqtt() {
  if (!clienteMqtt.connect(bordeIp.c_str(), MQTT_PUERTO, 800)) return false;  // espera corta: las luces no se traban
  uint8_t p[160];
  int n = 0;
  p[n++] = 0x10;  // CONNECT
  escribirLargo(p, n, 10 + 2 + strlen(DISPOSITIVO));
  const uint8_t cabecera[] = {0x00, 0x04, 'M', 'Q', 'T', 'T', 0x04, 0x02, 0x00, 30};  // v3.1.1, sesión limpia, 30 s
  memcpy(p + n, cabecera, sizeof(cabecera));
  n += sizeof(cabecera);
  escribirTexto(p, n, DISPOSITIVO);
  clienteMqtt.write(p, n);
  if (leerByteMqtt(1000) != 0x20 || leerByteMqtt(300) != 2) { clienteMqtt.stop(); return false; }
  leerByteMqtt(500);
  if (leerByteMqtt(500) != 0) { clienteMqtt.stop(); return false; }  // CONNACK con código 0 = aceptado
  String tema = String(MQTT_BASE) + "/" + CRUCE_ID + "/estado";
  n = 0;
  p[n++] = 0x82;  // SUBSCRIBE
  escribirLargo(p, n, 2 + 2 + tema.length() + 1);
  p[n++] = 0x00;
  p[n++] = 0x01;  // id del paquete
  escribirTexto(p, n, tema.c_str());
  p[n++] = 0x00;  // QoS 0
  clienteMqtt.write(p, n);
  ultimoPingMqtt = millis();
  Serial.println("MQTT conectado");
  return true;
}

void publicarMqtt() {
  String tema = String(MQTT_BASE) + "/" + DISPOSITIVO + "/sensor";
  String cuerpo = jsonLectura();
  uint8_t p[8];
  int n = 0;
  p[n++] = 0x30;  // PUBLISH QoS 0
  escribirLargo(p, n, 2 + tema.length() + cuerpo.length());
  p[n++] = tema.length() >> 8;
  p[n++] = tema.length() & 0xFF;
  clienteMqtt.write(p, n);
  clienteMqtt.write((const uint8_t*)tema.c_str(), tema.length());
  clienteMqtt.write((const uint8_t*)cuerpo.c_str(), cuerpo.length());
}

void leerMqtt() {
  while (clienteMqtt.connected() && clienteMqtt.available()) {
    int tipo = leerByteMqtt(100);
    if (tipo < 0) return;
    unsigned long largo = 0, mult = 1;
    int b;
    do {
      b = leerByteMqtt(200);
      if (b < 0) return;
      largo += (b & 0x7F) * mult;
      mult *= 128;
    } while ((b & 0x80) && mult <= 128UL * 128 * 128);
    String datos;
    for (unsigned long k = 0; k < largo; k++) {
      int c = leerByteMqtt(200);
      if (c < 0) return;
      if (datos.length() < 600) datos += (char)c;
    }
    if ((tipo & 0xF0) == 0x30 && datos.length() > 2) {  // PUBLISH: tema y luego el JSON
      int largoTema = ((uint8_t)datos[0] << 8) | (uint8_t)datos[1];
      leerRespuestaBorde(datos.substring(2 + largoTema));
    }
  }
}

void cicloMqtt(unsigned long ahora) {
  if (!clienteMqtt.connected()) {
    if (ahora - ultimoIntentoMqtt > 5000) {
      ultimoIntentoMqtt = ahora;
      conectarMqtt();
    }
    return;
  }
  publicarMqtt();
  if (ahora - ultimoPingMqtt > 15000) {
    const uint8_t ping[] = {0xC0, 0x00};
    clienteMqtt.write(ping, 2);
    ultimoPingMqtt = ahora;
  }
}
#endif

void aplicarSalidas(unsigned long ahora) {
  bool encendidas = modoLocal ? ((ahora / 500) % 2 == 0) : true;  // en modo local la luz parpadea
  luces(estadoMostrado, encendidas);
  bool sonido = false;
  if (alarmaPersona && !modoLocal && estadoMostrado != LIBRE) sonido = (ahora / 120) % 2 == 0;  // pitido rápido
  else if (estadoMostrado == CERRADO) sonido = (ahora % 1000) < 250;                           // pitido intermitente
  buzzer(sonido);
}

String jsonEstado() {
  String j = jsonLectura();
  j.remove(j.length() - 1);
  j += ",\"estado\":\"" + String(nombreEstado(estadoMostrado)) + "\"";
  j += ",\"estado_borde\":\"" + String(nombreEstado(estadoBorde)) + "\"";
  j += ",\"borde_ok\":" + String(modoLocal ? "false" : "true");
  j += "}";
  return j;
}

void paginaPrincipal() {
  String fondo = estadoMostrado == CERRADO ? "#c0392b" : (estadoMostrado == CUIDADO ? "#f1c40f" : "#1d6c3a");
  String letra = estadoMostrado == CUIDADO ? "#123249" : "#ffffff";
  String h = "<!doctype html><html lang='es'><head><meta charset='utf-8'>";
  h += "<meta name='viewport' content='width=device-width,initial-scale=1'>";
  h += "<meta http-equiv='refresh' content='1'><title>Paso Seguro · ESP32</title></head>";
  h += "<body style='margin:0;font-family:sans-serif;background:" + fondo + ";color:" + letra + ";text-align:center'>";
  h += "<h1 style='font-size:64px;margin:40px 0 10px'>" + String(nombreEstado(estadoMostrado)) + "</h1>";
  h += "<p style='font-size:24px'>Nivel del sensor: " + String(nivelPct) + " % · Flotador: " + String(flotadorActivo ? "ACTIVADO" : "normal") + "</p>";
  h += "<p style='font-size:20px'>" + String(modoLocal ? "MODO LOCAL: sin respuesta del borde" : "Conectado al borde") + "</p>";
  if (rttMs >= 0) h += "<p style='font-size:18px'>Ida y vuelta al borde: " + String(rttMs) + " ms</p>";
  h += "<p style='font-size:14px;opacity:.75'>Paso Seguro 5G · Grupo 6 · el aviso local funciona aunque no haya red</p>";
  h += "</body></html>";
  servidor.send(200, "text/html; charset=utf-8", h);
}

void paginaEstado() {
  servidor.sendHeader("Access-Control-Allow-Origin", "*");
  servidor.send(200, "application/json", jsonEstado());
}

void setup() {
  Serial.begin(115200);
  if (PIN_FLOTADOR >= 0) pinMode(PIN_FLOTADOR, INPUT_PULLUP);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_LED_AMAR, OUTPUT);
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  buzzer(false);
#if USAR_ULTRASONICO
  if (PIN_TRIG < 0) buscarPinesSensor(true);
  else { pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_ECHO, INPUT); }
#endif
  for (int e = 0; e < 3; e++) {  // prueba de luces al arrancar
    luces((Estado)e, true);
    delay(250);
  }

  // El Wi-Fi conecta en segundo plano: el aviso local arranca ya, sin esperar a la red.
  WiFi.mode(WIFI_STA);
  int redes = WiFi.scanNetworks();  // lista las redes a la vista: sirve para copiar el nombre exacto
  Serial.printf("Redes Wi-Fi a la vista: %d\n", redes);
  for (int i = 0; i < redes; i++) Serial.printf("  [%s] %d dBm\n", WiFi.SSID(i).c_str(), WiFi.RSSI(i));
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_NOMBRE, WIFI_CLAVE);
  Serial.println("Conectando al Wi-Fi en segundo plano. Mientras tanto: modo local.");

  servidor.on("/", paginaPrincipal);
  servidor.on("/estado", paginaEstado);
  servidor.begin();
  leerSensores();
  estadoLocal = objetivoLocal(LIBRE);
}

void loop() {
  servidor.handleClient();
  unsigned long ahora = millis();
  static unsigned long ultimaLectura = 0, ultimoEnvio = 0, ultimoWifi = 0, ultimoRegistro = 0;

#if USAR_ULTRASONICO
  static unsigned long ultimaBusqueda = 0;
  if (PIN_TRIG < 0 && ahora - ultimaBusqueda > 10000) {  // sin sensor: prueba los pines de siempre cada 10 s
    ultimaBusqueda = ahora;
    static int vueltas = 0;
    buscarPinesSensor(++vueltas % 12 == 0);  // la búsqueda completa (~20 s) solo cada 2 min
  }
#endif
  if (ahora - ultimaLectura >= LECTURA_MS) {
    ultimaLectura = ahora;
    leerSensores();
    actualizarLocal(ahora);
  }

  // Busca la IP del borde por su nombre (Gordo.local) al conectar y cada 30 s mientras no conteste.
  static unsigned long ultimaBusquedaBorde = 0;
  static bool mdnsListo = false;
  if (WiFi.status() == WL_CONNECTED && (!hayBorde || modoLocal) && (ultimaBusquedaBorde == 0 || ahora - ultimaBusquedaBorde > 30000)) {
    ultimaBusquedaBorde = ahora;
#ifdef HAY_MDNS
    if (!mdnsListo) mdnsListo = MDNS.begin(DISPOSITIVO);
    IPAddress ip = mdnsListo ? MDNS.queryHost(BORDE_NOMBRE, 1500) : IPAddress();
    if (ip != IPAddress() && ip.toString() != bordeIp) {
      bordeIp = ip.toString();
      Serial.println("Borde encontrado por nombre: " + String(BORDE_NOMBRE) + ".local = " + bordeIp);
    }
#endif
  }
  static bool wifiAvisado = false;
  if (WiFi.status() == WL_CONNECTED && !wifiAvisado) {
    wifiAvisado = true;
    Serial.println("Wi-Fi listo. Página local: http://" + WiFi.localIP().toString());
    Serial.println("Borde: http://" + bordeIp + ":" + String(BORDE_PUERTO));
  }
  if (WiFi.status() != WL_CONNECTED) {
    wifiAvisado = false;
    if (ahora - ultimoWifi > 10000) {
      ultimoWifi = ahora;
      WiFi.reconnect();
    }
  }

  if (WiFi.status() == WL_CONNECTED && ahora - ultimoEnvio >= (modoLocal ? ENVIO_LOCAL_MS : ENVIO_MS)) {
    ultimoEnvio = ahora;
    buzzer(false);  // si el envío tarda, que el zumbador no quede pegado
#if USAR_MQTT
    cicloMqtt(ahora);
#else
    enviarPorHttp();
#endif
    seq++;
  }
#if USAR_MQTT
  leerMqtt();
#endif

  ahora = millis();
  modoLocal = !hayBorde || (ahora - ultimoBordeMs > BORDE_VENCE_MS);
  Estado nuevo = modoLocal ? estadoLocal : estadoBorde;
  if (flotadorActivo) nuevo = CERRADO;  // el flotador manda siempre
  if (nuevo != estadoMostrado) {
    Serial.println(String("Cambio: ") + nombreEstado(estadoMostrado) + " -> " + nombreEstado(nuevo) +
                   (modoLocal ? " (modo local)" : " (decidido en el borde)"));
  }
  estadoMostrado = nuevo;
  aplicarSalidas(ahora);

  // Para calibrar y para ver la red: mirar estos números en el Monitor Serie (115200)
  if (ahora - ultimoRegistro >= 2000) {
    ultimoRegistro = ahora;
    Serial.printf("agua=%d nivel=%d%% flotador=%d local=%s borde=%s modo=%s rtt=%ld ms\n",
                  lecturaAgua, nivelPct, flotadorActivo, nombreEstado(estadoLocal), nombreEstado(estadoBorde),
                  modoLocal ? "LOCAL" : "borde", rttMs);
  }
}
