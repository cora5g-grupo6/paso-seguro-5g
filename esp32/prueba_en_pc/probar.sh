#!/usr/bin/env bash
# Compila PasoSeguro.ino en la PC (sin placa) y lo corre contra el borde local.
#   ./probar.sh                 # HTTP contra el borde en 127.0.0.1:8000 (40 s)
#   ./probar.sh mqtt            # MQTT contra el broker en 127.0.0.1:1883
#   PRUEBA_SIN_WIFI=1 ./probar.sh   # sin Wi-Fi: debe quedar en modo local y avisar igual
# No reemplaza la prueba en la placa: verifica la lógica, el JSON y los protocolos.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
SALIDA="${TMPDIR:-/tmp}/pasoseguro_pc"
DEFINE=(-DUSAR_ULTRASONICO=0)  # la PC simula el sensor analógico
if [ "${1:-}" = "mqtt" ]; then
  # Copia del sketch con USAR_MQTT 1 (el original no se toca)
  mkdir -p "$SALIDA.mqtt/PasoSeguro"
  sed 's/^#define USAR_MQTT 0/#define USAR_MQTT 1/' "$AQUI/../PasoSeguro/PasoSeguro.ino" > "$SALIDA.mqtt/PasoSeguro/PasoSeguro.ino"
  sed "s#../PasoSeguro/PasoSeguro.ino#$SALIDA.mqtt/PasoSeguro/PasoSeguro.ino#" "$AQUI/main.cpp" > "$SALIDA.mqtt/main.cpp"
  FUENTE="$SALIDA.mqtt/main.cpp"
else
  FUENTE="$AQUI/main.cpp"
fi
c++ -std=c++17 -Wall -Wextra -Wno-unused-parameter -I"$AQUI" "${DEFINE[@]+"${DEFINE[@]}"}" -o "$SALIDA" "$FUENTE"
echo "Compiló sin errores. Corriendo ${PRUEBA_SEGUNDOS:-40} s..."
PRUEBA_HOST="${PRUEBA_HOST:-127.0.0.1}" "$SALIDA"
