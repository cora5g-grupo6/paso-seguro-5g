#!/usr/bin/env python3
"""Precisión del nivel: pone un cartón (o el agua) a distancias conocidas y compara con lo que mide el sensor.

Uso (desde tools/, con el borde y la ESP32 andando):
  ../edge/.venv/bin/python medir_precision.py                       # 5 marcas: 35 45 55 65 75 cm, 10 lecturas
  ../edge/.venv/bin/python medir_precision.py --marcas 30 40 50 --lecturas 10 --d0 800 --d100 300

Para cada marca: medir con cinta de la cara de la sonda al cartón, ponerlo a esa distancia y apretar Enter.
Toma 10 lecturas nuevas de la ESP32 (una por segundo) desde /api/estado. El error en puntos usa la misma
calibración que la ESP32 (D0_MM y D100_MM), así que se compara directo con la meta: error < 5 puntos.
Guarda un CSV en edge/datos/ con una fila por marca.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

META_PTS = 5.0
CAMPOS = ("marca_real_mm", "n", "promedio_mm", "error_mm", "error_pts", "desvio_mm", "min_mm", "max_mm")


def resumen_marca(real_mm: float, lecturas: list[float], d0: float, d100: float) -> dict:
    if not lecturas:
        return {"marca_real_mm": real_mm, "n": 0, "promedio_mm": None, "error_mm": None, "error_pts": None,
                "desvio_mm": None, "min_mm": None, "max_mm": None}
    prom = statistics.fmean(lecturas)
    error = prom - real_mm
    return {
        "marca_real_mm": real_mm,
        "n": len(lecturas),
        "promedio_mm": round(prom, 1),
        "error_mm": round(error, 1),
        "error_pts": round(abs(error) / abs(d0 - d100) * 100, 1),
        "desvio_mm": round(statistics.pstdev(lecturas), 1),
        "min_mm": min(lecturas),
        "max_mm": max(lecturas),
    }


def informe(marcas: list[dict]) -> dict:
    pts = [m["error_pts"] for m in marcas if m["error_pts"] is not None]
    peor = max(pts) if pts else None
    return {"marcas": len(marcas), "peor_pts": peor, "prom_pts": round(statistics.fmean(pts), 1) if pts else None,
            "cumple": peor is not None and peor < META_PTS and len(pts) == len(marcas)}


def lecturas_nuevas(borde: str, cuantas: int, espera_s: float = 40) -> list[int]:
    import httpx

    vistas, valores, fin = set(), [], time.monotonic() + espera_s
    with httpx.Client(timeout=3) as c:
        while len(valores) < cuantas and time.monotonic() < fin:
            try:
                s = (c.get(f"{borde}/api/estado").json().get("sensores") or [{}])[0]
            except httpx.HTTPError:
                time.sleep(0.5)
                continue
            seq, mm = s.get("seq"), s.get("nivel_raw")
            if seq is not None and seq not in vistas:
                vistas.add(seq)
                if isinstance(mm, (int, float)) and mm > 0:
                    valores.append(mm)
                    print(f"  {len(valores):2d}/{cuantas}  {mm} mm", flush=True)
                else:
                    print("  (sin eco)", flush=True)
            time.sleep(0.3)
    return valores


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--borde", default="http://127.0.0.1:8000")
    p.add_argument("--marcas", type=float, nargs="+", default=[35, 45, 55, 65, 75], help="distancias reales en cm")
    p.add_argument("--lecturas", type=int, default=10)
    p.add_argument("--d0", type=float, default=800, help="D0_MM de la ESP32")
    p.add_argument("--d100", type=float, default=300, help="D100_MM de la ESP32")
    args = p.parse_args()

    filas = []
    for cm in args.marcas:
        input(f"\nCartón a {cm:g} cm de la cara de la sonda (medido con cinta). Enter para medir... ")
        lect = lecturas_nuevas(args.borde, args.lecturas)
        r = resumen_marca(cm * 10, lect, args.d0, args.d100)
        filas.append(r)
        if r["n"]:
            print(f"  → promedio {r['promedio_mm']} mm · error {r['error_mm']:+} mm = {r['error_pts']} puntos · desvío {r['desvio_mm']} mm")
        else:
            print("  → sin lecturas: revisar que la sonda vea el cartón")

    inf = informe(filas)
    print(f"\nPeor marca: {inf['peor_pts']} puntos · promedio {inf['prom_pts']} puntos · meta < {META_PTS:g}: "
          f"{'CUMPLE' if inf['cumple'] else 'NO CUMPLE'}")
    destino = Path(__file__).resolve().parent.parent / "edge" / "datos" / f"precision-{datetime.now():%Y-%m-%d-%H%M}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)
    print(f"Guardado en {destino}")


if __name__ == "__main__":
    main()
