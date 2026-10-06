"""El tablero de Grafana tiene que leer las mismas mediciones, campos y umbrales que usa el borde."""

import importlib.util
import json

from app.config import BASE, Config
from app.influx import MEDICION_ESTADO, MEDICION_LATENCIA

GENERADOR = BASE.parent / "tools" / "grafana_tablero.py"


def _generador():
    spec = importlib.util.spec_from_file_location("grafana_tablero", GENERADOR)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _consultas(tablero: dict) -> str:
    return "\n".join(t["query"] for p in tablero["panels"] for t in p.get("targets", []))


def test_los_dos_tableros_leen_lo_que_escribe_el_borde():
    m = _generador()
    for lenguaje in ("flux", "influxql"):
        q = _consultas(m.tablero(lenguaje))
        assert MEDICION_ESTADO in q and MEDICION_LATENCIA in q
        for campo in ("nivel", "estado_num", "p50", "p95"):
            assert campo in q, (lenguaje, campo)


def test_el_estado_se_ve_con_nombre_y_color():
    panel = next(p for p in _generador().tablero("flux")["panels"] if p["type"] == "state-timeline")
    opciones = panel["fieldConfig"]["defaults"]["mappings"][0]["options"]
    assert {k: v["text"] for k, v in opciones.items()} == {"0": "LIBRE", "1": "CUIDADO", "2": "CERRADO"}


def test_los_umbrales_del_nivel_son_los_del_borde():
    panel = next(p for p in _generador().tablero("influxql")["panels"] if p["title"] == "Nivel del agua")
    pasos = [s["value"] for s in panel["fieldConfig"]["defaults"]["thresholds"]["steps"]]
    defecto = Config.model_fields
    assert pasos == [None, defecto["umbral_cuidado"].default, defecto["umbral_cerrado"].default]


def test_la_hora_es_la_de_costa_rica():
    assert _generador().tablero("flux")["timezone"] == "America/Costa_Rica"


def test_los_archivos_para_importar_estan_al_dia():
    m = _generador()
    for lenguaje, archivo in m.ARCHIVOS.items():
        assert json.loads(archivo.read_text(encoding="utf-8")) == m.tablero(lenguaje), (
            f"{archivo.name} está desactualizado: correr tools/grafana_tablero.py")
