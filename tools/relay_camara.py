#!/usr/bin/env python3
"""Plan C de la cámara: lee una webcam USB (o un RTSP o un video) en esta máquina y empuja
los cuadros JPEG al borde por HTTP (POST /api/camara/frame).

Sirve cuando la cámara no se puede leer directo desde el borde: por ejemplo, webcam en una
laptop conectada a la red 5G con el dongle, y el borde corriendo en el MXIE.

Uso (desde tools/):
  ../edge/.venv/bin/python relay_camara.py --borde http://IP-DEL-BORDE:8000 --fuente 0 --fps 5
  ../edge/.venv/bin/python relay_camara.py --fuente videos/rio_prueba.mp4
"""

from __future__ import annotations

import argparse
import time

import cv2
import httpx


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--borde", default="http://localhost:8000")
    p.add_argument("--fuente", default="0", help="índice de webcam, URL RTSP/HTTP o archivo de video")
    p.add_argument("--fps", type=float, default=5)
    p.add_argument("--ancho", type=int, default=640)
    p.add_argument("--calidad", type=int, default=80)
    a = p.parse_args()

    fuente = int(a.fuente) if a.fuente.isdigit() else a.fuente
    cap = cv2.VideoCapture(fuente)
    if not cap.isOpened():
        raise SystemExit(f"No se pudo abrir la fuente {a.fuente}")
    es_archivo = isinstance(fuente, str) and "://" not in fuente
    url = a.borde.rstrip("/") + "/api/camara/frame"
    cliente = httpx.Client(timeout=3.0)
    enviados = 0
    print(f"Empujando cuadros de {a.fuente} a {url} ({a.fps} por segundo). Ctrl+C para parar.")
    try:
        while True:
            t0 = time.time()
            ok, img = cap.read()
            if not ok:
                if es_archivo:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                print("La cámara no entrega cuadros; reintento en 1 s")
                time.sleep(1)
                continue
            if img.shape[1] > a.ancho:
                img = cv2.resize(img, (a.ancho, int(img.shape[0] * a.ancho / img.shape[1])))
            ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, a.calidad])
            try:
                r = cliente.post(url, content=jpg.tobytes(), headers={"Content-Type": "image/jpeg"})
                enviados += 1
                if r.status_code != 200 or enviados % 50 == 0:
                    print(f"{enviados} cuadros · última respuesta {r.status_code} · {(time.time() - t0) * 1000:.0f} ms")
            except httpx.HTTPError as e:
                print(f"Sin borde ({type(e).__name__}); reintento")
            time.sleep(max(0.0, 1 / a.fps - (time.time() - t0)))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
