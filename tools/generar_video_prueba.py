#!/usr/bin/env python3
"""Genera un video de prueba para ensayar sin cámara.

Escena: tubo transparente con agua teñida de azul, regla pintada con franjas
verde/amarilla/roja, marca de referencia magenta y una "persona" que entra a la
zona del cruce. El nivel sigue el mismo guion que simular_sensor.py, así la cámara
y el ESP32 simulado coinciden.

Uso (desde tools/):
  ../edge/.venv/bin/python generar_video_prueba.py              # crea videos/rio_prueba.mp4 (100 s)
  ../edge/.venv/bin/python generar_video_prueba.py --instalar   # además copia la calibración al borde
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent
ANCHO, ALTO, FPS = 640, 480, 15
X0, X1 = 300, 380  # paredes del tubo
Y_CIEN, Y_CERO = 70, 410  # marcas de 100 % y 0 %
AGUA = np.array((205, 95, 25), np.float32)  # BGR, colorante azul
GUION = [(0, 15), (20, 15), (50, 85), (70, 85), (100, 20)]  # (segundo, nivel %)
PERSONA = (55.0, 63.0)  # segundos en que alguien entra a la zona del cruce
ZONA_PERSONAS = (0, 160, 290, 320)  # x, y, ancho, alto (para PERSONAS_ZONA)


def nivel_en(t: float) -> float:
    t = t % GUION[-1][0]
    for (t0, n0), (t1, n1) in zip(GUION, GUION[1:]):
        if t0 <= t <= t1:
            return n0 if t1 == t0 else n0 + (n1 - n0) * (t - t0) / (t1 - t0)
    return GUION[-1][1]


def y_de(pct: float) -> int:
    return int(round(Y_CERO - (Y_CERO - Y_CIEN) * pct / 100))


def escena_base() -> np.ndarray:
    img = np.zeros((ALTO, ANCHO, 3), np.uint8)
    for y in range(ALTO):  # pared con degradado suave
        img[y, :] = (200 - y // 12, 205 - y // 14, 210 - y // 16)
    cv2.rectangle(img, (0, 430), (ANCHO, ALTO), (95, 110, 125), -1)  # mesa
    # regla pintada a la derecha del tubo
    cv2.rectangle(img, (X1 + 8, Y_CIEN - 8), (X1 + 38, Y_CERO + 8), (240, 240, 240), -1)
    for desde, hasta, color in ((0, 40, (60, 160, 60)), (40, 70, (0, 200, 250)), (70, 100, (40, 40, 210))):
        cv2.rectangle(img, (X1 + 30, y_de(hasta)), (X1 + 38, y_de(desde)), color, -1)
    for p in range(0, 101, 10):
        y = y_de(p)
        cv2.line(img, (X1 + 8, y), (X1 + 24, y), (25, 25, 25), 2)
        cv2.putText(img, str(p), (X1 + 42, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 40, 40), 1, cv2.LINE_AA)
    # marca de referencia fija (magenta)
    cv2.rectangle(img, (X1 + 52, Y_CIEN - 10), (X1 + 70, Y_CIEN + 8), (255, 0, 255), -1)
    cv2.putText(img, "PRUEBA", (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1, cv2.LINE_AA)
    return img


def dibujar_persona(img: np.ndarray, t: float) -> None:
    a, b = PERSONA
    if not a <= t <= b:
        return
    x = int(30 + (t - a) / (b - a) * 200)
    y = 250
    oscuro = (55, 50, 45)
    cv2.circle(img, (x, y), 16, oscuro, -1)
    cv2.rectangle(img, (x - 18, y + 16), (x + 18, y + 110), oscuro, -1)
    paso = int(14 * math.sin(t * 8))
    cv2.line(img, (x - 8, y + 110), (x - 8 + paso, y + 175), oscuro, 9)
    cv2.line(img, (x + 8, y + 110), (x + 8 - paso, y + 175), oscuro, 9)


def cuadro(base: np.ndarray, t: float, rng: np.random.Generator) -> np.ndarray:
    img = base.astype(np.float32)
    y_sup = Y_CERO - (Y_CERO - Y_CIEN) * nivel_en(t) / 100
    for x in range(X0, X1):  # agua con ondas en la superficie
        yy = int(round(y_sup + 2.2 * math.sin(x / 7 + t * 3.5)))
        if yy < Y_CERO:
            prof = np.linspace(0.92, 1.05, Y_CERO - yy)[:, None]
            img[yy:Y_CERO, x] = AGUA * prof
    for _ in range(3):  # burbujas
        bx = int(rng.integers(X0 + 6, X1 - 6))
        by = int(rng.uniform(y_sup + 8, Y_CERO - 6)) if y_sup + 14 < Y_CERO else Y_CERO - 6
        cv2.circle(img, (bx, by), 2, (230, 170, 120), -1)
    cv2.rectangle(img, (X0 - 3, Y_CIEN - 25), (X1 + 3, Y_CERO + 3), (175, 175, 175), 2)  # paredes del tubo
    img *= 1 + 0.025 * math.sin(t * 2.1)  # parpadeo de la luz
    img += rng.normal(0, 3, img.shape)
    out = np.clip(img, 0, 255).astype(np.uint8)
    dibujar_persona(out, t)
    return out


def calibracion() -> dict:
    return {
        "roi": [X0, Y_CIEN - 20, X1 - X0, Y_CERO - Y_CIEN + 30],
        "y_cero": Y_CERO,
        "y_cien": Y_CIEN,
        "hsv_bajo": [90, 80, 40],
        "hsv_alto": [130, 255, 255],
        "modo": "columna",
        "ref_roi": [X1 + 50, Y_CIEN - 12, 24, 24],
        "ref_hsv_bajo": [140, 80, 80],
        "ref_hsv_alto": [170, 255, 255],
    }


def cuadros(segundos: float):
    base = escena_base()
    rng = np.random.default_rng(7)
    for k in range(int(segundos * FPS)):
        yield cuadro(base, k / FPS, rng)


@contextmanager
def sin_stderr():
    """El escritor AVFoundation de OpenCV en Mac imprime una línea por cuadro: se silencia."""
    copia = os.dup(2)
    nulo = os.open(os.devnull, os.O_WRONLY)
    os.dup2(nulo, 2)
    try:
        yield
    finally:
        os.dup2(copia, 2)
        os.close(nulo)
        os.close(copia)


def con_ffmpeg(salida: Path, segundos: float) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    # sin cuadros B (-bf 0), como transmite una cámara en vivo de baja latencia
    for codec in (["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-bf", "0", "-pix_fmt", "yuv420p"],
                  ["-c:v", "mpeg4", "-q:v", "4", "-bf", "0"]):
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ANCHO}x{ALTO}",
               "-r", str(FPS), "-i", "-", *codec, "-g", str(FPS), str(salida)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for img in cuadros(segundos):
                proc.stdin.write(img.tobytes())
            proc.stdin.close()
        except BrokenPipeError:
            pass
        if proc.wait() == 0:
            return True
    return False


def con_opencv(salida: Path, segundos: float) -> Path:
    for fourcc, ext in (("avc1", ".mp4"), ("mp4v", ".mp4"), ("MJPG", ".avi")):
        destino = salida.with_suffix(ext)
        with sin_stderr():
            escritor = cv2.VideoWriter(str(destino), cv2.VideoWriter_fourcc(*fourcc), FPS, (ANCHO, ALTO))
            if not escritor.isOpened():
                continue
            for img in cuadros(segundos):
                escritor.write(img)
            escritor.release()
        return destino
    raise SystemExit("No hay códec de video disponible (instale ffmpeg)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--salida", default=str(AQUI / "videos" / "rio_prueba.mp4"))
    p.add_argument("--segundos", type=float, default=GUION[-1][0])
    p.add_argument("--instalar", action="store_true", help="copia la calibración a edge/config/calibracion.json")
    a = p.parse_args()

    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    if not con_ffmpeg(salida, a.segundos):
        salida = con_opencv(salida, a.segundos)
    total = int(a.segundos * FPS)

    cal = salida.parent / "calibracion_prueba.json"
    cal.write_text(json.dumps(calibracion(), indent=1), encoding="utf-8")
    print(f"Video: {salida} ({total} cuadros, {a.segundos:.0f} s, {FPS} cuadros/s)")
    print(f"Calibración: {cal}")
    print(f"Zona de personas para el video: PERSONAS_ZONA={','.join(map(str, ZONA_PERSONAS))}")
    if a.instalar:
        destino = AQUI.parent / "edge" / "config" / "calibracion.json"
        shutil.copyfile(cal, destino)
        print(f"Calibración instalada en {destino}")


if __name__ == "__main__":
    main()
