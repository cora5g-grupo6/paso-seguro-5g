"""Tests del cliente del IMN (API WIS2 / OGC API Features).

Los datos de prueba son respuestas reales del 5-oct-2026 (tests/datos/imn_*.json).
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from app.imn import (
    NOMBRE_LLUVIA,
    ClienteIMN,
    IMNError,
    estacion_mas_cercana,
    parsear_estaciones,
    parsear_lluvia,
)

DATOS = Path(__file__).parent / "datos"
LLUVIA = json.loads((DATOS / "imn_lluvia_78774.json").read_text(encoding="utf-8"))
ESTACIONES = json.loads((DATOS / "imn_estaciones.json").read_text(encoding="utf-8"))
LIBERIA = "0-20000-0-78774"


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def test_lee_las_8_estaciones_reales():
    est = parsear_estaciones(ESTACIONES)
    assert len(est) == 8
    lib = next(e for e in est if e.id == LIBERIA)
    assert "Daniel Oduber" in lib.nombre
    assert lib.lat == pytest.approx(10.589, abs=1e-3)
    assert lib.lon == pytest.approx(-85.552, abs=1e-3)


def test_la_estacion_mas_cercana_al_vado_es_finca_la_ceiba():
    est, km = estacion_mas_cercana(parsear_estaciones(ESTACIONES), 9.908952, -85.206468)
    assert est.id == "0-188-0-72157"
    assert 20 < km < 30


def test_lluvia_horaria_del_aguacero_de_ayer_en_liberia():
    r = parsear_lluvia(LLUVIA, LIBERIA, hasta=ts("2026-10-04T22:30:00Z"))
    assert r.mm_1h == pytest.approx(40.4, abs=0.01)
    assert r.mm_3h == pytest.approx(45.6, abs=0.01)  # 40,4 + 5,2 + 0
    assert r.t_ultimo == ts("2026-10-04T22:00:00Z")


def test_ultimo_dato_disponible_y_acumulados():
    r = parsear_lluvia(LLUVIA, LIBERIA)
    assert r.t_ultimo == ts("2026-10-05T15:00:00Z")
    assert r.mm_1h == 0
    assert r.mm_24h == pytest.approx(47.6, abs=0.05)
    assert r.max_1h == pytest.approx(40.4, abs=0.01)
    assert r.t_max == ts("2026-10-04T22:00:00Z")


def test_estacion_sin_datos_devuelve_none():
    assert parsear_lluvia({"type": "FeatureCollection", "features": []}, LIBERIA) is None


def test_el_cliente_ordena_por_reporttime_y_filtra_la_lluvia():
    urls = []

    def servidor(request):
        urls.append(request.url)
        return httpx.Response(200, json=LLUVIA)

    cli = ClienteIMN("http://imn.prueba/oapi", transport=httpx.MockTransport(servidor))
    r = asyncio.run(cli.lluvia(LIBERIA))
    params = urls[0].params
    assert params["sortby"] == "-reportTime"  # con -phenomenonTime el servidor real responde error
    assert params["name"] == NOMBRE_LLUVIA
    assert params["wigos_station_identifier"] == LIBERIA
    assert r.mm_1h == 0


def test_sin_red_el_cliente_da_un_error_claro():
    def servidor(request):
        raise httpx.ConnectError("sin red")

    cli = ClienteIMN("http://imn.prueba/oapi", transport=httpx.MockTransport(servidor))
    with pytest.raises(IMNError):
        asyncio.run(cli.lluvia(LIBERIA))
