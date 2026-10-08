/*
  Paso Seguro 5G · Arduino UNO + Ethernet Shield (W5100)

  Mide el nivel del agua con un sensor ultrasónico impermeable y se lo manda al servidor de borde
  una vez por segundo, por cable, a través del CPE 5G. Prende el semáforo con el estado que le
  responde el borde. Si el borde no contesta en 5 s, pasa a modo local: decide solo con su nivel
  y el flotador, y las luces parpadean para que se note.

  Conexiones (el UNO trabaja a 5 V: el sensor va directo, sin convertidor de nivel)
    Sensor ultrasónico: VCC a 5V, GND a GND, TRIG a D7, ECHO a D8
    Flotador (opcional): entre D2 y GND (cerrado = agua arriba)
    Semáforo: verde D3, amarillo D5, rojo D6 (con resistencia, o el módulo semáforo)
    Zumbador activo: D9
    TMP36 (opcional, corrige la velocidad del sonido): Vout a A0 y USAR_TMP36 en 1
    El Ethernet Shield ocupa D4 (tarjeta SD) y D10 a D13 (SPI): no usarlos.
  Red: cable del shield a un puerto LAN del CPE 5G, la misma red que el borde. IP por DHCP.
  Monitor serie: 115200.
*/
#include <SPI.h>
#include <Ethernet.h>

// ============================== CONFIGURACIÓN ==============================
byte MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0x56, 0x01};  // si el shield trae etiqueta con su MAC, usar esa
IPAddress IP_FIJA(192, 168, 1, 240);                    // solo si el CPE no da IP por DHCP
IPAddress PUERTA(192, 168, 1, 1);
IPAddress BORDE_IP(192, 168, 1, 251);                  // IP del borde: la muestra tools/prueba_conectividad.sh
const uint16_t BORDE_PUERTO = 8000;
const char ID_EQUIPO[] = "uno-5g";

// Calibración: distancia de la sonda al agua con el nivel en 0 % y en 100 %.
// El 100 % tiene que quedar a más de 250 mm de la sonda (zona ciega del sensor).
const long D0_MM = 800;
const long D100_MM = 300;
#define USAR_TMP36 0  // 1 si hay un TMP36 en A0

// Modo local: los mismos umbrales del borde
const float UMBRAL_CUIDADO = 40.0;
const float UMBRAL_CERRADO = 70.0;
const unsigned long BAJADA_LOCAL_MS = 10000;  // demo; en un río real, varios minutos
const unsigned long CADA_MS = 1000;
const unsigned long BORDE_VENCE_MS = 5000;
const unsigned long ESPERA_RESPUESTA_MS = 800;
const unsigned long REINTENTO_DHCP_MS = 60000;

const int PIN_TRIG = 7, PIN_ECHO = 8, PIN_FLOTADOR = 2;
const int PIN_VERDE = 3, PIN_AMARILLO = 5, PIN_ROJO = 6, PIN_ZUMBADOR = 9;
const int PIN_TMP36 = A0;
// ============================================================================

enum Estado { LIBRE, CUIDADO, CERRADO };

EthernetClient cliente;
bool hayRed = false;
bool modoLocal = true;
bool alarmaPersona = false;
bool bajando = false;
Estado estadoBorde = LIBRE, estadoMostrado = CUIDADO, estadoLocalActual = LIBRE;
unsigned long tUltimoBorde = 0, tUltimoCiclo = 0, tUltimoDhcp = 0, tBaja = 0;
long rttMs = -1, seq = 0, mmActual = -1;
int ultimoCodigo = -1;
float nivelActual = -1;
bool flotadorActual = false;

const char* nombre(Estado e) { return e == CERRADO ? "CERRADO" : (e == CUIDADO ? "CUIDADO" : "LIBRE"); }

float velocidadSonidoMmUs(float tempC) { return (331.3 + 0.606 * tempC) / 1000.0; }  // mm por microsegundo

float temperaturaC() {
#if USAR_TMP36
  float t = (analogRead(PIN_TMP36) * 5.0 / 1024.0 - 0.5) * 100.0;
  if (t > -10 && t < 60) return t;
#endif
  return 20.0;
}

long medirUnaVez(float tempC) {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(20);  // los sensores impermeables piden un pulso más largo que el HC-SR04
  digitalWrite(PIN_TRIG, LOW);
  unsigned long us = pulseIn(PIN_ECHO, HIGH, 30000UL);  // 30 ms: unos 5 m
  if (us == 0) return -1;
  return (long)(us * velocidadSonidoMmUs(tempC) / 2.0 + 0.5);
}

// Mediana de 5 disparos: un eco suelto (una gota, una hoja) no mueve el nivel
long distanciaMm(float tempC) {
  long v[5];
  int n = 0;
  for (int i = 0; i < 5; i++) {
    long d = medirUnaVez(tempC);
    if (d > 0) v[n++] = d;
    delay(30);  // el sensor necesita un respiro entre disparos
  }
  if (n < 3) return -1;  // con menos de 3 ecos buenos no se confía
  for (int i = 1; i < n; i++) {
    long x = v[i];
    int j = i - 1;
    while (j >= 0 && v[j] > x) {
      v[j + 1] = v[j];
      j--;
    }
    v[j + 1] = x;
  }
  return v[n / 2];
}

float nivelDesdeMm(long mm) {
  if (mm <= 0) return -1;
  float p = (float)(D0_MM - mm) * 100.0 / (float)(D0_MM - D100_MM);
  return constrain(p, 0.0, 110.0);
}

bool flotadorActivo() { return digitalRead(PIN_FLOTADOR) == LOW; }  // cerrado contra GND

void armarJson(char* buf, size_t n, float nivel, long mm, bool flotador, long rtt) {
  IPAddress ip = Ethernet.localIP();
  int k = snprintf(buf, n, "{\"id\":\"%s\",\"seq\":%ld,\"uptime_s\":%lu,\"modo\":\"%s\",\"ip\":\"%u.%u.%u.%u\",\"flotador\":%s",
                   ID_EQUIPO, seq, millis() / 1000UL, modoLocal ? "local" : "borde", (unsigned)ip[0],
                   (unsigned)ip[1], (unsigned)ip[2], (unsigned)ip[3], flotador ? "true" : "false");
  if (nivel >= 0 && k > 0 && k < (int)n) {
    char num[10];
    dtostrf(nivel, 1, 1, num);  // el UNO no imprime %f: con %f saldría un «?»
    k += snprintf(buf + k, n - k, ",\"nivel_pct\":%s,\"nivel_raw\":%ld", num, mm);
  }
  if (rtt >= 0 && k > 0 && k < (int)n) k += snprintf(buf + k, n - k, ",\"rtt_ms\":%ld", rtt);
  if (k > 0 && k < (int)n) snprintf(buf + k, n - k, "}");
}

// POST /api/sensor. Devuelve el código HTTP (-1 si no conecta) y deja el cuerpo de la respuesta.
int enviarAlBorde(const char* json, char* cuerpo, size_t n) {
  cuerpo[0] = '\0';
  if (!cliente.connect(BORDE_IP, BORDE_PUERTO)) return -1;
  char host[24];
  snprintf(host, sizeof host, "%u.%u.%u.%u:%u", (unsigned)BORDE_IP[0], (unsigned)BORDE_IP[1],
           (unsigned)BORDE_IP[2], (unsigned)BORDE_IP[3], (unsigned)BORDE_PUERTO);
  cliente.print(F("POST /api/sensor HTTP/1.1\r\nHost: "));
  cliente.print(host);
  cliente.print(F("\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: "));
  cliente.print((int)strlen(json));
  cliente.print(F("\r\n\r\n"));
  cliente.print(json);

  unsigned long t0 = millis();
  int codigo = -1, nl = 0, saltos = 0;
  char linea[16];
  bool enCuerpo = false;
  size_t k = 0;
  while (millis() - t0 < ESPERA_RESPUESTA_MS) {
    if (!cliente.available()) {
      if (!cliente.connected()) break;
      delay(1);
      continue;
    }
    int c = cliente.read();
    if (c < 0) break;
    if (codigo < 0) {  // primera línea: "HTTP/1.1 200 OK"
      if (c == '\n') {
        linea[nl] = '\0';
        codigo = nl > 9 ? atoi(linea + 9) : 0;
      } else if (nl < 15) {
        linea[nl++] = (char)c;
      }
      continue;
    }
    if (!enCuerpo) {  // los encabezados terminan en una línea vacía
      saltos = (c == '\n') ? saltos + 1 : (c == '\r' ? saltos : 0);
      enCuerpo = saltos == 2;
      continue;
    }
    if (k < n - 1) cuerpo[k++] = (char)c;
  }
  cuerpo[k] = '\0';
  cliente.stop();
  return codigo;
}

bool procesarRespuesta(const char* cuerpo) {
  const char* p = strstr(cuerpo, "\"estado\":\"");
  if (!p) return false;
  p += 10;
  if (strncmp(p, "CERRADO", 7) == 0) estadoBorde = CERRADO;
  else if (strncmp(p, "CUIDADO", 7) == 0) estadoBorde = CUIDADO;
  else if (strncmp(p, "LIBRE", 5) == 0) estadoBorde = LIBRE;
  else return false;
  alarmaPersona = strstr(cuerpo, "\"alarma_persona\":true") != NULL;
  return true;
}

// Modo local: sube al instante; para bajar, de a un escalón y con el nivel bajo durante BAJADA_LOCAL_MS
Estado estadoLocal(float nivel, bool flotador, unsigned long ahora) {
  Estado objetivo = LIBRE;
  if (flotador || nivel >= UMBRAL_CERRADO) objetivo = CERRADO;
  else if (nivel < 0) objetivo = estadoLocalActual > CUIDADO ? estadoLocalActual : CUIDADO;  // sin dato: no baja
  else if (nivel >= UMBRAL_CUIDADO) objetivo = CUIDADO;
  if (objetivo > estadoLocalActual) {
    estadoLocalActual = objetivo;
    bajando = false;
  } else if (objetivo < estadoLocalActual) {
    if (!bajando) {
      bajando = true;
      tBaja = ahora;
    } else if (ahora - tBaja >= BAJADA_LOCAL_MS) {
      estadoLocalActual = (Estado)(estadoLocalActual - 1);
      tBaja = ahora;
    }
  } else {
    bajando = false;
  }
  return estadoLocalActual;
}

void luces(Estado e, bool encendidas) {
  digitalWrite(PIN_VERDE, encendidas && e == LIBRE ? HIGH : LOW);
  digitalWrite(PIN_AMARILLO, encendidas && e == CUIDADO ? HIGH : LOW);
  digitalWrite(PIN_ROJO, encendidas && e == CERRADO ? HIGH : LOW);
}

void actualizarSalidas(unsigned long ahora) {
  luces(estadoMostrado, !modoLocal || (ahora / 500) % 2 == 0);  // en modo local, parpadean
  bool sonido = false;
  if (alarmaPersona && !modoLocal && estadoMostrado != LIBRE) sonido = (ahora / 120) % 2 == 0;  // pitido rápido
  else if (estadoMostrado == CERRADO) sonido = (ahora % 1000) < 250;                            // intermitente
  digitalWrite(PIN_ZUMBADOR, sonido ? HIGH : LOW);
}

void reportar() {
  Serial.print(F("d="));
  Serial.print(mmActual);
  Serial.print(F(" mm  nivel="));
  if (nivelActual >= 0) Serial.print(nivelActual, 1);
  else Serial.print(F("sin eco"));
  Serial.print(F(" %  flotador="));
  Serial.print(flotadorActual ? F("si") : F("no"));
  Serial.print(modoLocal ? F("  -> sin borde, modo local: ") : F("  -> borde: "));
  Serial.print(nombre(estadoMostrado));
  if (!modoLocal) {
    Serial.print(F(" (ida y vuelta "));
    Serial.print(rttMs);
    Serial.print(F(" ms)"));
  }
  Serial.println();
}

void ciclo() {
  mmActual = distanciaMm(temperaturaC());
  nivelActual = nivelDesdeMm(mmActual);
  flotadorActual = flotadorActivo();
  char json[200], cuerpo[160];
  seq++;
  armarJson(json, sizeof json, nivelActual, mmActual, flotadorActual, rttMs);
  ultimoCodigo = -1;
  if (hayRed) {
    unsigned long t0 = millis();
    ultimoCodigo = enviarAlBorde(json, cuerpo, sizeof cuerpo);
    if (ultimoCodigo == 200 && procesarRespuesta(cuerpo)) {
      rttMs = (long)(millis() - t0);
      tUltimoBorde = millis();
      modoLocal = false;
    }
  }
  unsigned long ahora = millis();
  Estado local = estadoLocal(nivelActual, flotadorActual, ahora);
  if (!hayRed || ahora - tUltimoBorde > BORDE_VENCE_MS) modoLocal = true;
  estadoMostrado = modoLocal ? local : estadoBorde;
  if (flotadorActual) estadoMostrado = CERRADO;  // el flotador manda siempre
  reportar();
}

void conectarRed(unsigned long esperaMs) {
  Serial.println(F("Pidiendo IP por DHCP..."));
  hayRed = Ethernet.begin(MAC, esperaMs, 4000) == 1;
  tUltimoDhcp = millis();
  if (!hayRed) {
    if (Ethernet.hardwareStatus() == EthernetNoHardware)
      Serial.println(F("Sin IP: la placa no ve el shield de red. Revisar que este bien encajado."));
    else {
      // Sin DHCP: prueba con IP fija en la red del CPE. Si el borde contesta, sigue así.
      Ethernet.begin(MAC, IP_FIJA, PUERTA, PUERTA, IPAddress(255, 255, 255, 0));
      hayRed = true;
      Serial.println(F("Sin DHCP: uso la IP fija 192.168.1.240 (si el borde no contesta, revisar cable y puerto LAN)."));
    }
    if (!hayRed) return;
  }
  Ethernet.setRetransmissionTimeout(200);  // si el borde no está, el intento no traba el semáforo
  Ethernet.setRetransmissionCount(3);
  IPAddress ip = Ethernet.localIP();
  char txt[56];
  snprintf(txt, sizeof txt, "IP %u.%u.%u.%u -> borde %u.%u.%u.%u:%u", (unsigned)ip[0], (unsigned)ip[1],
           (unsigned)ip[2], (unsigned)ip[3], (unsigned)BORDE_IP[0], (unsigned)BORDE_IP[1],
           (unsigned)BORDE_IP[2], (unsigned)BORDE_IP[3], (unsigned)BORDE_PUERTO);
  Serial.println(txt);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  digitalWrite(PIN_TRIG, LOW);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_FLOTADOR, INPUT_PULLUP);
  pinMode(PIN_VERDE, OUTPUT);
  pinMode(PIN_AMARILLO, OUTPUT);
  pinMode(PIN_ROJO, OUTPUT);
  pinMode(PIN_ZUMBADOR, OUTPUT);
  luces(CUIDADO, true);  // amarillo mientras arranca
  Serial.println(F("Paso Seguro 5G · Arduino UNO"));
  conectarRed(10000);
}

void loop() {
  unsigned long ahora = millis();
  if (hayRed) {
    Ethernet.maintain();
  } else if (ahora - tUltimoDhcp > REINTENTO_DHCP_MS) {
    actualizarSalidas(ahora);
    conectarRed(5000);
  }
  if (ahora - tUltimoCiclo >= CADA_MS) {
    tUltimoCiclo = ahora;
    ciclo();
  }
  actualizarSalidas(millis());
}
