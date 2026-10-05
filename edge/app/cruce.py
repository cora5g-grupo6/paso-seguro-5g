"""Cruce vigilado: se carga de config/cruce.json.

Coordenadas en WGS84, siempre como [latitud, longitud] (el orden que usa CIFS).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

LatLon = tuple[float, float]


@dataclass
class Cruce:
    id: str
    nombre: str
    rio: str
    lugar: str = ""
    tipo_via: str = "vehicular"  # "vehicular" se publica en Waze; "peatonal" no (la spec no lo admite)
    calle: str = ""  # nombre de la vía tal como aparece en Waze (street)
    direccion: str = "BOTH_DIRECTIONS"
    punto: LatLon = (0.0, 0.0)
    polilinea: list[LatLon] = field(default_factory=list)  # tramo afectado, en el sentido del tránsito
    rio_linea: list[LatLon] = field(default_factory=list)  # solo para dibujar el mapa
    ruta_alterna_es: str = "No cruce. Espere en un lugar alto o regrese por donde vino."
    ruta_alterna_en: str = "Do not cross. Wait on high ground or turn back."
    regla_cm: float = 30.0  # alto de la regla pintada en la maqueta
    equipos: list[dict] = field(default_factory=list)  # [{"tipo", "nombre", "punto"}]
    coordenadas_confirmadas: bool = False
    nota: str = ""
    atribucion: str = ""

    @property
    def publica_en_waze(self) -> bool:
        return self.tipo_via == "vehicular" and len(self.polilinea) >= 2 and len(self.calle) >= 2

    @property
    def rio_en_frase(self) -> str:
        """'Río Vainilla' -> 'río Vainilla' (para usarlo dentro de una frase)."""
        primera, _, resto = self.rio.partition(" ")
        if primera in ("Río", "Quebrada", "Cañón", "Riachuelo"):
            return f"{primera.lower()} {resto}".strip()
        return self.rio

    def a_dict(self) -> dict:
        d = asdict(self)
        d["publica_en_waze"] = self.publica_en_waze
        return d


def cargar_cruce(ruta: str | Path) -> Cruce:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    validos = {f.name for f in fields(Cruce)}
    desconocidos = [k for k in datos if k not in validos and not k.startswith("_")]
    if desconocidos:
        raise ValueError(f"{ruta}: campos desconocidos {desconocidos}")
    datos = {k: v for k, v in datos.items() if k in validos}
    datos["punto"] = tuple(datos.get("punto", (0.0, 0.0)))
    for clave in ("polilinea", "rio_linea"):
        datos[clave] = [tuple(p) for p in datos.get(clave, [])]
    return Cruce(**datos)
