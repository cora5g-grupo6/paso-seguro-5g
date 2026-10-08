#!/usr/bin/env bash
# Prueba de conectividad por la red 5G (NDAC): pasos 1 a 3, con OK o FALLA en cada uno.
#
# Uso (desde tools/), con la laptop en la red 5G: por cable al dongle Nokia (con el Wi-Fi apagado)
# o por el Wi-Fi del CPE 5G:
#   ./prueba_conectividad.sh                            # dongle; borde en esta misma laptop
#   PUERTA_5G=192.168.1.1 ./prueba_conectividad.sh      # CPE 5G por Wi-Fi (su puerta de enlace)
#   ./prueba_conectividad.sh http://IP-DEL-BORDE:8000   # borde en otra máquina (MXIE u otra laptop)
#
# Variables opcionales:
#   PUERTA_5G=192.168.225.1   puerta de enlace del equipo 5G: la del dongle (etiqueta e informes de la PCII) o la del CPE
#   IP_PCII=...               IP pública de la PCII: si la salida es esa, se sale por su red y no por la 5G
# Sale con código 1 si algo falla.
set -u

BORDE="${1:-http://localhost:8000}"
BORDE="${BORDE%/}"
PUERTA="${PUERTA_5G:-${PUERTA_DONGLE:-192.168.225.1}}"
FALLAS=0

ok()    { printf '  \033[32mOK\033[0m     %s\n' "$1"; }
falla() { printf '  \033[31mFALLA\033[0m  %s\n' "$1"; FALLAS=$((FALLAS + 1)); }
ojo()   { printf '  \033[33mOJO\033[0m    %s\n' "$1"; }

# --- 1. Laptop conectada al dongle -------------------------------------------------------
echo "1. Laptop conectada al equipo 5G (dongle o CPE)"
if [ "$(uname)" = "Darwin" ]; then
  RUTA="$(route -n get default 2>/dev/null)"
  GW="$(printf '%s\n' "$RUTA" | awk '/gateway:/ {print $2}')"
  IF="$(printf '%s\n' "$RUTA" | awk '/interface:/ {print $2}')"
  WIFI_IF="$(networksetup -listallhardwareports 2>/dev/null | awk '/Hardware Port: (Wi-Fi|AirPort)/ {getline; print $2}')"
  IP_LOCAL="$([ -n "$IF" ] && ipconfig getifaddr "$IF" 2>/dev/null)"
  PING_ESPERA="-t 3"
else
  LINEA="$(ip route show default 2>/dev/null | head -1)"
  GW="$(printf '%s\n' "$LINEA" | awk '{for (i = 1; i < NF; i++) if ($i == "via") print $(i + 1)}')"
  IF="$(printf '%s\n' "$LINEA" | awk '{for (i = 1; i < NF; i++) if ($i == "dev") print $(i + 1)}')"
  WIFI_IF="$(ls /sys/class/net 2>/dev/null | grep -E '^wl' | head -1)"
  IP_LOCAL="$([ -n "$IF" ] && ip -4 addr show "$IF" 2>/dev/null | awk '/inet / {sub(/\/.*/, "", $2); print $2; exit}')"
  PING_ESPERA="-W 3"
fi

EN_5G=0
if [ "$GW" = "$PUERTA" ]; then
  EN_5G=1  # con el CPE, el Wi-Fi es justamente el camino a la 5G
  ok "La salida por defecto es el equipo 5G ($GW, interfaz $IF, IP ${IP_LOCAL:-?})"
else
  falla "La salida por defecto es ${GW:-ninguna} (interfaz ${IF:-?}), no el equipo 5G ($PUERTA): conectar el cable al dongle o el Wi-Fi del CPE"
  if [ -n "$WIFI_IF" ] && [ "$IF" = "$WIFI_IF" ]; then
    ojo "Se está saliendo por un Wi-Fi que no es el del equipo 5G ($IF): apagarlo o cambiar de red"
  fi
fi
# shellcheck disable=SC2086  # PING_ESPERA lleva opción y valor
if ping -c 2 $PING_ESPERA "$PUERTA" >/dev/null 2>&1; then
  ok "El equipo 5G responde ($PUERTA)"
else
  falla "El equipo 5G no responde ($PUERTA)"
fi

# --- 2. Salida a internet por la 5G -----------------------------------------------------------
echo "2. Salida a internet por la 5G"
COD="$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://www.google.com/generate_204)"
if [ "$COD" = "204" ]; then
  ok "Hay internet (google.com/generate_204)"
else
  falla "No hay salida a internet (respuesta: ${COD:-ninguna})"
fi

INFO="$(curl -s --max-time 8 https://ipinfo.io/json)"
IP_PUB="$(printf '%s\n' "$INFO" | sed -nE 's/.*"ip": *"([^"]+)".*/\1/p' | head -1)"
ORG="$(printf '%s\n' "$INFO" | sed -nE 's/.*"org": *"([^"]+)".*/\1/p' | head -1)"
if [ -z "$IP_PUB" ]; then
  falla "No se pudo ver la IP pública de salida"
elif [ -n "${IP_PCII:-}" ] && [ "$IP_PUB" = "$IP_PCII" ]; then
  falla "Se sale por la red de la PCII ($IP_PUB), no por la 5G: apagar el Wi-Fi"
elif printf '%s' "$ORG" | grep -qiE 'radiograf|racsa'; then
  if [ "$EN_5G" = 1 ]; then
    ok "Se sale por RACSA a través del equipo 5G, como dice la PCII ($IP_PUB, $ORG)"
  else
    # otras redes también salen por RACSA: sin el paso 1, esto no prueba que se pase por la 5G
    ojo "Se sale por RACSA ($ORG), pero no por el equipo 5G: eso no prueba la 5G (ver el paso 1)"
  fi
else
  ojo "Se sale por $IP_PUB (${ORG:-proveedor desconocido}). Según la PCII, la red 5G sale por RACSA: si no es RACSA, la ruta no pasa por la 5G"
fi

COD="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 'http://wis2box.imn.ac.cr/oapi/collections?f=json')"
if [ "$COD" = "200" ]; then
  ok "El IMN responde (lluvia)"
else
  falla "El IMN no responde (respuesta: ${COD:-ninguna})"
fi

# --- 3. Servidor de borde ---------------------------------------------------------------------
echo "3. Servidor de borde"
SALUD="$(curl -s --max-time 5 "$BORDE/salud")"
if printf '%s' "$SALUD" | grep -qE '"ok": *true'; then
  ESTADO="$(printf '%s' "$SALUD" | grep -oE '"estado": *"[A-Z]+"' | head -1 | sed -E 's/.*"([A-Z]+)"$/\1/')"
  ok "El borde responde en $BORDE (estado: ${ESTADO:-?})"
  MS="$(for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w '%{time_total}\n' --max-time 3 "$BORDE/ping"; done \
        | sort -n | awk '{v[NR] = $1} END {if (NR) printf "%.1f", v[int((NR + 1) / 2)] * 1000}')"
  [ -n "$MS" ] && echo "         Ida y vuelta a /ping: $MS ms (mediana de 10)"
  if [ -n "${IP_LOCAL:-}" ] && printf '%s' "$BORDE" | grep -qE 'localhost|127\.0\.0\.1'; then
    PUERTO="$(printf '%s' "$BORDE" | sed -nE 's#.*:([0-9]+)$#\1#p')"
    URL_RED="http://$IP_LOCAL:${PUERTO:-8000}"
    if curl -s --max-time 5 "$URL_RED/salud" | grep -qE '"ok": *true'; then
      ok "También responde en $URL_RED. En el XR20, probar $URL_RED/guia (si no carga desde la red 5G, es el NAT del equipo 5G)"
    else
      falla "Solo responde en localhost: el borde tiene que escuchar en 0.0.0.0 (así lo arranca edge/correr_local.sh)"
    fi
  fi
else
  falla "El borde no responde en $BORDE/salud: arrancarlo con edge/correr_local.sh"
fi

echo
if [ "$FALLAS" -eq 0 ]; then
  echo "Todo OK. Siguen el paso 4 (abrir /guia en el XR20) y el 5 (medir_latencia.py desde otro equipo en 5G)."
else
  echo "$FALLAS falla(s). Arreglarlas en orden: cada paso depende del anterior."
  exit 1
fi
