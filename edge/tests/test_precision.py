"""La medición de precisión (5 marcas × 10 lecturas) tiene que dar el error en mm y en puntos de nivel."""

import importlib.util

from app.config import BASE

HERRAMIENTA = BASE.parent / "tools" / "medir_precision.py"


def _herramienta():
    spec = importlib.util.spec_from_file_location("medir_precision", HERRAMIENTA)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_marca_sin_error():
    r = _herramienta().resumen_marca(500, [498, 502, 505, 495, 500], d0=800, d100=300)
    assert r["n"] == 5 and r["promedio_mm"] == 500
    assert r["error_mm"] == 0 and r["error_pts"] == 0
    assert r["desvio_mm"] > 0


def test_error_en_puntos_usa_el_rango_de_la_calibracion():
    # 20 mm de error sobre un rango de 500 mm (800 → 300) son 4 puntos de nivel.
    r = _herramienta().resumen_marca(400, [420] * 10, d0=800, d100=300)
    assert r["error_mm"] == 20 and r["error_pts"] == 4.0


def test_informe_cumple_si_ninguna_marca_pasa_de_5_puntos():
    m = _herramienta()
    bien = [m.resumen_marca(400, [410] * 10, 800, 300), m.resumen_marca(600, [590] * 10, 800, 300)]
    assert m.informe(bien)["cumple"] is True
    mal = bien + [m.resumen_marca(500, [530] * 10, 800, 300)]  # 30 mm = 6 puntos
    inf = m.informe(mal)
    assert inf["cumple"] is False and inf["peor_pts"] == 6.0


def test_marca_sin_lecturas_no_rompe():
    r = _herramienta().resumen_marca(500, [], 800, 300)
    assert r["n"] == 0 and r["error_pts"] is None
