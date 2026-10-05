#!/usr/bin/env bash
# Demo completa sin hardware: borde con el video de prueba como cámara + ESP32 simulado.
#   ./demo_sin_hardware.sh
# Abre http://localhost:8000 (tablero), /guia (teléfono del guía) y /turista.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
EDGE="$AQUI/../edge"
PY="$EDGE/.venv/bin/python"
[ -x "$PY" ] || { echo "Falta el entorno. Primero: cd ../edge && ./correr_local.sh --instalar"; exit 1; }
[ -f "$AQUI/videos/rio_prueba.mp4" ] || "$PY" "$AQUI/generar_video_prueba.py" --instalar
[ -f "$EDGE/config/calibracion.json" ] || cp "$AQUI/videos/calibracion_prueba.json" "$EDGE/config/calibracion.json"

export CAMARA_ACTIVA=true
export CAMARA_FUENTES="${CAMARA_FUENTES:-../tools/videos/rio_prueba.mp4}"
export PERSONAS_METODO="${PERSONAS_METODO:-movimiento}"
export PERSONAS_ZONA="${PERSONAS_ZONA:-0,160,290,320}"
export MQTT_ACTIVO="${MQTT_ACTIVO:-false}"

cd "$EDGE"
"$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "${PUERTO:-8000}" --timeout-graceful-shutdown 3 &
BORDE=$!
SIM=""
trap 'kill $BORDE $SIM 2>/dev/null || true' EXIT INT TERM
sleep 4
"$PY" "$AQUI/simular_sensor.py" --borde "http://localhost:${PUERTO:-8000}" --escenario crecida &
SIM=$!
echo
echo "Tablero:  http://localhost:${PUERTO:-8000}"
echo "Guía:     http://localhost:${PUERTO:-8000}/guia"
echo "Turista:  http://localhost:${PUERTO:-8000}/turista"
echo "Ctrl+C para terminar."
wait $BORDE
