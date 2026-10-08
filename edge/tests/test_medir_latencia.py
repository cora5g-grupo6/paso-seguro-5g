"""medir_latencia.py --guia: toma la entrega del aviso que el teléfono del guía confirmó (ack) para el cierre recién disparado."""

import importlib.util

from app.config import BASE

HERRAMIENTA = BASE.parent / "tools" / "medir_latencia.py"


def _herramienta():
    spec = importlib.util.spec_from_file_location("medir_latencia", HERRAMIENTA)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ev(t, estado="CERRADO", acks=()):
    return {"id": f"e{t}", "estado": estado, "t_evento_ms": t, "acks": [{"cliente": c, "entrega_ms": ms} for c, ms in acks]}


def test_toma_el_ack_del_guia_en_el_cierre_nuevo():
    eventos = [ev(2000, acks=[("tablero", 5.0), ("xr20", 41.5)]), ev(1000, acks=[("xr20", 99.0)])]
    assert _herramienta().entrega_guia(eventos, "xr20", desde_ms=1500) == 41.5


def test_ignora_cierres_viejos_y_otros_estados():
    eventos = [ev(2000, estado="CUIDADO", acks=[("xr20", 30.0)]), ev(1000, acks=[("xr20", 99.0)])]
    assert _herramienta().entrega_guia(eventos, "xr20", desde_ms=1500) is None


def test_sin_ack_del_guia_todavia():
    assert _herramienta().entrega_guia([ev(2000, acks=[("tablero", 5.0)])], "xr20", desde_ms=1500) is None
