#!/usr/bin/env bash
# Corre el servidor de borde en esta laptop, sin Docker.
#   ./correr_local.sh              instala lo que falte y arranca en http://localhost:8000
#   ./correr_local.sh --instalar   solo instala
#   PUERTO=8080 ./correr_local.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null; then
    uv venv --python 3.11 .venv
  elif command -v python3.11 >/dev/null; then
    python3.11 -m venv .venv
  else
    echo "Hace falta Python 3.11 (o uv: https://docs.astral.sh/uv/)."
    exit 1
  fi
fi
if command -v uv >/dev/null; then
  uv pip install --python .venv/bin/python -q -r requirements.txt -r requirements-dev.txt
else
  .venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt
fi

[ -f .env ] || { cp .env.example .env; echo "Creé .env a partir de .env.example: revíselo."; }
if [ ! -f ../tools/videos/rio_prueba.mp4 ]; then
  echo "Generando el video de prueba (unos 40 s)..."
  .venv/bin/python ../tools/generar_video_prueba.py
fi
[ -f config/calibracion.json ] || cp ../tools/videos/calibracion_prueba.json config/calibracion.json

[ "${1:-}" = "--instalar" ] && { echo "Listo."; exit 0; }
echo "Tablero: http://localhost:${PUERTO:-8000} · Guía: /guia · Turista: /turista · Calibrar: /calibrar"
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PUERTO:-8000}" --timeout-graceful-shutdown 3
