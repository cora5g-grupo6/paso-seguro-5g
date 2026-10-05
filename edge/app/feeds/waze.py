"""Feed CIFS para Waze for Cities (JSON y XML) y su validador.

Fuentes leídas el 5-oct-2026:
- Spec:  https://developers.google.com/waze/data-feed/cifs-specification
- Guías: https://developers.google.com/waze/data-feed/road-closure-information
- XSD:   https://www.gstatic.com/road-incidents/cifsv2.xsd

Decisiones:
- CERRADO -> type ROAD_CLOSED / subtype ROAD_CLOSED_HAZARD: cierre total, Waze cambia rutas.
- CUIDADO -> type HAZARD / subtype HAZARD_WEATHER_FLOOD: alerta en el mapa, no cambia rutas.
- Cada episodio (tramo continuo en CUIDADO o CERRADO) es un incidente con id estable.
- starttime = inicio del episodio y no se toca después (la spec lo pide para cierres activos).
- endtime mientras dura: bloque fijo (3 h por defecto) que se extiende de a un bloque cuando
  falta poco. No se recalcula con la hora actual (la spec lo pide) y, si el borde se cae,
  el cierre vence solo en horas y no a los 14 días que Waze asume sin endtime.
- Al reabrir: endtime = hora real de reapertura, y el incidente sigue en el feed
  `retencion_s` (1 h) para que Waze lo lea antes de quitarlo.
- Formato JSON: el "plano" de los ejemplos completos ({"incidents": [{...}]}).
  Con envuelto=True sale el otro que también aparece en la documentación
  ({"incidents": [{"incident": {...}}]}).
"""

from __future__ import annotations

import json
import logging
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.cruce import Cruce
from app.estado import Estado

try:
    from zoneinfo import ZoneInfo

    ZONA_CR = ZoneInfo("America/Costa_Rica")
except Exception:  # sin base de zonas horarias: Costa Rica no tiene horario de verano
    ZONA_CR = timezone(timedelta(hours=-6), "CST")

log = logging.getLogger("paso_seguro.feeds")
XSD_URL = "http://www.gstatic.com/road-incidents/cifsv2.xsd"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

TIPOS = {"ROAD_CLOSED", "ACCIDENT", "HAZARD", "POLICE", "CHIT_CHAT", "JAM", "CONSTRUCTION"}
SUBTIPOS = {
    "ACCIDENT": {"ACCIDENT_MINOR", "ACCIDENT_MAJOR"},
    "HAZARD": {
        "HAZARD_ON_ROAD", "HAZARD_ON_ROAD_CAR_STOPPED", "HAZARD_ON_ROAD_CONSTRUCTION",
        "HAZARD_ON_ROAD_EMERGENCY_VEHICLE", "HAZARD_ON_ROAD_ICE", "HAZARD_ON_ROAD_LANE_CLOSED",
        "HAZARD_ON_ROAD_OBJECT", "HAZARD_ON_ROAD_OIL", "HAZARD_ON_ROAD_POT_HOLE",
        "HAZARD_ON_ROAD_ROAD_KILL", "HAZARD_ON_ROAD_TRAFFIC_LIGHT_FAULT", "HAZARD_ON_SHOULDER",
        "HAZARD_ON_SHOULDER_ANIMALS", "HAZARD_ON_SHOULDER_CAR_STOPPED",
        "HAZARD_ON_SHOULDER_MISSING_SIGN", "HAZARD_WEATHER", "HAZARD_WEATHER_FLOOD",
        "HAZARD_WEATHER_FOG", "HAZARD_WEATHER_FREEZING_RAIN", "HAZARD_WEATHER_HAIL",
        "HAZARD_WEATHER_HEAT_WAVE", "HAZARD_WEATHER_HEAVY_RAIN", "HAZARD_WEATHER_HEAVY_SNOW",
        "HAZARD_WEATHER_HURRICANE", "HAZARD_WEATHER_MONSOON", "HAZARD_WEATHER_TORNADO",
    },
    "ROAD_CLOSED": {"ROAD_CLOSED_HAZARD", "ROAD_CLOSED_CONSTRUCTION", "ROAD_CLOSED_EVENT"},
    "JAM": {"JAM_LIGHT_TRAFFIC", "JAM_MODERATE_TRAFFIC", "JAM_HEAVY_TRAFFIC", "JAM_STAND_STILL_TRAFFIC"},
    "POLICE": {"POLICE_VISIBLE", "POLICE_HIDING", "POLICE_WITH_MOBILE_CAMERA"},
}
FORMATO_HORA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
CAJA_CR = (5.0, -88.0, 12.0, -82.0)  # lat_min, lon_min, lat_max, lon_max (incluye la Isla del Coco)


def iso(t: float, zona=ZONA_CR) -> str:
    """Epoch -> '2026-10-09T09:00:00-06:00' (segundos y zona horaria, como pide CIFS)."""
    return datetime.fromtimestamp(t, zona).isoformat(timespec="seconds")


def distancia_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


# --- Episodios ---------------------------------------------------------------

@dataclass
class Episodio:
    id: str
    estado: Estado
    inicio: float
    fin_estimado: float
    actualizado: float
    fin: float | None = None

    @property
    def activo(self) -> bool:
        return self.fin is None


class GestorEpisodios:
    """Convierte la secuencia de estados del cruce en incidentes estables para los feeds."""

    def __init__(
        self,
        cruce_id: str,
        bloque_s: float = 3 * 3600,
        margen_s: float = 30 * 60,
        retencion_s: float = 3600,
        archivo: str | Path | None = None,
    ):
        self.prefijo = "PS" + re.sub(r"[^A-Za-z0-9]", "", cruce_id).upper()[:16]
        self.bloque_s = bloque_s
        self.margen_s = margen_s
        self.retencion_s = retencion_s
        self.archivo = Path(archivo) if archivo else None
        self.episodios: list[Episodio] = []
        self._cargar()

    @property
    def activo(self) -> Episodio | None:
        return next((e for e in reversed(self.episodios) if e.activo), None)

    def actualizar(self, estado: Estado, t: float) -> bool:
        """Registra el estado actual. Devuelve True si cambió algún episodio."""
        cambio = False
        act = self.activo
        if act and (estado == Estado.LIBRE or act.estado != estado):
            act.fin = t
            act.actualizado = t
            if int(act.fin) <= int(act.inicio):
                # duró menos de un segundo: en CIFS quedaría endtime == starttime (inválido)
                self.episodios.remove(act)
            act = None
            cambio = True
        if estado != Estado.LIBRE:
            if act is None:
                self.episodios.append(
                    Episodio(
                        id=self._nuevo_id(estado, t),
                        estado=estado,
                        inicio=t,
                        fin_estimado=t + self.bloque_s,
                        actualizado=t,
                    )
                )
                cambio = True
            else:
                while act.fin_estimado - t <= self.margen_s:
                    act.fin_estimado += self.bloque_s
                    act.actualizado = t
                    cambio = True
        antes = len(self.episodios)
        self.episodios = [e for e in self.episodios if e.activo or t - e.fin <= self.retencion_s]
        cambio = cambio or len(self.episodios) != antes
        if cambio:
            self._guardar()
        return cambio

    def vigentes(self, t: float) -> list[Episodio]:
        return [e for e in self.episodios if e.activo or t - e.fin <= self.retencion_s]

    def _nuevo_id(self, estado: Estado, t: float) -> str:
        base = f"{self.prefijo}{'C' if estado == Estado.CERRADO else 'A'}{int(t)}"
        usados = {e.id for e in self.episodios}
        candidato, n = base, 1
        while candidato in usados:
            n += 1
            candidato = f"{base}N{n}"
        return candidato

    def _guardar(self) -> None:
        if not self.archivo:
            return
        try:
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            datos = [{**asdict(e), "estado": str(e.estado)} for e in self.episodios]
            tmp = self.archivo.with_suffix(".tmp")
            tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.archivo)
        except OSError as e:  # disco lleno o sin permisos: el feed en memoria y las alertas siguen
            log.warning("No se pudo guardar %s: %s", self.archivo, e)

    def _cargar(self) -> None:
        if not self.archivo or not self.archivo.exists():
            return
        try:
            datos = json.loads(self.archivo.read_text(encoding="utf-8"))
            self.episodios = [Episodio(**{**d, "estado": Estado(d["estado"])}) for d in datos]
        except (ValueError, KeyError, TypeError):
            self.episodios = []  # archivo dañado: se empieza de cero


# --- Generación ----------------------------------------------------------------

def polilinea_cifs(puntos) -> str:
    return " ".join(f"{lat:.6f} {lon:.6f}" for lat, lon in puntos)


def descripcion(estado: Estado, cruce: Cruce) -> str:
    """Texto corto para Waze (la spec recomienda menos de 40 caracteres)."""
    if estado == Estado.CERRADO:
        larga, corta = f"Cerrado: crecida del {cruce.rio_en_frase}", "Cerrado por crecida del río"
    else:
        larga, corta = f"Precaución: crece el {cruce.rio_en_frase}", "Río crecido: precaución"
    return larga if len(larga) < 40 else corta


def incidente_cifs(ep: Episodio, cruce: Cruce) -> dict:
    cerrado = ep.estado == Estado.CERRADO
    return {
        "id": ep.id,
        "type": "ROAD_CLOSED" if cerrado else "HAZARD",
        "subtype": "ROAD_CLOSED_HAZARD" if cerrado else "HAZARD_WEATHER_FLOOD",
        "description": descripcion(ep.estado, cruce),
        "street": cruce.calle,
        "direction": cruce.direccion,
        "polyline": polilinea_cifs(cruce.polilinea),
        "starttime": iso(ep.inicio),
        "endtime": iso(ep.fin if ep.fin is not None else ep.fin_estimado),
        "creationtime": iso(ep.inicio),
        "updatetime": iso(ep.actualizado),
    }


def feed_cifs_json(episodios: list[Episodio], cruce: Cruce, envuelto: bool = False) -> dict:
    if not cruce.publica_en_waze:
        return {"incidents": []}
    incs = [incidente_cifs(e, cruce) for e in sorted(episodios, key=lambda e: e.inicio)]
    if envuelto:
        return {"incidents": [{"incident": i} for i in incs]}
    return {"incidents": incs}


def feed_cifs_xml(episodios: list[Episodio], cruce: Cruce, t_generado: float) -> str:
    ET.register_namespace("xsi", XSI)
    raiz = ET.Element("incidents", {f"{{{XSI}}}noNamespaceSchemaLocation": XSD_URL, "timestamp": iso(t_generado)})
    for inc in feed_cifs_json(episodios, cruce)["incidents"]:
        nodo = ET.SubElement(raiz, "incident", {"id": inc["id"]})
        for clave in ("creationtime", "updatetime", "type", "subtype", "description", "street",
                      "direction", "polyline", "starttime", "endtime"):
            ET.SubElement(nodo, clave).text = inc[clave]
    ET.indent(raiz)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"


# --- Validación ------------------------------------------------------------------

@dataclass
class ResultadoValidacion:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errores

    def a_dict(self) -> dict:
        return {"ok": self.ok, "errores": self.errores, "avisos": self.avisos}


def _leer_polyline(valor, pre: str, errores: list[str]) -> list[tuple[float, float]] | None:
    if not valor or not str(valor).strip():
        errores.append(f"{pre}: falta polyline")
        return None
    partes = str(valor).split()
    try:
        numeros = [float(p) for p in partes]
    except ValueError:
        errores.append(f"{pre}: polyline tiene valores que no son números")
        return None
    if len(numeros) % 2:
        errores.append(f"{pre}: polyline necesita pares 'lat lon'")
        return None
    return [(numeros[i], numeros[i + 1]) for i in range(0, len(numeros), 2)]


def validar_cifs(feed: dict, bbox: tuple[float, float, float, float] | None = None) -> ResultadoValidacion:
    """Revisa un feed JSON contra la spec CIFS (campos, formatos y guías de cierres)."""
    r = ResultadoValidacion()
    if not isinstance(feed, dict) or not isinstance(feed.get("incidents"), list):
        r.errores.append("Falta la lista 'incidents' en la raíz")
        return r
    vistos: set[str] = set()
    for i, item in enumerate(feed["incidents"]):
        inc = item["incident"] if isinstance(item, dict) and set(item) == {"incident"} else item
        if not isinstance(inc, dict):
            r.errores.append(f"Evento {i + 1}: no es un objeto")
            continue
        pre = f"Evento {i + 1}"

        iid = inc.get("id")
        if iid in (None, ""):
            r.errores.append(f"{pre}: falta id")
        else:
            iid = str(iid)
            pre = f"Evento {iid}"
            if len(iid) < 3:
                r.errores.append(f"{pre}: el id debe tener al menos 3 caracteres (XSD)")
            if not re.fullmatch(r"[A-Za-z0-9]+", iid):
                r.avisos.append(f"{pre}: la spec pide un id alfanumérico")
            if iid in vistos:
                r.errores.append(f"{pre}: id repetido en el feed")
            vistos.add(iid)

        tipo = inc.get("type")
        if not tipo:
            r.errores.append(f"{pre}: falta type")
        elif tipo not in TIPOS:
            r.errores.append(f"{pre}: type '{tipo}' no existe en la spec")
        sub = inc.get("subtype")
        if sub:
            if tipo in SUBTIPOS and sub not in SUBTIPOS[tipo]:
                r.errores.append(f"{pre}: subtype '{sub}' no corresponde a type '{tipo}'")
        else:
            r.avisos.append(f"{pre}: falta subtype (recomendado)")

        calle = inc.get("street")
        if not calle or len(str(calle).strip()) < 2:
            r.errores.append(f"{pre}: falta street (mínimo 2 caracteres)")
        desc = inc.get("description")
        if not desc:
            r.errores.append(f"{pre}: falta description (el XSD la exige)")
        elif len(str(desc)) > 40:
            r.avisos.append(f"{pre}: description de {len(desc)} caracteres; la spec recomienda menos de 40")

        direc = inc.get("direction")
        if direc is not None and direc not in ("BOTH_DIRECTIONS", "ONE_DIRECTION"):
            r.errores.append(f"{pre}: direction '{direc}' no es BOTH_DIRECTIONS ni ONE_DIRECTION")

        puntos = _leer_polyline(inc.get("polyline"), pre, r.errores)
        if puntos is not None:
            if len(puntos) == 1:
                if tipo == "ROAD_CLOSED":
                    r.errores.append(f"{pre}: la polyline de un cierre necesita al menos 2 puntos")
                elif direc is None:
                    r.errores.append(f"{pre}: con un solo punto en la polyline, direction es obligatorio")
            elif direc is None:
                r.avisos.append(f"{pre}: falta direction (muy recomendado)")
            fuera = [p for p in puntos if not (-90 <= p[0] <= 90 and -180 <= p[1] <= 180)]
            if fuera:
                r.errores.append(f"{pre}: polyline con coordenadas fuera de rango: {fuera[0]}")
            elif bbox and any(not (bbox[0] <= la <= bbox[2] and bbox[1] <= lo <= bbox[3]) for la, lo in puntos):
                r.errores.append(f"{pre}: polyline fuera del área esperada (¿latitud y longitud invertidas?)")
            if any(len(p.split(".")[-1]) < 6 if "." in p else True for p in str(inc["polyline"]).split()):
                r.avisos.append(f"{pre}: la spec recomienda al menos 6 decimales por coordenada")
            if len(puntos) >= 2:
                largo = sum(distancia_m(puntos[k], puntos[k + 1]) for k in range(len(puntos) - 1))
                extremos = distancia_m(puntos[0], puntos[-1])
                if largo > 20000:
                    r.errores.append(f"{pre}: polyline de {largo / 1000:.1f} km; Waze no acepta más de 20 km")
                if len(puntos) > 2 and extremos < 5 and largo > 30:
                    r.errores.append(f"{pre}: polyline circular (Waze la rechaza)")
                elif tipo == "ROAD_CLOSED" and extremos < 30:
                    r.avisos.append(f"{pre}: inicio y fin a {extremos:.0f} m; Waze recomienda al menos 30 m")

        for campo in ("starttime", "endtime", "creationtime", "updatetime"):
            v = inc.get(campo)
            if v is not None and not FORMATO_HORA.match(str(v)):
                r.errores.append(f"{pre}: {campo} '{v}' no tiene el formato yyyy-MM-ddTHH:mm:ss±HH:mm")
        if tipo == "ROAD_CLOSED" and not inc.get("starttime"):
            r.errores.append(f"{pre}: falta starttime (obligatorio en cierres)")
        if not inc.get("endtime"):
            r.avisos.append(f"{pre}: sin endtime Waze asume 14 días desde el inicio")
        ini, fin = inc.get("starttime"), inc.get("endtime")
        if ini and fin and FORMATO_HORA.match(str(ini)) and FORMATO_HORA.match(str(fin)):
            if datetime.fromisoformat(fin) <= datetime.fromisoformat(ini):
                r.errores.append(f"{pre}: endtime no es posterior a starttime")
    return r
