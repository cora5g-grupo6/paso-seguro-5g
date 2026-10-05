"""Tests del despachador de alertas y de las estadísticas de latencia."""

import asyncio
import json

import httpx
import pytest

from app.alertas import Despachador, N8nPrueba, PttStub, Webhook, es_url_de_prueba
from app.latencia import Estadistica, Latencias

ALERTA = {"id": "ev1", "tipo": "cambio_estado", "estado": "CERRADO", "mensaje_es": "Cruce cerrado"}


def ok(_request):
    return httpx.Response(200)


# --- Latencia ----------------------------------------------------------------

def test_estadistica_calcula_percentiles():
    e = Estadistica()
    for v in range(1, 101):
        e.agregar(v)
    r = e.resumen()
    assert r["n"] == 100
    assert r["p50"] == pytest.approx(50.5, abs=1)
    assert r["p95"] == pytest.approx(95, abs=1.5)
    assert r["max"] == 100 and r["ultimo"] == 100


def test_estadistica_guarda_solo_la_ventana():
    e = Estadistica(ventana=10)
    for v in range(100):
        e.agregar(v)
    assert e.resumen()["n"] == 10
    assert e.resumen()["min"] == 90


def test_latencias_por_nombre():
    lat = Latencias()
    lat.agregar("vision_ms", 5)
    assert lat.resumen()["vision_ms"]["ultimo"] == 5


# --- Adaptadores ---------------------------------------------------------------

def test_webhook_envia_el_json_de_la_alerta():
    recibido = []

    def servidor(request):
        recibido.append(json.loads(request.content))
        return httpx.Response(200)

    w = Webhook(["http://receptor.prueba/hook"], transport=httpx.MockTransport(servidor))
    r = asyncio.run(w.enviar(ALERTA))
    assert r["ok"]
    assert recibido[0]["id"] == "ev1"


def test_n8n_viene_apagado_por_defecto():
    llamadas = []

    def servidor(request):
        llamadas.append(request)
        return httpx.Response(200)

    n = N8nPrueba(url="https://n8n.ejemplo/webhook/paso-seguro-prueba", transport=httpx.MockTransport(servidor))
    assert not n.activo
    asyncio.run(Despachador([n], Latencias()).despachar(ALERTA))
    assert llamadas == []


def test_n8n_rechaza_una_url_que_no_es_de_prueba():
    n = N8nPrueba(url="https://n8n.ejemplo/webhook/lia-produccion", activo=True, transport=httpx.MockTransport(ok))
    r = asyncio.run(n.enviar(ALERTA))
    assert not r["ok"]
    assert "prueba" in r["detalle"]


@pytest.mark.parametrize(
    "url, es_prueba",
    [
        ("https://n8n.ejemplo/webhook/paso-seguro-prueba", True),
        ("https://n8n.ejemplo/webhook-test/9f2c", True),  # así son las URL de prueba de n8n
        ("https://n8n.ejemplo/webhook/test/alerta", True),
        ("https://n8n.ejemplo/webhook/alertas-latest", False),  # "test" dentro de otra palabra
        ("https://n8n.ejemplo/aprueba-cierre", False),  # "prueba" dentro de otra palabra
        ("https://n8n.ejemplo/webhook/prueba/../produccion", False),  # httpx lo normaliza a producción
        ("https://prueba.ejemplo/webhook/produccion", False),  # solo cuenta la ruta, no el dominio
    ],
)
def test_guardia_de_n8n_reconoce_solo_urls_de_prueba(url, es_prueba):
    assert es_url_de_prueba(url) is es_prueba


def test_n8n_de_prueba_envia_y_marca_la_alerta_como_prueba():
    recibido = []

    def servidor(request):
        recibido.append(json.loads(request.content))
        return httpx.Response(200)

    n = N8nPrueba(url="https://n8n.ejemplo/webhook/paso-seguro-prueba", activo=True,
                  transport=httpx.MockTransport(servidor))
    r = asyncio.run(n.enviar(ALERTA))
    assert r["ok"]
    assert recibido[0]["prueba"] is True


def test_ptt_stub_deja_la_alerta_en_cola_y_avisa_que_falta_la_api(tmp_path):
    p = PttStub(tmp_path / "ptt.jsonl", activo=True)
    r = asyncio.run(p.enviar(ALERTA))
    assert not r["ok"]
    assert "API" in r["detalle"]
    guardada = json.loads((tmp_path / "ptt.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert guardada["id"] == "ev1"


def test_despachador_mide_cada_envio_y_sigue_si_uno_falla():
    def caido(_request):
        raise httpx.ConnectError("caído")

    lat = Latencias()
    d = Despachador(
        [
            Webhook(["http://a.prueba/x"], transport=httpx.MockTransport(ok)),
            Webhook(["http://b.prueba/x"], transport=httpx.MockTransport(caido), nombre="webhook-b"),
        ],
        lat,
    )
    res = asyncio.run(d.despachar(ALERTA))
    assert [r["ok"] for r in res] == [True, False]
    assert "alerta_envio_ms:webhook" in lat.resumen()
