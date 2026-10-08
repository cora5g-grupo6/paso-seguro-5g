#!/usr/bin/env python3
"""Mide la latencia contra el borde, desde la máquina donde se corre (laptop con dongle 5G, etc.).

Uso (desde tools/):
  ../edge/.venv/bin/python medir_latencia.py --borde http://IP-DEL-BORDE:8000 -n 100
  ../edge/.venv/bin/python medir_latencia.py --borde http://IP-DEL-BORDE:8000 --comparar https://www.google.com/generate_204
  ../edge/.venv/bin/python medir_latencia.py --alerta      # (modo demo) sube el agua y mide hasta que llega la alerta
  ../edge/.venv/bin/python medir_latencia.py -n 1 --guia xr20 --ciclos 50   # aviso hasta el XR20 con /guia?id=xr20 abierta

Mide:
  ping     ida y vuelta HTTP a /ping (red + servidor)
  alerta   desde que se manda "el agua subió" hasta que llega la alerta por SSE
           (subida + decisión en el borde + bajada). Necesita MODO_DEMO=true en el borde.
  guía     de la decisión a que el teléfono del guía recibe el aviso (lo confirma la página /guia con su hora,
           corregida con /ping). Necesita MODO_DEMO=true y la página abierta en el teléfono.
"""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time

import httpx


def pings(cliente: httpx.Client, url: str, n: int, pausa: float) -> list[float]:
    valores = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            cliente.get(url)
            valores.append((time.perf_counter() - t0) * 1000)
        except httpx.HTTPError as e:
            print(f"  fallo: {type(e).__name__}")
        time.sleep(pausa)
    return valores


def resumen(nombre: str, v: list[float]) -> None:
    if not v:
        print(f"{nombre}: sin datos")
        return
    s = sorted(v)
    p = lambda q: s[min(len(s) - 1, int(round((len(s) - 1) * q)))]  # noqa: E731
    jitter = statistics.pstdev(v) if len(v) > 1 else 0.0
    print(f"{nombre}: n={len(v)}  mín {s[0]:.1f}  p50 {p(.5):.1f}  p95 {p(.95):.1f}  máx {s[-1]:.1f}  jitter {jitter:.1f} ms")


def escuchar_alerta(borde: str, listo: threading.Event, llego: dict) -> None:
    with httpx.Client(timeout=None) as c, c.stream("GET", borde + "/api/stream") as r:
        tipo = None
        listo.set()
        for linea in r.iter_lines():
            if linea.startswith("event:"):
                tipo = linea[6:].strip()
            elif linea.startswith("data:") and tipo == "alerta":
                datos = json.loads(linea[5:])
                if datos.get("estado") == "CERRADO":
                    llego["t"] = time.perf_counter()
                    return


def medir_alerta(borde: str, ciclos: int) -> list[float]:
    valores = []
    with httpx.Client(timeout=5.0) as c:
        for k in range(ciclos):
            c.post(borde + "/api/demo/reiniciar")
            c.post(borde + "/api/demo/nivel", json={"nivel_pct": 10})
            time.sleep(0.5)
            listo, llego = threading.Event(), {}
            hilo = threading.Thread(target=escuchar_alerta, args=(borde, listo, llego), daemon=True)
            hilo.start()
            listo.wait(5)
            time.sleep(0.3)
            t0 = time.perf_counter()
            c.post(borde + "/api/demo/nivel", json={"nivel_pct": 85})
            hilo.join(5)
            if "t" in llego:
                ms = (llego["t"] - t0) * 1000
                valores.append(ms)
                print(f"  ciclo {k + 1}: alerta CERRADO en {ms:.1f} ms")
            else:
                print(f"  ciclo {k + 1}: no llegó la alerta")
        c.post(borde + "/api/demo/reiniciar")
    return valores


def entrega_guia(eventos: list[dict], cliente: str, desde_ms: float) -> float | None:
    """Entrega del aviso (decisión → teléfono) que confirmó `cliente` para el cierre disparado desde `desde_ms`."""
    for ev in sorted(eventos, key=lambda e: e.get("t_evento_ms", 0), reverse=True):
        if ev.get("estado") != "CERRADO" or ev.get("t_evento_ms", 0) < desde_ms:
            continue
        for a in ev.get("acks", []):
            if a.get("cliente") == cliente:
                return a.get("entrega_ms")
    return None


def medir_entrega_guia(borde: str, cliente: str, ciclos: int) -> list[float]:
    # La página /guia?id=<cliente> tiene que estar abierta en el teléfono: confirma cada alerta con su hora.
    valores = []
    with httpx.Client(timeout=5.0) as c:
        for k in range(ciclos):
            c.post(borde + "/api/demo/reiniciar")
            c.post(borde + "/api/demo/nivel", json={"nivel_pct": 10, "fuente": "sensor"})
            time.sleep(1.0)
            desde = time.time() * 1000 - 50
            c.post(borde + "/api/demo/nivel", json={"nivel_pct": 85, "fuente": "sensor"})
            ms, fin = None, time.monotonic() + 8
            while ms is None and time.monotonic() < fin:
                time.sleep(0.2)
                ms = entrega_guia(c.get(borde + "/api/eventos", params={"n": 10}).json(), cliente, desde)
            if ms is None:
                print(f"  ciclo {k + 1}: el teléfono «{cliente}» no confirmó en 8 s")
            else:
                valores.append(ms)
                print(f"  ciclo {k + 1}: aviso en el teléfono en {ms:.1f} ms")
        c.post(borde + "/api/demo/reiniciar")
    return valores


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--borde", default="http://localhost:8000")
    p.add_argument("-n", type=int, default=50)
    p.add_argument("--pausa", type=float, default=0.2)
    p.add_argument("--comparar", help="otra URL para comparar (p. ej. un servidor en internet)")
    p.add_argument("--alerta", action="store_true", help="mide acción → alerta por SSE (modo demo)")
    p.add_argument("--ciclos", type=int, default=5)
    p.add_argument("--guia", metavar="CLIENTE", help="mide decisión → aviso en el teléfono con /guia?id=CLIENTE abierta (modo demo)")
    a = p.parse_args()
    borde = a.borde.rstrip("/")

    with httpx.Client(timeout=5.0) as c:
        c.get(borde + "/ping")  # calienta la conexión
        resumen(f"Borde  {borde}/ping", pings(c, borde + "/ping", a.n, a.pausa))
        if a.comparar:
            try:
                c.get(a.comparar)
                resumen(f"Compara {a.comparar}", pings(c, a.comparar, a.n, a.pausa))
            except httpx.HTTPError as e:
                print(f"Compara {a.comparar}: no responde ({type(e).__name__}); ¿hay internet?")
    if a.alerta:
        resumen("Acción → alerta (SSE)", medir_alerta(borde, a.ciclos))
    if a.guia:
        resumen(f"Decisión → aviso en «{a.guia}»", medir_entrega_guia(borde, a.guia, a.ciclos))


if __name__ == "__main__":
    main()
