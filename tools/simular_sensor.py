#!/usr/bin/env python3
"""Simula el ESP32 del flotador: manda lecturas al borde por HTTP o MQTT, como el real.

Uso (desde tools/):
  ../edge/.venv/bin/python simular_sensor.py                          # crecida por HTTP a localhost:8000
  ../edge/.venv/bin/python simular_sensor.py --escenario oscilante    # prueba la histéresis
  ../edge/.venv/bin/python simular_sensor.py --modo mqtt --mqtt-host localhost
  ../edge/.venv/bin/python simular_sensor.py --borde http://10.0.0.20:8000 --duracion 120

Escenarios:
  crecida    el mismo guion del video de prueba (15 % -> 85 % -> 20 % en 100 s); el flotador salta a 75 %
  estable    nivel bajo y quieto
  oscilante  ronda el umbral de CUIDADO (40 %) para ver que el estado no aletea
  corte      cada 50 s deja de enviar 20 s (el borde debe pasar a modo degradado)
  flotador   nivel bajo pero el flotador salta 15 s cada minuto (respaldo físico)
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time

import httpx

GUION = [(0, 15), (20, 15), (50, 85), (70, 85), (100, 20)]
FLOTADOR_PCT = 75  # altura a la que se monta el flotador


def interpolar(t: float) -> float:
    t = t % GUION[-1][0]
    for (t0, n0), (t1, n1) in zip(GUION, GUION[1:]):
        if t0 <= t <= t1:
            return n0 if t1 == t0 else n0 + (n1 - n0) * (t - t0) / (t1 - t0)
    return GUION[-1][1]


def lectura(escenario: str, t: float) -> tuple[float, bool]:
    if escenario == "crecida":
        n = interpolar(t)
    elif escenario == "oscilante":
        n = 40 + 4 * math.sin(t * 1.3)
    elif escenario == "corte":
        n = 30
    else:  # estable, flotador
        n = 15
    n = max(0.0, min(100.0, n + random.gauss(0, 1.2)))
    flotador = n >= FLOTADOR_PCT or (escenario == "flotador" and 30 <= t % 60 < 45)
    return n, flotador


def semaforo_local(n: float, flotador: bool) -> str:
    return "ROJO" if flotador or n >= 70 else "AMARILLO" if n >= 40 else "VERDE"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--borde", default="http://localhost:8000")
    p.add_argument("--modo", choices=["http", "mqtt"], default="http")
    p.add_argument("--mqtt-host", default="localhost")
    p.add_argument("--mqtt-puerto", type=int, default=1883)
    p.add_argument("--mqtt-base", default="pasoseguro")
    p.add_argument("--id", default="esp32-sim")
    p.add_argument("--escenario", default="crecida", choices=["crecida", "estable", "oscilante", "corte", "flotador"])
    p.add_argument("--periodo", type=float, default=1.0, help="segundos entre lecturas")
    p.add_argument("--duracion", type=float, default=0, help="segundos (0 = sin fin)")
    a = p.parse_args()

    mqttc = None
    if a.modo == "mqtt":
        import paho.mqtt.client as mqtt

        mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-{a.id}")
        mqttc.on_message = lambda _c, _u, m: print(f"   ← estado del borde: {m.payload.decode()[:120]}")
        mqttc.connect(a.mqtt_host, a.mqtt_puerto, keepalive=30)
        mqttc.subscribe(f"{a.mqtt_base}/+/estado")
        mqttc.loop_start()

    http = httpx.Client(timeout=2.0)
    url = a.borde.rstrip("/") + "/api/sensor"
    rtt = None
    seq = 0
    inicio = time.time()
    print(f"Simulando {a.id} · escenario {a.escenario} · {a.modo.upper()} → {a.borde if a.modo == 'http' else a.mqtt_host}")
    try:
        while True:
            t = time.time() - inicio
            if a.duracion and t > a.duracion:
                break
            if a.escenario == "corte" and 15 <= t % 50 < 35:
                print(f"t={t:5.1f}s  (sin enviar: simula que el ESP32 perdió la red; él sigue con aviso local)")
                time.sleep(a.periodo)
                continue
            n, flot = lectura(a.escenario, t)
            datos = {"id": a.id, "nivel_pct": round(n, 1), "nivel_raw": int(n * 20), "flotador": flot,
                     "semaforo_local": semaforo_local(n, flot), "rssi": -60 + random.randint(-6, 6),
                     "seq": seq, "uptime_s": int(t), "modo": "simulador"}
            if rtt is not None:
                datos["rtt_ms"] = round(rtt, 1)
            if mqttc:
                mqttc.publish(f"{a.mqtt_base}/{a.id}/sensor", json.dumps(datos))
                print(f"t={t:5.1f}s  nivel={n:5.1f} %  flotador={'SÍ' if flot else 'no'}  → publicado por MQTT")
            else:
                try:
                    t0 = time.perf_counter()
                    r = http.post(url, json=datos)
                    rtt = (time.perf_counter() - t0) * 1000
                    resp = r.json()
                    print(f"t={t:5.1f}s  nivel={n:5.1f} %  flotador={'SÍ' if flot else 'no'}  → borde: "
                          f"{resp.get('estado', '?'):<8} luz={resp.get('color', '?'):<8} ida y vuelta {rtt:5.1f} ms")
                except (httpx.HTTPError, ValueError) as e:
                    rtt = None
                    print(f"t={t:5.1f}s  sin respuesta del borde ({type(e).__name__}): el ESP32 real queda en modo local")
            seq += 1
            time.sleep(a.periodo)
    except KeyboardInterrupt:
        pass
    finally:
        if mqttc:
            mqttc.loop_stop()


if __name__ == "__main__":
    main()
