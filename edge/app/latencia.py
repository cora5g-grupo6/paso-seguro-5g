"""Estadísticas de latencia en vivo (último, p50, p95, mín, máx) por nombre de medición.

Nombres que usa el sistema:
  vision_ms                 análisis de un cuadro (CPU)
  captura_a_decision_ms     del cuadro capturado a la decisión de la máquina de estados
  sensor_a_decision_ms      de la llegada del dato del ESP32 a la decisión
  esp32_rtt_ms              ida y vuelta del POST del ESP32 (Wi-Fi + 5G), lo mide el ESP32
  cliente_rtt_ms:<cliente>  ida y vuelta de /ping desde un tablero (p. ej. el XR20 del guía)
  alerta_entrega_ms         de la decisión a que el teléfono del guía recibe la alerta
  alerta_envio_ms:<canal>   tiempo de envío a cada canal (webhook, n8n, PTT)
  nube_rtt_ms               ida y vuelta del borde a un servidor en internet (comparación)
"""

from __future__ import annotations

import math
import threading
from collections import deque


class Estadistica:
    def __init__(self, ventana: int = 300):
        self._v: deque[float] = deque(maxlen=ventana)
        self.total = 0

    def agregar(self, ms: float) -> None:
        self._v.append(float(ms))
        self.total += 1

    def valores(self, n: int | None = None) -> list[float]:
        v = list(self._v)
        return v[-n:] if n else v

    def resumen(self) -> dict:
        if not self._v:
            return {"n": 0}
        a = sorted(self._v)
        n = len(a)

        def pct(p: float) -> float:
            k = (n - 1) * p / 100
            f = math.floor(k)
            c = min(f + 1, n - 1)
            return a[f] + (a[c] - a[f]) * (k - f)

        return {
            "n": n,
            "ultimo": round(self._v[-1], 2),
            "p50": round(pct(50), 2),
            "p95": round(pct(95), 2),
            "min": round(a[0], 2),
            "max": round(a[-1], 2),
            "prom": round(sum(a) / n, 2),
        }


class Latencias:
    """Registro seguro entre hilos (la visión corre en su propio hilo)."""

    def __init__(self, ventana: int = 300):
        self._series: dict[str, Estadistica] = {}
        self._ventana = ventana
        self._lock = threading.Lock()

    def agregar(self, nombre: str, ms: float) -> None:
        with self._lock:
            self._series.setdefault(nombre, Estadistica(self._ventana)).agregar(ms)

    def resumen(self) -> dict[str, dict]:
        with self._lock:
            return {k: v.resumen() for k, v in sorted(self._series.items())}

    def serie(self, nombre: str, n: int = 60) -> list[float]:
        with self._lock:
            e = self._series.get(nombre)
            return e.valores(n) if e else []
