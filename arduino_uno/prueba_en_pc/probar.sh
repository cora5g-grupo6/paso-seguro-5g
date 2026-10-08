#!/usr/bin/env bash
# Compila PasoSeguroUNO.ino en la PC (sin placa), prueba su lógica y conversa con el borde local.
#   ./probar.sh                       # lógica + 3 envíos reales al borde en 127.0.0.1:8000
#   PRUEBA_SIN_BORDE=1 ./probar.sh    # solo la lógica
#   PRUEBA_HOST=192.168.1.17 ./probar.sh
# No reemplaza la prueba en la placa: verifica la lógica, el JSON y el HTTP.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
SALIDA="${TMPDIR:-/tmp}/pasoseguro_uno_pc"
c++ -std=c++17 -Wall -Wextra -Wno-unused-parameter -I"$AQUI" -o "$SALIDA" "$AQUI/main.cpp"
"$SALIDA"
