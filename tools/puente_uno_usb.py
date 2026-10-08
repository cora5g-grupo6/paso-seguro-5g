#!/usr/bin/env python3
"""Puente UNO por USB -> borde: lee el nivel que imprime PasoSeguroUNO.ino y lo manda a /api/sensor.

Sirve cuando el UNO no tiene red: el sensor ultrasónico va en el UNO (5 V, pines 7 y 8)
y el UNO va por USB a la máquina del borde. Solo usa la biblioteca estándar más httpx.

Uso (desde tools/):
  ../edge/.venv/bin/python puente_uno_usb.py                      # busca /dev/cu.usbmodem* solo
  ../edge/.venv/bin/python puente_uno_usb.py --puerto /dev/cu.usbmodem143301
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import termios
import time

import httpx

# Línea del sketch: "d=1735 mm  nivel=86.8 %  flotador=no  -> ..."  (o "nivel=sin eco")
LINEA = re.compile(r"d=(-?\d+) mm\s+nivel=([\d.]+|sin eco) %\s+flotador=(si|no)")


def abrir(puerto: str) -> int:
    fd = os.open(puerto, os.O_RDONLY | os.O_NOCTTY)
    a = termios.tcgetattr(fd)
    a[0] = 0  # iflag
    a[1] = 0  # oflag
    a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL  # cflag
    a[3] = 0  # lflag: modo crudo
    a[4] = a[5] = termios.B115200
    a[6][termios.VMIN] = 1
    a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    return fd


def lineas(fd: int):
    resto = b""
    while True:
        trozo = os.read(fd, 256)
        if not trozo:
            raise OSError("el UNO se desconectó")
        resto += trozo
        while b"\n" in resto:
            linea, resto = resto.split(b"\n", 1)
            yield linea.decode("utf-8", "replace").strip()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--puerto", default="")
    p.add_argument("--borde", default="http://127.0.0.1:8000")
    p.add_argument("--id", default="uno-usb-1")
    args = p.parse_args()

    while True:
        puerto = args.puerto or next(iter(sorted(glob.glob("/dev/cu.usbmodem*"))), "")
        if not puerto:
            print("No veo el UNO por USB (/dev/cu.usbmodem*). Reintento en 3 s...", flush=True)
            time.sleep(3)
            continue
        try:
            fd = abrir(puerto)
            print(f"Leyendo el UNO en {puerto} -> {args.borde}/api/sensor como '{args.id}'", flush=True)
            with httpx.Client(timeout=3) as cli:
                for linea in lineas(fd):
                    m = LINEA.search(linea)
                    if not m:
                        if linea:
                            print("UNO:", linea, flush=True)
                        continue
                    mm, nivel, flot = int(m.group(1)), m.group(2), m.group(3) == "si"
                    datos = {"id": args.id, "nivel_raw": mm, "flotador": flot, "enlace": "usb"}
                    if nivel != "sin eco":
                        datos["nivel_pct"] = float(nivel)
                    t0 = time.monotonic()
                    try:
                        r = cli.post(f"{args.borde}/api/sensor", json=datos)
                        ms = (time.monotonic() - t0) * 1000
                        print(f"d={mm} mm nivel={nivel} -> borde {r.status_code} ({ms:.0f} ms)", flush=True)
                    except httpx.HTTPError as e:
                        print("El borde no contesta:", e, flush=True)
        except OSError as e:
            print("Problema con el puerto:", e, "- reintento en 3 s", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
