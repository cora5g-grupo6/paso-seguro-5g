"""Tests del orquestador: reinicios, datos raros y fallas de disco (hallazgos de la revisión)."""

import time

from fastapi.testclient import TestClient

from app.config import Config
from app.estado import Estado
from app.feeds.waze import GestorEpisodios
from app.main import crear_app
from app.sistema import Sistema


def config(tmp_path, **kw):
    base = dict(_env_file=None, camara_activa=False, mqtt_activo=False, imn_activo=False, nube_activa=False,
                modo_demo=True, datos_dir=str(tmp_path / "datos"), bajada_s=900)
    return Config(**{**base, **kw})


# --- Reinicio con un cierre activo -------------------------------------------------

def test_al_reiniciar_el_borde_retoma_el_cierre_guardado(tmp_path):
    cfg = config(tmp_path)
    antes = GestorEpisodios("vado-ruta-623", archivo=tmp_path / "datos" / "episodios.json")
    antes.actualizar(Estado.CERRADO, time.time() - 120)  # estaba cerrado hace 2 min y el borde se reinició

    s = Sistema(cfg)
    assert s.decision.estado == Estado.CERRADO
    r = s.registrar_sensor({"id": "esp32", "nivel_pct": 30}, "http")
    assert r["estado"] == "CERRADO"  # no reabre de golpe: sigue la regla de bajada (900 s)
    assert s.episodios.activo is not None and s.episodios.activo.estado == Estado.CERRADO


def test_reiniciar_en_modo_demo_cierra_el_episodio_en_vez_de_borrarlo(tmp_path):
    antes = GestorEpisodios("vado-ruta-623", archivo=tmp_path / "datos" / "episodios.json")
    antes.actualizar(Estado.CERRADO, time.time() - 120)  # cerrado desde hace 2 min
    s = Sistema(config(tmp_path))
    s.reiniciar()
    feed = s.feed_waze_json()["incidents"]
    assert len(feed) == 1 and feed[0]["endtime"]  # queda con hora de fin fija, como pide Waze
    assert s.episodios.activo is None


# --- Falla de disco -------------------------------------------------------------------

def test_si_no_se_puede_escribir_en_disco_la_alerta_sale_igual(tmp_path):
    estorbo = tmp_path / "datos"
    estorbo.mkdir()
    s = Sistema(config(tmp_path))
    s.episodios.archivo = tmp_path / "es_un_archivo" / "episodios.json"
    (tmp_path / "es_un_archivo").write_text("x")
    r = s.registrar_sensor({"id": "esp32", "nivel_pct": 85}, "http")
    assert r["estado"] == "CERRADO"
    assert s.eventos and s.eventos[0]["estado"] == "CERRADO"


# --- Datos raros por la API -------------------------------------------------------------

def _cliente(tmp_path):
    return TestClient(crear_app(config(tmp_path)))


def test_nan_en_el_nivel_se_rechaza(tmp_path):
    with _cliente(tmp_path) as c:
        r = c.post("/api/sensor", content='{"id": "x", "nivel_pct": NaN}', headers={"content-type": "application/json"})
        assert r.status_code == 422


def test_nan_en_un_campo_extra_no_congela_el_tablero(tmp_path):
    with _cliente(tmp_path) as c:
        r = c.post("/api/sensor", content='{"id": "x", "nivel_pct": 10, "rssi": NaN, "modo": "local"}',
                   headers={"content-type": "application/json"})
        assert r.status_code == 200
        assert c.get("/api/estado").status_code == 200
        assert c.get("/api/latencia").status_code == 200


def test_ack_con_hora_nan_se_rechaza(tmp_path):
    with _cliente(tmp_path) as c:
        c.post("/api/sensor", json={"id": "x", "nivel_pct": 85})
        eid = c.get("/api/eventos").json()[0]["id"]
        r = c.post(f"/api/alertas/{eid}/ack", content='{"cliente": "g", "t_recibido_ms": NaN}',
                   headers={"content-type": "application/json"})
        assert r.status_code == 422
        assert c.get("/api/latencia").status_code == 200


def test_calibracion_con_datos_incompletos_se_rechaza(tmp_path):
    with _cliente(tmp_path) as c:
        r = c.post("/api/camara/calibracion",
                   json={"roi": [1, 2, 3, 4], "y_cero": 400, "y_cien": 60, "punto_agua": [5, 5], "ref_roi": [1, 2]})
        assert r.status_code == 422
