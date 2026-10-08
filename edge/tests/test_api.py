"""Tests de la API del borde (sin cámara, sin MQTT, sin IMN y sin internet)."""

import json
import time
from pathlib import Path

import pytest
import xmlschema
from fastapi.testclient import TestClient

from app.config import Config
from app.main import crear_app
from app.mqtt_cliente import leer_mensaje_sensor

XSD = xmlschema.XMLSchema(str(Path(__file__).parent.parent / "app" / "feeds" / "cifsv2.xsd"))


def config(tmp_path, **kw):
    base = dict(
        _env_file=None,
        camara_activa=False,
        mqtt_activo=False,
        imn_activo=False,
        nube_activa=False,
        modo_demo=True,
        datos_dir=str(tmp_path / "datos"),
        bajada_s=1,
    )
    return Config(**{**base, **kw})


@pytest.fixture
def cliente(tmp_path):
    with TestClient(crear_app(config(tmp_path))) as c:
        yield c


def sensor(c, **kw):
    return c.post("/api/sensor", json={"id": "esp32-prueba", "nivel_pct": 10, "flotador": False, **kw})


def test_ping_devuelve_la_hora_del_servidor(cliente):
    t0 = time.time() * 1000
    r = cliente.get("/ping")
    assert r.status_code == 200
    assert abs(r.json()["t_srv"] - t0) < 5000


def test_sensor_bajo_deja_libre_y_responde_el_estado_al_esp32(cliente):
    r = sensor(cliente, nivel_pct=10).json()
    assert r["estado"] == "LIBRE"
    assert r["color"] == "VERDE"
    assert r["buzzer"] is False


def test_sensor_alto_cierra_y_aparece_en_todos_los_feeds(cliente):
    r = sensor(cliente, nivel_pct=85).json()
    assert (r["estado"], r["color"], r["buzzer"]) == ("CERRADO", "ROJO", True)
    waze = cliente.get("/feeds/waze.json").json()
    assert waze["incidents"][0]["type"] == "ROAD_CLOSED"
    xml = cliente.get("/feeds/waze.xml")
    assert xml.headers["content-type"].startswith("application/xml")
    XSD.validate(xml.text)
    geo = cliente.get("/feeds/estado.geojson").json()
    assert any(f["properties"].get("estado") == "CERRADO" for f in geo["features"])
    google = cliente.get("/feeds/google-cierres.geojson").json()
    assert len(google["features"]) == 1
    val = cliente.get("/feeds/validacion").json()
    assert val["waze_json"]["ok"] and val["waze_xml_xsd"]["ok"]


def test_feed_envuelto(cliente):
    sensor(cliente, nivel_pct=85)
    feed = cliente.get("/feeds/waze.json?envuelto=1").json()
    assert set(feed["incidents"][0]) == {"incident"}


def test_flotador_activado_cierra(cliente):
    assert sensor(cliente, nivel_pct=5, flotador=True).json()["estado"] == "CERRADO"


def test_el_cambio_de_estado_queda_como_evento_con_mensajes(cliente):
    sensor(cliente, nivel_pct=85)
    ev = cliente.get("/api/eventos").json()[0]
    assert ev["tipo"] == "cambio_estado"
    assert ev["estado"] == "CERRADO"
    assert ev["mensajes"]["en"] and ev["mensajes"]["es"]
    assert ev["t_evento_ms"] > 0


def test_estado_completo_para_el_tablero(cliente):
    sensor(cliente, nivel_pct=50)
    j = cliente.get("/api/estado").json()
    for clave in ("estado", "nivel", "fuente", "razones", "mensajes", "entradas", "umbrales", "imn", "nube"):
        assert clave in j
    assert j["estado"] == "CUIDADO"
    assert j["fuente"] == "sensor"


def test_cruce_para_el_mapa(cliente):
    c = cliente.get("/api/cruce").json()
    assert len(c["polilinea"]) >= 2 and c["calle"]


def test_cierre_manual_sube_y_al_quitarlo_no_reabre_de_golpe(cliente):
    sensor(cliente, nivel_pct=10)
    r = cliente.post("/api/manual", json={"estado": "CERRADO", "motivo": "derrumbe"}).json()
    assert r["estado"] == "CERRADO"
    cliente.post("/api/manual", json={"estado": None})
    assert cliente.get("/api/estado").json()["estado"] == "CERRADO"  # baja de a un escalón, con tiempo


def test_demo_inyecta_nivel_y_lluvia(cliente):
    assert cliente.post("/api/demo/nivel", json={"nivel_pct": 75}).json()["estado"] == "CERRADO"
    cliente.post("/api/demo/reiniciar")
    assert cliente.get("/api/estado").json()["estado"] in ("LIBRE", "CUIDADO")
    sensor(cliente, nivel_pct=10)
    r = cliente.post("/api/demo/lluvia", json={"mm_1h": 40.4}).json()
    assert r["estado"] == "CUIDADO"


def test_sin_modo_demo_no_hay_inyeccion(tmp_path):
    with TestClient(crear_app(config(tmp_path, modo_demo=False))) as c:
        assert c.post("/api/demo/nivel", json={"nivel_pct": 75}).status_code == 404


def test_ack_del_guia_mide_la_entrega_de_la_alerta(cliente):
    sensor(cliente, nivel_pct=85)
    ev = cliente.get("/api/eventos").json()[0]
    r = cliente.post(f"/api/alertas/{ev['id']}/ack",
                     json={"cliente": "guia-xr20", "t_recibido_ms": ev["t_evento_ms"] + 40}).json()
    assert r["entrega_ms"] == pytest.approx(40, abs=1)
    assert "alerta_entrega_ms" in cliente.get("/api/latencia").json()


def test_ack_de_alerta_inexistente_da_404(cliente):
    assert cliente.post("/api/alertas/nada/ack", json={"cliente": "x"}).status_code == 404


def test_latencias_de_clientes_y_del_esp32(cliente):
    cliente.post("/api/latencia/cliente", json={"cliente": "guia-xr20", "rtt_ms": [12.5, 14.0, 11.2]})
    sensor(cliente, rtt_ms=21)
    lat = cliente.get("/api/latencia").json()
    assert lat["cliente_rtt_ms:guia-xr20"]["n"] == 3
    assert lat["esp32_rtt_ms"]["ultimo"] == 21


def test_stream_sse_manda_el_estado_al_conectarse(cliente):
    with cliente.stream("GET", "/api/stream?max_eventos=1") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        datos = [json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:")]
    assert datos and "estado" in datos[0]


def test_paginas_del_tablero(cliente):
    for ruta in ("/", "/guia", "/turista", "/calibrar", "/medir"):
        r = cliente.get(ruta)
        assert r.status_code == 200 and "<html" in r.text.lower(), ruta


def test_medir_manda_200_muestras_con_el_nombre_de_la_red(cliente):
    # La página /medir manda cada tanda de 200 muestras como cliente «<id>-<red>-<destino>».
    r = cliente.post("/api/latencia/cliente", json={"cliente": "xr20-4g-nube", "rtt_ms": [40.0] * 200})
    assert r.json() == {"ok": True, "n": 200}
    assert cliente.get("/api/latencia").json()["cliente_rtt_ms:xr20-4g-nube"]["n"] == 200


def test_sin_camara_el_video_avisa(cliente):
    assert cliente.get("/api/camara/captura.jpg").status_code == 503


def test_mensaje_mqtt_del_sensor():
    d = leer_mensaje_sensor("pasoseguro/esp32-1/sensor", b'{"nivel_pct": 80, "flotador": false}', "pasoseguro")
    assert d == {"id": "esp32-1", "nivel_pct": 80, "flotador": False}
    assert leer_mensaje_sensor("pasoseguro/esp32-1/otro", b"{}", "pasoseguro") is None
    assert leer_mensaje_sensor("pasoseguro/esp32-1/sensor", b"no es json", "pasoseguro") is None
