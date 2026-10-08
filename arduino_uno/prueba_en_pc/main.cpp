// Banco de prueba en PC para PasoSeguroUNO.ino (sin placa).
// Prueba la lógica con reloj y sensor simulados, y después conversa de verdad con el borde local.
#include "Arduino.h"
#include "Ethernet.h"

unsigned long pruebaMicros = 0;
bool pruebaTiempoReal = false;
int pruebaPines[32] = {0};
int pruebaAnalogico[8] = {0};
long pruebaEchoUs = 0;
bool pruebaDhcpOk = true;
const char* pruebaHostBorde = "127.0.0.1";
bool pruebaBordeCaido = false;
SerialFalso Serial;
EthernetClass Ethernet;

#include "../PasoSeguroUNO/PasoSeguroUNO.ino"

static int fallas = 0;
#define REVISAR(cond)                                         \
  do {                                                        \
    if (!(cond)) {                                            \
      printf("  FALLA, línea %d: %s\n", __LINE__, #cond);     \
      fallas++;                                               \
    }                                                         \
  } while (0)

static long ecoParaMm(long mm) { return lround(mm * 2.0 / velocidadSonidoMmUs(20)); }

int main() {
  Serial.silencio = true;
  pruebaPines[PIN_FLOTADOR] = HIGH;  // con INPUT_PULLUP, el flotador abierto se lee HIGH
  printf("Lógica (reloj y sensor simulados)\n");

  // Nivel a partir de la distancia, con los límites de la calibración
  REVISAR(fabs(nivelDesdeMm(D0_MM)) < 0.01);
  REVISAR(fabs(nivelDesdeMm(D100_MM) - 100) < 0.01);
  REVISAR(fabs(nivelDesdeMm((D0_MM + D100_MM) / 2) - 50) < 0.01);
  REVISAR(nivelDesdeMm(D0_MM + 100) == 0);
  REVISAR(nivelDesdeMm(D100_MM - 200) == 110);
  REVISAR(nivelDesdeMm(-1) < 0);

  // Distancia con eco simulado (mediana de 5); sin eco no inventa un valor
  pruebaEchoUs = ecoParaMm(500);
  REVISAR(labs(distanciaMm(20) - 500) <= 1);
  pruebaEchoUs = 0;
  REVISAR(distanciaMm(20) == -1);

  // JSON: decimales con dtostrf (sin «?») y sin nivel cuando no hay eco
  char json[200];
  armarJson(json, sizeof json, 57.63, 512, false, 14);
  REVISAR(strstr(json, "\"nivel_pct\":57.6") != nullptr);
  REVISAR(strstr(json, "\"nivel_raw\":512") != nullptr);
  REVISAR(strstr(json, "\"flotador\":false") != nullptr);
  REVISAR(strstr(json, "\"rtt_ms\":14") != nullptr);
  REVISAR(strstr(json, "\"id\":\"uno-5g\"") != nullptr);
  REVISAR(strchr(json, '?') == nullptr);
  armarJson(json, sizeof json, -1, -1, true, -1);
  REVISAR(strstr(json, "nivel_pct") == nullptr && strstr(json, "\"flotador\":true") != nullptr);

  // Respuesta del borde
  REVISAR(procesarRespuesta("{\"estado\":\"CUIDADO\",\"color\":\"AMARILLO\",\"nivel\":52.0,\"buzzer\":false,"
                            "\"alarma_persona\":true,\"t_srv\":1}"));
  REVISAR(estadoBorde == CUIDADO && alarmaPersona);
  REVISAR(!procesarRespuesta("<html>error</html>"));

  // Modo local: sube al instante, baja de a un escalón y el flotador manda
  unsigned long t = 0;
  REVISAR(estadoLocal(75, false, t) == CERRADO);
  REVISAR(estadoLocal(20, false, t += 1000) == CERRADO);
  REVISAR(estadoLocal(20, false, t += BAJADA_LOCAL_MS) == CUIDADO);
  REVISAR(estadoLocal(20, false, t += BAJADA_LOCAL_MS) == LIBRE);
  REVISAR(estadoLocal(10, true, t += 1000) == CERRADO);
  REVISAR(estadoLocal(-1, false, t += 1000) == CERRADO);  // sin eco no baja

  // Sin borde: a los 5 s pasa a modo local, usa su propio nivel y las luces parpadean
  estadoLocalActual = LIBRE;
  bajando = false;
  hayRed = true;
  modoLocal = false;
  pruebaBordeCaido = true;
  tUltimoBorde = millis();
  pruebaEchoUs = ecoParaMm(500);  // 60 %
  for (int i = 0; i < 7; i++) {
    ciclo();
    delay(1000);
  }
  REVISAR(modoLocal && estadoMostrado == CUIDADO);
  actualizarSalidas(1000);
  REVISAR(pruebaPines[PIN_AMARILLO] == HIGH && pruebaPines[PIN_ROJO] == LOW);
  actualizarSalidas(1500);
  REVISAR(pruebaPines[PIN_AMARILLO] == LOW);

  // Conversación real con el borde que corre en la PC (se salta con PRUEBA_SIN_BORDE=1)
  if (!getenv("PRUEBA_SIN_BORDE")) {
    pruebaTiempoReal = true;
    pruebaBordeCaido = false;
    if (getenv("PRUEBA_HOST")) pruebaHostBorde = getenv("PRUEBA_HOST");
    Serial.silencio = false;
    printf("\nConversación real con el borde en %s:%u\n", pruebaHostBorde, BORDE_PUERTO);
    for (int i = 0; i < 3; i++) {
      ciclo();
      delay(1000);
    }
    REVISAR(ultimoCodigo == 200 && !modoLocal);
  }

  printf(fallas ? "\n%d falla(s)\n" : "\nTodo OK\n", fallas);
  return fallas ? 1 : 0;
}
