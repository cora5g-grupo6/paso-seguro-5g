"""Cliente del IMN: API WIS2 / OGC API Features en http://wis2box.imn.ac.cr/oapi

Verificado llamando a la API el 5-oct-2026:
- Colecciones: discovery-metadata, stations, messages y
  urn:wmo:md:cr-imn:core.surface-based-observations.synop (observaciones SYNOP).
- 8 estaciones: aeropuertos Juan Santamaría, Tobías Bolaños, Daniel Oduber y Limón,
  más Comando Los Chiles, Finca La Ceiba, Sixaola y Coto 49. Solo http.
- La lluvia llega como name = total_precipitation_or_total_water_equivalent en kg m-2 (= mm),
  un dato por reporte horario; phenomenonTime es el intervalo de 1 h ("inicio/fin").
- Hay que ordenar con sortby=-reportTime: con -phenomenonTime el servidor responde error.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import httpx

URL_IMN = "http://wis2box.imn.ac.cr/oapi"
COLECCION_SYNOP = "urn:wmo:md:cr-imn:core.surface-based-observations.synop"
NOMBRE_LLUVIA = "total_precipitation_or_total_water_equivalent"


class IMNError(Exception):
    """El IMN no respondió o respondió algo que no se puede leer."""


@dataclass
class Estacion:
    id: str
    nombre: str
    lat: float
    lon: float
    alt: float | None = None


@dataclass
class ResumenLluvia:
    estacion_id: str
    estacion: str = ""
    mm_1h: float = 0.0
    mm_3h: float = 0.0
    mm_24h: float = 0.0
    max_1h: float = 0.0
    t_max: float | None = None
    t_ultimo: float = 0.0
    horas: list[tuple[str, float]] = field(default_factory=list)  # (reportTime, mm), más reciente primero
    distancia_km: float | None = None

    def a_dict(self) -> dict:
        return asdict(self)


def _ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def _iso_utc(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _horas_del_periodo(pt: str | None) -> float | None:
    if pt and "/" in pt:
        a, b = pt.split("/", 1)
        return (_ts(b) - _ts(a)) / 3600
    return None


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def parsear_estaciones(geojson: dict) -> list[Estacion]:
    out = []
    for f in geojson.get("features", []):
        p = f.get("properties") or {}
        c = (f.get("geometry") or {}).get("coordinates") or []
        if len(c) < 2:
            continue
        out.append(
            Estacion(
                id=p.get("wigos_station_identifier") or f.get("id"),
                nombre=p.get("name", ""),
                lat=float(c[1]),
                lon=float(c[0]),
                alt=float(c[2]) if len(c) > 2 and c[2] is not None else None,
            )
        )
    return out


def estacion_mas_cercana(estaciones: list[Estacion], lat: float, lon: float) -> tuple[Estacion, float]:
    return min(((e, distancia_km(lat, lon, e.lat, e.lon)) for e in estaciones), key=lambda x: x[1])


def parsear_lluvia(geojson: dict, estacion_id: str, hasta: float | None = None,
                   nombre_estacion: str = "") -> ResumenLluvia | None:
    """Resume la lluvia horaria de una estación. `hasta` (epoch) permite repetir el pasado."""
    datos: dict[float, float] = {}
    for f in geojson.get("features", []):
        p = f.get("properties") or {}
        if p.get("wigos_station_identifier") != estacion_id or p.get("name") != NOMBRE_LLUVIA:
            continue
        try:
            t, v = _ts(p["reportTime"]), float(p["value"])
        except (KeyError, TypeError, ValueError):
            continue
        periodo = _horas_del_periodo(p.get("phenomenonTime"))
        if periodo is not None and abs(periodo - 1) > 0.01:
            continue  # solo acumulados de 1 h
        if hasta is not None and t > hasta:
            continue
        datos[t] = v
    if not datos:
        return None
    serie = sorted(datos.items(), reverse=True)
    t_ult = serie[0][0]

    def suma(horas: int) -> float:
        return round(sum(v for t, v in serie if t > t_ult - horas * 3600 + 1), 2)

    t_max, v_max = max(serie, key=lambda x: (x[1], x[0]))
    return ResumenLluvia(
        estacion_id=estacion_id,
        estacion=nombre_estacion,
        mm_1h=round(serie[0][1], 2),
        mm_3h=suma(3),
        mm_24h=suma(24),
        max_1h=round(v_max, 2),
        t_max=t_max if v_max > 0 else None,
        t_ultimo=t_ult,
        horas=[(_iso_utc(t), round(v, 2)) for t, v in serie[:48]],
    )


class ClienteIMN:
    def __init__(self, base: str = URL_IMN, timeout: float = 20.0, transport: httpx.AsyncBaseTransport | None = None):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    async def _get(self, ruta: str, params: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as c:
                r = await c.get(f"{self.base}{ruta}", params=params)
                r.raise_for_status()
                return r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise IMNError(f"El IMN no respondió bien ({type(e).__name__}: {e})") from e

    async def estaciones(self) -> list[Estacion]:
        return parsear_estaciones(await self._get("/collections/stations/items", {"f": "json", "limit": 100}))

    async def lluvia(self, estacion_id: str, horas: int = 48, nombre: str = "") -> ResumenLluvia | None:
        datos = await self._get(
            f"/collections/{COLECCION_SYNOP}/items",
            {
                "f": "json",
                "limit": horas + 4,
                "sortby": "-reportTime",
                "wigos_station_identifier": estacion_id,
                "name": NOMBRE_LLUVIA,
            },
        )
        return parsear_lluvia(datos, estacion_id, nombre_estacion=nombre)

    async def lluvia_todas(self, estaciones: list[Estacion], horas: int = 48) -> list[ResumenLluvia]:
        """Una sola consulta para todas las estaciones (para la tabla del tablero)."""
        datos = await self._get(
            f"/collections/{COLECCION_SYNOP}/items",
            {"f": "json", "limit": horas * len(estaciones) + 40, "sortby": "-reportTime", "name": NOMBRE_LLUVIA},
        )
        out = []
        for e in estaciones:
            r = parsear_lluvia(datos, e.id, nombre_estacion=e.nombre)
            if r:
                out.append(r)
        return out
