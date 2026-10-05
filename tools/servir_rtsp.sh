#!/usr/bin/env bash
# Sirve el video de prueba por la red para probar el lector de video del borde sin la cámara 5G.
#
#   ./servir_rtsp.sh
#
# - Con mediamtx instalado (https://github.com/bluenviron/mediamtx): RTSP real.
#     En el borde: CAMARA_FUENTES=rtsp://127.0.0.1:8554/rio
# - Sin mediamtx: el mismo ffmpeg lo sirve por HTTP como MPEG-TS (un cliente a la vez).
#     En el borde: CAMARA_FUENTES=http://127.0.0.1:8090/rio.ts
#   (ffmpeg no puede ser servidor RTSP de salida; para eso está mediamtx.)
# En Linux/MXIE con Docker: docker compose --profile simulacion up (trae mediamtx).
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
VIDEO="${1:-$AQUI/videos/rio_prueba.mp4}"
[ -f "$VIDEO" ] || { echo "Falta $VIDEO. Primero: ../edge/.venv/bin/python generar_video_prueba.py"; exit 1; }
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg en el PATH"; exit 1; }
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264; then
  CODEC=(-c:v libx264 -preset ultrafast -tune zerolatency -bf 0 -g 15)
else
  CODEC=(-c:v mpeg4 -q:v 5 -bf 0 -g 15)
fi

if command -v mediamtx >/dev/null; then
  mediamtx >/dev/null 2>&1 &
  MTX=$!
  trap 'kill $MTX 2>/dev/null || true' EXIT INT TERM
  sleep 1
  echo "RTSP en rtsp://127.0.0.1:8554/rio  (Ctrl+C para parar)"
  ffmpeg -hide_banner -loglevel warning -re -stream_loop -1 -i "$VIDEO" -an "${CODEC[@]}" \
    -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/rio
else
  PUERTO="${PUERTO:-8090}"
  echo "Sin mediamtx: video por HTTP en http://127.0.0.1:${PUERTO}/rio.ts  (Ctrl+C para parar)"
  while true; do
    # -listen 1: ffmpeg atiende un cliente HTTP; cuando se va, vuelve a escuchar
    ffmpeg -hide_banner -loglevel warning -re -stream_loop -1 -i "$VIDEO" -an "${CODEC[@]}" \
      -f mpegts -listen 1 "http://0.0.0.0:${PUERTO}/rio.ts" || true
    sleep 0.5
  done
fi
