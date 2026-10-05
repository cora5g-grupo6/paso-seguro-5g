#!/usr/bin/env python3
"""Valida los feeds de Waze del borde contra la spec CIFS y el XSD oficial.

Uso (desde tools/):
  ../edge/.venv/bin/python validar_feed.py                              # borde en localhost:8000
  ../edge/.venv/bin/python validar_feed.py --borde http://10.0.0.20:8000
  ../edge/.venv/bin/python validar_feed.py --json feed.json --xml feed.xml   # archivos sueltos
Sale con código 1 si hay errores.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
import xmlschema

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "edge"))
from app.feeds.waze import CAJA_CR, validar_cifs  # noqa: E402

XSD = AQUI.parent / "edge" / "app" / "feeds" / "cifsv2.xsd"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--borde", default="http://localhost:8000")
    p.add_argument("--json", help="archivo JSON en vez de pedirlo al borde")
    p.add_argument("--xml", help="archivo XML en vez de pedirlo al borde")
    a = p.parse_args()

    if a.json or a.xml:
        feed_json = json.loads(Path(a.json).read_text(encoding="utf-8")) if a.json else None
        feed_xml = Path(a.xml).read_text(encoding="utf-8") if a.xml else None
    else:
        b = a.borde.rstrip("/")
        feed_json = httpx.get(b + "/feeds/waze.json", timeout=5).json()
        feed_xml = httpx.get(b + "/feeds/waze.xml", timeout=5).text

    hay_error = False
    if feed_json is not None:
        r = validar_cifs(feed_json, CAJA_CR)
        print(f"JSON: {len(feed_json.get('incidents', []))} incidente(s) · {'OK' if r.ok else 'CON ERRORES'}")
        for e in r.errores:
            print(f"  ERROR  {e}")
        for w in r.avisos:
            print(f"  aviso  {w}")
        hay_error |= not r.ok
    if feed_xml is not None:
        errores = [str(getattr(e, "reason", e)) for e in xmlschema.XMLSchema(str(XSD)).iter_errors(feed_xml)]
        print(f"XML contra el XSD oficial de Waze: {'OK' if not errores else 'CON ERRORES'}")
        for e in errores:
            print(f"  ERROR  {e}")
        hay_error |= bool(errores)
    return 1 if hay_error else 0


if __name__ == "__main__":
    sys.exit(main())
