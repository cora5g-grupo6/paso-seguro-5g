"""GeoJSON del estado del cruce y exportador para Google Maps Content Partners (GMCP).

Google Maps (leído el 5-oct-2026 en https://support.google.com/mapcontentpartners/answer/144284):
- Los cierres que entran a Waze por el feed CIFS se propagan solos a Google Maps:
  15-25 min para uno nuevo y hasta 1-2 h para un cambio. Ese es el camino en tiempo real.
- Para cargar cierres puntuales directo en GMCP, Google acepta GeoJSON/JSON/XML con
  TYPE, POLYLINE, DIRECTION, START_TIME y END_TIME obligatorios (ID, ROAD_NAME,
  DESCRIPTION y SOURCE opcionales). No hay tipo para inundación: solo se exportan los CERRADO.
"""

from __future__ import annotations

from app.cruce import Cruce
from app.estado import Estado
from app.feeds.waze import Episodio, descripcion, iso, polilinea_cifs

COLORES = {Estado.LIBRE: "#1e8e3e", Estado.CUIDADO: "#f9ab00", Estado.CERRADO: "#d93025"}
AZUL_RIO = "#1a73e8"


def _lonlat(p) -> list[float]:
    return [p[1], p[0]]  # GeoJSON (RFC 7946) usa [longitud, latitud]


def estado_geojson(
    cruce: Cruce,
    estado: Estado,
    t: float,
    nivel: float | None = None,
    fuente: str | None = None,
    razones: list[str] | None = None,
    mensajes: dict | None = None,
) -> dict:
    color = COLORES[estado]
    mensajes = mensajes or {}
    feats = [
        {
            "type": "Feature",
            "id": cruce.id,
            "geometry": {"type": "Point", "coordinates": _lonlat(cruce.punto)},
            "properties": {
                "tipo": "cruce",
                "cruce_id": cruce.id,
                "nombre": cruce.nombre,
                "rio": cruce.rio,
                "lugar": cruce.lugar,
                "estado": str(estado),
                "color": color,
                "nivel_pct": nivel,
                "fuente_nivel": fuente,
                "razones": razones or [],
                "actualizado": iso(t),
                "mensaje_es": mensajes.get("es"),
                "mensaje_en": mensajes.get("en"),
                "marker-color": color,  # simplestyle: se ve en geojson.io y similares
            },
        }
    ]
    if len(cruce.polilinea) >= 2:
        feats.append(
            {
                "type": "Feature",
                "id": f"{cruce.id}-tramo",
                "geometry": {"type": "LineString", "coordinates": [_lonlat(p) for p in cruce.polilinea]},
                "properties": {
                    "tipo": "tramo",
                    "cruce_id": cruce.id,
                    "calle": cruce.calle,
                    "estado": str(estado),
                    "color": color,
                    "stroke": color,
                    "stroke-width": 6,
                },
            }
        )
    if len(cruce.rio_linea) >= 2:
        feats.append(
            {
                "type": "Feature",
                "id": f"{cruce.id}-rio",
                "geometry": {"type": "LineString", "coordinates": [_lonlat(p) for p in cruce.rio_linea]},
                "properties": {"tipo": "rio", "cruce_id": cruce.id, "nombre": cruce.rio,
                               "stroke": AZUL_RIO, "stroke-width": 3},
            }
        )
    return {"type": "FeatureCollection", "features": feats}


def google_cierres_geojson(episodios: list[Episodio], cruce: Cruce) -> dict:
    """Cierres en el esquema de carga puntual de GMCP (solo CERRADO y solo vías vehiculares)."""
    feats = []
    if cruce.publica_en_waze:
        for ep in sorted(episodios, key=lambda e: e.inicio):
            if ep.estado != Estado.CERRADO:
                continue
            feats.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [_lonlat(p) for p in cruce.polilinea]},
                    "properties": {
                        "ID": ep.id,
                        "TYPE": "INCIDENT_ROAD_CLOSED",
                        "POLYLINE": polilinea_cifs(cruce.polilinea),
                        "DIRECTION": cruce.direccion,
                        "START_TIME": iso(ep.inicio),
                        "END_TIME": iso(ep.fin if ep.fin is not None else ep.fin_estimado),
                        "ROAD_NAME": cruce.calle,
                        "DESCRIPTION": descripcion(Estado.CERRADO, cruce),
                        "SOURCE": "Paso Seguro 5G (prototipo)",
                    },
                }
            )
    return {"type": "FeatureCollection", "features": feats}
