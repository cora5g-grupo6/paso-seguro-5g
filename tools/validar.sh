#!/usr/bin/env bash
# Valida Paso Seguro 5G de punta a punta, sin hardware:
#   1. pruebas automáticas del borde;
#   2. el borde arranca en modo demo;
#   3. flujo LIBRE → CUIDADO → CERRADO;
#   4. feeds de Waze contra la spec CIFS y el XSD oficial;
#   5. aviso a un «teléfono del guía» simulado, con su tiempo de entrega.
# Uso (desde la raíz del proyecto):  bash tools/validar.sh
# Sale con código 1 si algo falla. No toca datos del proyecto: usa una carpeta temporal y el puerto 8099.
set -uo pipefail
cd "$(dirname "$0")/.."
RAIZ=$(pwd)
PY="$RAIZ/edge/.venv/bin/python"
PUERTO=${PUERTO:-8099}
BORDE="http://127.0.0.1:$PUERTO"
TMP=$(mktemp -d)
FALLAS=0
PID=""
GUIA=""
ok()    { echo "  ✅ $*"; }
falla() { echo "  ❌ $*"; FALLAS=$((FALLAS + 1)); }
limpiar() { [ -n "$GUIA" ] && kill "$GUIA" 2>/dev/null; [ -n "$PID" ] && kill "$PID" 2>/dev/null; rm -rf "$TMP"; }
trap limpiar EXIT

if [ ! -x "$PY" ]; then
  echo "0/5 Creando el entorno de Python (hace falta Python 3.11 o más nuevo)…"
  BASE=$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)
  "$BASE" -m venv "$RAIZ/edge/.venv" && "$PY" -m pip install -q -r edge/requirements.txt -r edge/requirements-dev.txt \
    || { echo "No pude crear el entorno. Hace falta Python 3.11+."; exit 1; }
fi

echo "1/5 Pruebas automáticas"
N=$(cd edge && "$PY" -m pytest --collect-only -q -p no:warnings 2>/dev/null | awk -F': ' '/^tests\// {s+=$2} END {print s+0}')
if (cd edge && "$PY" -m pytest -q -p no:warnings -x >"$TMP/pytest.log" 2>&1); then ok "$N pruebas en verde"; else falla "hay pruebas que fallan:"; grep -E "FAILED|Error" "$TMP/pytest.log" | head -5; fi

echo "2/5 Borde en modo demo (puerto $PUERTO)"
(cd edge && CAMARA_ACTIVA=false MQTT_ACTIVO=false IMN_ACTIVO=false NUBE_ACTIVA=false MODO_DEMO=true BAJADA_S=1 \
  DATOS_DIR="$TMP/datos" exec "$PY" -m uvicorn app.main:app --port "$PUERTO" >"$TMP/borde.log" 2>&1) &
PID=$!; disown $PID
for _ in $(seq 1 40); do curl -sf -m 1 "$BORDE/salud" >/dev/null && break; sleep 0.5; done
if curl -sf -m 2 "$BORDE/salud" >/dev/null; then ok "responde en $BORDE/salud"; else falla "el borde no arrancó"; tail -20 "$TMP/borde.log"; exit 1; fi

estado() { curl -s -m 2 "$BORDE/api/estado" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['estado'])"; }
nivel()  { curl -s -m 2 -X POST "$BORDE/api/demo/nivel" -H 'Content-Type: application/json' -d "{\"nivel_pct\": $1, \"fuente\": \"sensor\"}" >/dev/null; }

echo "3/5 Flujo de decisión (umbrales: CUIDADO 40 %, CERRADO 70 %)"
curl -s -m 2 -X POST "$BORDE/api/demo/reiniciar" >/dev/null
for _ in 1 2 3 4 5 6; do nivel 10; sleep 0.6; done
E=$(estado); [ "$E" = "LIBRE" ] && ok "nivel 10 % → LIBRE" || falla "nivel 10 % dio $E (esperaba LIBRE)"
nivel 50; E=$(estado); [ "$E" = "CUIDADO" ] && ok "nivel 50 % → CUIDADO al instante" || falla "nivel 50 % dio $E (esperaba CUIDADO)"
nivel 85; E=$(estado); [ "$E" = "CERRADO" ] && ok "nivel 85 % → CERRADO al instante" || falla "nivel 85 % dio $E (esperaba CERRADO)"
nivel 10; E=$(estado); [ "$E" = "CERRADO" ] && ok "al bajar el agua no reabre de golpe (sigue CERRADO)" || falla "reabrió de golpe: $E"

echo "4/5 Feeds de Waze (spec CIFS y XSD oficial)"
if (cd tools && "$PY" validar_feed.py --borde "$BORDE" >"$TMP/feed.log" 2>&1); then ok "feeds válidos"; else falla "feeds con errores:"; tail -5 "$TMP/feed.log"; fi

echo "5/5 Aviso al teléfono del guía (simulado en esta máquina)"
cat >"$TMP/guia.py" <<EOF
import httpx, json, time
B = "$BORDE"
with httpx.Client(timeout=None) as c, c.stream("GET", B + "/api/stream") as r:
    tipo = None
    for l in r.iter_lines():
        if l.startswith("event:"): tipo = l[6:].strip()
        elif l.startswith("data:") and tipo == "alerta":
            d = json.loads(l[5:])
            if d.get("estado") == "CERRADO":
                httpx.post(f"{B}/api/alertas/{d['id']}/ack", json={"cliente": "xr20-simulado", "t_recibido_ms": time.time() * 1000})
EOF
"$PY" "$TMP/guia.py" >/dev/null 2>&1 &
GUIA=$!; disown $GUIA
sleep 1
SALIDA=$(cd tools && "$PY" medir_latencia.py --borde "$BORDE" -n 1 --guia xr20-simulado --ciclos 3 2>&1 | tail -1)
echo "     $SALIDA"
echo "$SALIDA" | grep -q "n=3" && ok "el guía confirmó los 3 avisos" || falla "el guía no confirmó los avisos"

echo
if [ "$FALLAS" -eq 0 ]; then echo "RESULTADO: todo en verde ✅"; else echo "RESULTADO: $FALLAS falla(s) ❌"; exit 1; fi
