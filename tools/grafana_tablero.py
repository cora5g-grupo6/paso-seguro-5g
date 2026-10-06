#!/usr/bin/env python3
"""Genera los tableros de Grafana para la historia que el borde escribe en InfluxDB.

Uso (desde tools/):
  ../edge/.venv/bin/python grafana_tablero.py

Escribe un archivo por lenguaje de consulta. En Grafana: Dashboards → New → Import, subir el que
corresponda a la fuente de datos InfluxDB configurada y elegirla al importar:
  grafana/paso-seguro-flux.json      InfluxDB 2.x y Cloud (Flux)
  grafana/paso-seguro-influxql.json  InfluxDB 1.x y 3.x (InfluxQL)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "edge"))

from app.config import BASE, Config  # noqa: E402
from app.cruce import cargar_cruce  # noqa: E402
from app.influx import MEDICION_ESTADO, MEDICION_LATENCIA  # noqa: E402

ARCHIVOS = {
    "flux": AQUI / "grafana" / "paso-seguro-flux.json",
    "influxql": AQUI / "grafana" / "paso-seguro-influxql.json",
}
DEFECTO = Config.model_fields
CUIDADO = DEFECTO["umbral_cuidado"].default
CERRADO = DEFECTO["umbral_cerrado"].default
BUCKET = DEFECTO["influx_bucket"].default
CRUCE = cargar_cruce(BASE / DEFECTO["cruce_archivo"].default).id
COLORES = {"LIBRE": "#1d6c3a", "CUIDADO": "#f1c40f", "CERRADO": "#c0392b"}  # los del semáforo del ESP32
AZUL = "#2b78b5"
FUENTE = {"type": "influxdb", "uid": "${DS_INFLUXDB}"}  # Grafana pide elegir la fuente al importar

MAPEO_ESTADO = [{"type": "value", "options": {
    "0": {"text": "LIBRE", "color": COLORES["LIBRE"], "index": 0},
    "1": {"text": "CUIDADO", "color": COLORES["CUIDADO"], "index": 1},
    "2": {"text": "CERRADO", "color": COLORES["CERRADO"], "index": 2},
}}]
PASOS_ESTADO = {"mode": "absolute", "steps": [
    {"color": COLORES["LIBRE"], "value": None},
    {"color": COLORES["CUIDADO"], "value": 1},
    {"color": COLORES["CERRADO"], "value": 2},
]}
PASOS_NIVEL = {"mode": "absolute", "steps": [
    {"color": COLORES["LIBRE"], "value": None},
    {"color": COLORES["CUIDADO"], "value": CUIDADO},
    {"color": COLORES["CERRADO"], "value": CERRADO},
]}
VENTANA_MAX = "aggregateWindow(every: v.windowPeriod, fn: max, createEmpty: false)"
VENTANA_PROM = "aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"


def _flux(medicion: str, campos: list[str], final: str, filtro: str = "", agrupar: str = '"_field"') -> str:
    # se agrupa por campo para juntar las series de cada fuente (cámara o sensor) en una sola línea
    campos_txt = " or ".join(f'r._field == "{c}"' for c in campos)
    return (
        'from(bucket: "${bucket}")\n'
        "  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n"
        f'  |> filter(fn: (r) => r._measurement == "{medicion}" and r.cruce == "${{cruce}}"{filtro})\n'
        f"  |> filter(fn: (r) => {campos_txt})\n"
        f"  |> group(columns: [{agrupar}])\n"
        '  |> sort(columns: ["_time"])\n'
        f"  |> {final}"
    )


def _influxql(select: str, medicion: str, filtro: str = "", agrupar: str = "") -> str:
    q = f'SELECT {select} FROM "{medicion}" WHERE "cruce" =~ /^$cruce$/{filtro} AND $timeFilter'
    return q + (f" GROUP BY {agrupar}" if agrupar else "")


def _consultas(flux: bool) -> dict[str, str]:
    if flux:
        return {
            "estado_ultimo": _flux(MEDICION_ESTADO, ["estado_num"], "last()"),
            "nivel_ultimo": _flux(MEDICION_ESTADO, ["nivel"], "last()"),
            "camara": _flux(MEDICION_LATENCIA, ["p50"], "last()", ' and r.tramo == "captura_a_decision_ms"'),
            "guia": _flux(MEDICION_LATENCIA, ["p50"], "last()", " and r.tramo =~ /^cliente_rtt_ms/", '"tramo"'),
            "nivel": _flux(MEDICION_ESTADO, ["nivel"], VENTANA_MAX),
            "estado": _flux(MEDICION_ESTADO, ["estado_num"], VENTANA_MAX),
            "latencias": _flux(MEDICION_LATENCIA, ["p50", "p95"], VENTANA_PROM, agrupar='"tramo", "_field"'),
        }
    por_tiempo = "time($__interval) fill(none)"
    return {
        "estado_ultimo": _influxql('last("estado_num") AS "estado"', MEDICION_ESTADO),
        "nivel_ultimo": _influxql('last("nivel") AS "nivel"', MEDICION_ESTADO),
        "camara": _influxql('last("p50") AS "p50"', MEDICION_LATENCIA, " AND \"tramo\" = 'captura_a_decision_ms'"),
        "guia": _influxql('last("p50") AS "p50"', MEDICION_LATENCIA, ' AND "tramo" =~ /^cliente_rtt_ms/', '"tramo"'),
        "nivel": _influxql('max("nivel") AS "nivel"', MEDICION_ESTADO, agrupar=por_tiempo),
        "estado": _influxql('max("estado_num") AS "estado"', MEDICION_ESTADO, agrupar=por_tiempo),
        "latencias": _influxql('mean("p50") AS "p50", mean("p95") AS "p95"', MEDICION_LATENCIA,
                               agrupar='time($__interval), "tramo" fill(none)'),
    }


def _objetivo(flux: bool, consulta: str, alias: str = "") -> dict:
    t = {"refId": "A", "datasource": FUENTE, "query": consulta}
    if not flux:
        t.update(rawQuery=True, resultFormat="time_series")
        if alias:
            t["alias"] = alias
    return t


def _panel(id_: int, tipo: str, titulo: str, pos: tuple[int, int, int, int], objetivo: dict,
           defaults: dict, opciones: dict, descripcion: str = "") -> dict:
    x, y, w, h = pos
    return {
        "id": id_, "type": tipo, "title": titulo, "description": descripcion,
        "gridPos": {"x": x, "y": y, "w": w, "h": h}, "datasource": FUENTE, "targets": [objetivo],
        "fieldConfig": {"defaults": defaults, "overrides": []}, "options": opciones,
    }


def _stat(modo_color: str) -> dict:
    return {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": modo_color, "graphMode": "none", "justifyMode": "center", "textMode": "value",
            "orientation": "auto"}


def tablero(lenguaje: str) -> dict:
    flux = lenguaje == "flux"
    q = _consultas(flux)
    ms = {"unit": "ms", "decimals": 1, "color": {"mode": "fixed", "fixedColor": AZUL}}
    paneles = [
        _panel(1, "stat", "Estado actual", (0, 0, 6, 5), _objetivo(flux, q["estado_ultimo"]),
               {"mappings": MAPEO_ESTADO, "thresholds": PASOS_ESTADO, "color": {"mode": "thresholds"}},
               _stat("background")),
        _panel(2, "gauge", "Nivel actual", (6, 0, 6, 5), _objetivo(flux, q["nivel_ultimo"]),
               {"unit": "percent", "min": 0, "max": 100, "decimals": 0, "thresholds": PASOS_NIVEL,
                "color": {"mode": "thresholds"}},
               {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                "showThresholdMarkers": True, "showThresholdLabels": False}),
        _panel(3, "stat", "Cámara → decisión (p50)", (12, 0, 6, 5), _objetivo(flux, q["camara"]), ms,
               _stat("value"), "Del cuadro de la cámara a la decisión del borde."),
        _panel(4, "stat", "Teléfono del guía ↔ borde (p50)", (18, 0, 6, 5),
               _objetivo(flux, q["guia"], alias="$tag_tramo"),
               {**ms, **({"displayName": "${__field.labels.tramo}"} if flux else {})},
               _stat("value"), "Ida y vuelta medida desde la página del guía (XR20). Es el número 5G del pitch."),
        _panel(5, "timeseries", "Nivel del agua", (0, 5, 24, 9), _objetivo(flux, q["nivel"], alias="nivel"),
               {"unit": "percent", "min": 0, "max": 110, "thresholds": PASOS_NIVEL,
                "color": {"mode": "fixed", "fixedColor": AZUL},
                "custom": {"lineWidth": 2, "fillOpacity": 10, "spanNulls": True,
                           "thresholdsStyle": {"mode": "line+area"}}},
               {"legend": {"showLegend": False}, "tooltip": {"mode": "single"}},
               f"Máximo por intervalo. CUIDADO desde {CUIDADO} % y CERRADO desde {CERRADO} %."),
        _panel(6, "state-timeline", "Estado del cruce", (0, 14, 24, 5), _objetivo(flux, q["estado"], alias="estado"),
               {"mappings": MAPEO_ESTADO, "thresholds": PASOS_ESTADO, "color": {"mode": "thresholds"}},
               {"mergeValues": True, "showValue": "auto", "rowHeight": 0.9, "legend": {"showLegend": False}}),
        _panel(7, "timeseries", "Latencia por tramo (p50 y p95)", (0, 19, 24, 9),
               _objetivo(flux, q["latencias"], alias="$tag_tramo · $col"),
               {"unit": "ms", "min": 0, "custom": {"lineWidth": 1, "fillOpacity": 0, "spanNulls": True},
                **({"displayName": "${__field.labels.tramo} · ${__field.labels._field}"} if flux else {})},
               {"legend": {"displayMode": "table", "placement": "right", "calcs": ["lastNotNull", "max"]},
                "tooltip": {"mode": "multi"}}),
    ]

    variables = []
    if flux:
        variables.append({"name": "bucket", "label": "Bucket", "type": "textbox", "query": BUCKET, "hide": 0,
                          "current": {"text": BUCKET, "value": BUCKET},
                          "options": [{"selected": True, "text": BUCKET, "value": BUCKET}]})
        consulta_cruce = ('import "influxdata/influxdb/schema"\n'
                          f'schema.tagValues(bucket: "${{bucket}}", tag: "cruce", '
                          f'predicate: (r) => r._measurement == "{MEDICION_ESTADO}", start: -30d)')
    else:
        consulta_cruce = f'SHOW TAG VALUES FROM "{MEDICION_ESTADO}" WITH KEY = "cruce"'
    variables.append({"name": "cruce", "label": "Cruce", "type": "query", "datasource": FUENTE,
                      "query": consulta_cruce, "definition": consulta_cruce, "refresh": 1, "sort": 1, "hide": 0,
                      "current": {"text": CRUCE, "value": CRUCE}, "options": [], "includeAll": False,
                      "multi": False})

    return {
        "__inputs": [{"name": "DS_INFLUXDB", "label": "InfluxDB", "description": "", "type": "datasource",
                      "pluginId": "influxdb", "pluginName": "InfluxDB"}],
        "__requires": [{"type": "datasource", "id": "influxdb", "name": "InfluxDB", "version": "1.0.0"}],
        "title": f"Paso Seguro 5G ({'Flux' if flux else 'InfluxQL'})",
        "uid": f"paso-seguro-5g-{lenguaje}",
        "description": "Historia del cruce que el borde de Paso Seguro 5G escribe en InfluxDB",
        "tags": ["paso-seguro", "5g", "hackaton"],
        "timezone": "America/Costa_Rica",
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "5s",
        "schemaVersion": 39,
        "version": 1,
        "editable": True,
        "graphTooltip": 1,
        "templating": {"list": variables},
        "annotations": {"list": []},
        "panels": paneles,
    }


def main() -> None:
    for lenguaje, archivo in ARCHIVOS.items():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(json.dumps(tablero(lenguaje), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Escrito {archivo.relative_to(AQUI.parent)}")


if __name__ == "__main__":
    main()
