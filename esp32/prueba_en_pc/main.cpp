// Banco de prueba en PC para PasoSeguro.ino.
// Compila el sketch tal cual y simula el agua y el flotador. Habla de verdad con el borde (HTTP)
// o con el broker (MQTT) por la red. Ver probar.sh.
//
// Variables de entorno:
//   PRUEBA_HOST=127.0.0.1     a dónde se conecta (en vez de BORDE_HOST del sketch)
//   PRUEBA_SEGUNDOS=40        duración
//   PRUEBA_SIN_WIFI=1         simula que no hay Wi-Fi (debe quedar en modo local)
#include <chrono>
#include <map>
#include <thread>

#include "Arduino.h"
#include "HTTPClient.h"
#include "WebServer.h"
#include "WiFi.h"

#include "../PasoSeguro/PasoSeguro.ino"

SerialFalso Serial;
WiFiFalso WiFi;
static const auto inicio = std::chrono::steady_clock::now();
static std::map<int, int> pines;

unsigned long millis() {
  return (unsigned long)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - inicio).count();
}
void delay(unsigned long ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }
void pinMode(int, int) {}
void digitalWrite(int pin, int valor) { pines[pin] = valor; }
long map(long x, long in_min, long in_max, long out_min, long out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Nivel simulado: 10 % -> 85 % en los primeros 40 % del tiempo, se queda, y baja a 10 %.
static double nivelSimulado() {
  double total = (getenv("PRUEBA_SEGUNDOS") ? atof(getenv("PRUEBA_SEGUNDOS")) : 40.0) * 1000.0;
  double f = millis() / total;
  if (f < 0.1) return 10;
  if (f < 0.4) return 10 + (f - 0.1) / 0.3 * 75;
  if (f < 0.6) return 85;
  if (f < 0.9) return 85 - (f - 0.6) / 0.3 * 75;
  return 10;
}
int analogRead(int) { return (int)(nivelSimulado() * 20); }                        // AGUA_LLENO = 2000 -> 100 %
int digitalRead(int pin) { return (pin == 14 && nivelSimulado() >= 75) ? LOW : HIGH; }  // flotador a 75 %

int main() {
  double segundos = getenv("PRUEBA_SEGUNDOS") ? atof(getenv("PRUEBA_SEGUNDOS")) : 40.0;
  setup();
  while (millis() < segundos * 1000) {
    loop();
    delay(2);
  }
  servidor.rutas["/estado"]();
  printf("\n/estado -> %d %s\n", servidor.ultimoCodigo, servidor.ultimaRespuesta.c_str());
  servidor.rutas["/"]();
  printf("/ -> %d (%u bytes de HTML)\n", servidor.ultimoCodigo, servidor.ultimaRespuesta.length());
  printf("Luces al final: rojo=%d amarillo=%d verde=%d · envíos=%lu · rtt=%ld ms · modo=%s\n", pines[PIN_LED_ROJO],
         pines[PIN_LED_AMAR], pines[PIN_LED_VERDE], seq, rttMs, modoLocal ? "LOCAL" : "borde");
  return 0;
}
