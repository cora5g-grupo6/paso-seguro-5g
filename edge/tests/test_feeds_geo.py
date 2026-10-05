"""Tests del GeoJSON de estado y del exportador para Google Maps Content Partners.

Esquema de Google para cargar cierres puntuales (GeoJSON/JSON/XML), leído el 5-oct-2026:
https://support.google.com/mapcontentpartners/answer/144284
Campos obligatorios: TYPE, POLYLINE, DIRECTION, START_TIME, END_TIME.
"""

import re
from datetime import datetime

import pytest

from app.cruce import Cruce
from app.estado import Estado
from app.feeds.geo import COLORES, estado_geojson, google_cierres_geojson
from app.feeds.waze import ZONA_CR, GestorEpisodios

T0 = datetime(2026, 10, 9, 9, 0, tzinfo=ZONA_CR).timestamp()


@pytest.fixture
def cruce():
    return Cruce(
        id="vado-prueba",
        nombre="Vado de prueba",
        rio="Río Vainilla",
        calle="Ruta 623",
        punto=(9.908952, -85.206468),
        polilinea=[(9.910472, -85.207366), (9.908952, -85.206468), (9.907315, -85.207280)],
        rio_linea=[(9.910134, -85.208026), (9.908834, -85.206288), (9.907428, -85.206256)],
    )


def _punto(fc):
    return next(f for f in fc["features"] if f["geometry"]["type"] == "Point")


def _por_tipo(fc, tipo):
    return [f for f in fc["features"] if f["properties"].get("tipo") == tipo]


def test_estado_geojson_trae_el_punto_y_el_tramo_en_orden_lon_lat(cruce):
    fc = estado_geojson(cruce, Estado.CERRADO, T0, nivel=74.0, fuente="camara",
                        razones=["Nivel 74 %"], mensajes={"es": "Cerrado", "en": "Closed"})
    assert fc["type"] == "FeatureCollection"
    punto = _punto(fc)
    [tramo] = _por_tipo(fc, "tramo")
    assert punto["geometry"]["coordinates"] == [cruce.punto[1], cruce.punto[0]]
    assert tramo["geometry"]["coordinates"][0] == [cruce.polilinea[0][1], cruce.polilinea[0][0]]
    p = punto["properties"]
    assert p["estado"] == "CERRADO"
    assert p["color"] == COLORES[Estado.CERRADO]
    assert p["nivel_pct"] == 74.0
    assert p["actualizado"].endswith("-06:00")
    assert p["mensaje_es"] == "Cerrado" and p["mensaje_en"] == "Closed"


def test_estado_geojson_incluye_el_rio_para_dibujarlo(cruce):
    fc = estado_geojson(cruce, Estado.LIBRE, T0)
    [rio] = _por_tipo(fc, "rio")
    assert len(rio["geometry"]["coordinates"]) == 3


def test_google_solo_exporta_cierres_con_los_campos_obligatorios(cruce):
    g = GestorEpisodios(cruce.id)
    g.actualizar(Estado.CUIDADO, T0)
    g.actualizar(Estado.CERRADO, T0 + 300)
    fc = google_cierres_geojson(g.vigentes(T0 + 300), cruce)
    [f] = fc["features"]
    p = f["properties"]
    for campo in ("TYPE", "POLYLINE", "DIRECTION", "START_TIME", "END_TIME"):
        assert p[campo], f"falta {campo}"
    assert p["TYPE"] == "INCIDENT_ROAD_CLOSED"
    assert p["DIRECTION"] == "BOTH_DIRECTIONS"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?[+-]\d{2}:\d{2}$", p["START_TIME"])
    assert p["POLYLINE"].split()[:2] == ["9.910472", "-85.207366"]
    assert f["geometry"]["type"] == "LineString"
    assert p["ROAD_NAME"] == "Ruta 623"


def test_google_no_exporta_alertas_ni_cruces_peatonales(cruce):
    g = GestorEpisodios(cruce.id)
    g.actualizar(Estado.CUIDADO, T0)
    assert google_cierres_geojson(g.vigentes(T0), cruce)["features"] == []  # Google no tiene tipo "inundación"
    g.actualizar(Estado.CERRADO, T0 + 60)
    cruce.tipo_via = "peatonal"
    assert google_cierres_geojson(g.vigentes(T0 + 60), cruce)["features"] == []
