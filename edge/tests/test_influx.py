"""Tests de la escritura en InfluxDB: protocolo de líneas, cliente (2.x y 1.x), cola con reintentos
y lo que el borde manda (nivel, estado, fuente y latencias)."""

import asyncio
import time

import httpx

from app.config import Config
from app.estado import Decision, Estado
from app.influx import ClienteInflux, EscritorInflux, linea, puntos_estado, puntos_latencia
from app.sistema import Sistema


def config(tmp_path, **kw):
    base = dict(_env_file=None, camara_activa=False, mqtt_activo=False, imn_activo=False, nube_activa=False,
                modo_demo=True, datos_dir=str(tmp_path / "datos"), bajada_s=900)
    return Config(**{**base, **kw})


def transporte(respuestas, pedidos):
    """MockTransport que guarda cada pedido y responde con los códigos de la lista, en orden."""
    codigos = iter(respuestas)

    def manejar(req: httpx.Request) -> httpx.Response:
        pedidos.append(req)
        return httpx.Response(next(codigos))

    return httpx.MockTransport(manejar)


# --- Protocolo de líneas -------------------------------------------------------------

def test_linea_escapa_espacios_comas_e_iguales():
    l = linea("paso seguro", {"cruce": "vado 623,a=b"}, {"nota x": "ok"}, 1000)
    assert l == r'paso\ seguro,cruce=vado\ 623\,a\=b nota\ x="ok" 1000'


def test_linea_respeta_el_tipo_de_cada_campo():
    l = linea("m", {}, {"f": 37.5, "i": 2, "b": True, "s": 'di "hola" \\ chau'}, 5)
    assert l == r'm b=true,f=37.5,i=2i,s="di \"hola\" \\ chau" 5'


def test_linea_omite_campos_vacios_o_no_finitos_y_etiquetas_vacias():
    l = linea("m", {"cruce": "c1", "fuente": ""}, {"a": None, "b": float("nan"), "c": float("inf"), "d": 1.0}, 7)
    assert l == "m,cruce=c1 d=1.0 7"
    assert linea("m", {"cruce": "c1"}, {"a": None}, 7) is None  # sin campos no hay punto


# --- Qué se escribe --------------------------------------------------------------------

def test_puntos_estado_lleva_nivel_estado_y_fuente():
    d = Decision(estado=Estado.CUIDADO, anterior=Estado.LIBRE, cambio=True, objetivo=Estado.CUIDADO,
                 nivel=52.5, fuente="camara", tasa=12.0)
    assert puntos_estado(d, "vado-ruta-623", 1700000000000) == [
        "paso_seguro_estado,cruce=vado-ruta-623,fuente=camara "
        'degradado=false,discrepancia=false,estado="CUIDADO",estado_num=1i,nivel=52.5,tasa=12.0 1700000000000'
    ]


def test_el_nivel_entero_se_escribe_como_decimal_para_no_cambiar_el_tipo_del_campo():
    d = Decision(estado=Estado.CERRADO, anterior=Estado.CUIDADO, cambio=True, objetivo=Estado.CERRADO,
                 nivel=85, fuente="sensor", tasa=None)
    (l,) = puntos_estado(d, "c1", 1)
    assert "nivel=85.0" in l and "nivel=85i" not in l


def test_puntos_estado_sin_datos_no_inventa_el_nivel():
    d = Decision(estado=Estado.CUIDADO, anterior=Estado.CUIDADO, cambio=False, objetivo=Estado.CUIDADO,
                 nivel=None, fuente="ninguna", tasa=None, degradado=True)
    (l,) = puntos_estado(d, "c1", 1)
    assert l.startswith("paso_seguro_estado,cruce=c1,fuente=ninguna ")
    assert "nivel=" not in l and "tasa=" not in l and "degradado=true" in l


def test_puntos_latencia_solo_tramos_con_datos():
    resumen = {
        "captura_a_decision_ms": {"n": 120, "ultimo": 40.2, "p50": 37.1, "p95": 69.0, "min": 20.0, "max": 90.0},
        "cliente_rtt_ms:xr20-guia": {"n": 3, "ultimo": 21.0, "p50": 20.5, "p95": 25.0, "min": 19.0, "max": 25.0},
        "nube_rtt_ms": {"n": 0},
    }
    assert puntos_latencia(resumen, "c1", 9) == [
        "paso_seguro_latencia,cruce=c1,tramo=captura_a_decision_ms n=120i,p50=37.1,p95=69.0,ultimo=40.2 9",
        "paso_seguro_latencia,cruce=c1,tramo=cliente_rtt_ms:xr20-guia n=3i,p50=20.5,p95=25.0,ultimo=21.0 9",
    ]


# --- Cliente ---------------------------------------------------------------------------

def test_cliente_v2_manda_con_token_org_bucket_y_milisegundos():
    pedidos = []
    c = ClienteInflux("http://influx.local:8086/", bucket="paso_seguro", org="pcii", token="secreto-123",
                      transport=transporte([204], pedidos))
    asyncio.run(c.escribir(["m a=1.0 1", "m a=2.0 2"]))
    (r,) = pedidos
    assert r.method == "POST" and r.url.path == "/api/v2/write"
    assert dict(r.url.params) == {"org": "pcii", "bucket": "paso_seguro", "precision": "ms"}
    assert r.headers["authorization"] == "Token secreto-123"
    assert r.content == b"m a=1.0 1\nm a=2.0 2"


def test_cliente_v1_usa_la_base_y_no_pone_la_clave_en_la_url():
    pedidos = []
    c = ClienteInflux("http://influx.local:8086", bucket="paso_seguro", version="1", usuario="grupo6",
                      clave="clave-1", transport=transporte([204], pedidos))
    asyncio.run(c.escribir(["m a=1.0 1"]))
    (r,) = pedidos
    assert r.url.path == "/write"
    assert dict(r.url.params) == {"db": "paso_seguro", "precision": "ms"}
    assert "clave-1" not in str(r.url)
    assert r.headers["authorization"].startswith("Basic ")


# --- Cola con reintentos ------------------------------------------------------------------

def test_si_influx_falla_los_puntos_quedan_y_se_reintentan_en_orden():
    pedidos = []
    c = ClienteInflux("http://influx.local:8086", bucket="b", token="t", transport=transporte([500, 204], pedidos))
    e = EscritorInflux(c)
    e.agregar(["m a=1.0 1", "m a=2.0 2"])
    assert asyncio.run(e.enviar()) is False
    assert e.estado()["pendientes"] == 2 and e.estado()["ultimo_error"] == "HTTP 500"
    e.agregar(["m a=3.0 3"])
    assert asyncio.run(e.enviar()) is True
    assert pedidos[-1].content == b"m a=1.0 1\nm a=2.0 2\nm a=3.0 3"  # los viejos primero
    est = e.estado()
    assert est["pendientes"] == 0 and est["enviados"] == 3 and est["ok"] is True


def test_sin_red_el_borde_no_se_cae_y_guarda_los_puntos():
    def sin_red(req):
        raise httpx.ConnectError("sin red", request=req)

    e = EscritorInflux(ClienteInflux("http://influx.local:8086", bucket="b", token="t",
                                     transport=httpx.MockTransport(sin_red)))
    e.agregar(["m a=1.0 1"])
    assert asyncio.run(e.enviar()) is False
    assert e.estado()["pendientes"] == 1 and e.estado()["ultimo_error"] == "ConnectError"


def test_sin_pendientes_no_llama_a_influx():
    pedidos = []
    e = EscritorInflux(ClienteInflux("http://x:8086", bucket="b", token="t", transport=transporte([], pedidos)))
    assert asyncio.run(e.enviar()) is True and pedidos == []


def test_con_la_cola_llena_se_descartan_los_mas_viejos():
    e = EscritorInflux(ClienteInflux("http://x:8086", bucket="b", token="t"), max_pendientes=3)
    e.agregar([f"m a={i}.0 {i}" for i in range(5)])
    assert e.estado()["pendientes"] == 3 and e.estado()["descartados"] == 2
    assert list(e.pendientes) == ["m a=2.0 2", "m a=3.0 3", "m a=4.0 4"]


def test_el_estado_no_muestra_el_token_ni_la_clave():
    e = EscritorInflux(ClienteInflux("http://influx.local:8086", bucket="b", org="o", token="token-secreto",
                                     version="1", usuario="u", clave="clave-secreta"))
    texto = str(e.estado())
    assert "token-secreto" not in texto and "clave-secreta" not in texto
    assert e.estado()["destino"] == "influx.local"


# --- En el borde ---------------------------------------------------------------------------

def test_el_borde_sin_influx_no_cambia_nada(tmp_path):
    s = Sistema(config(tmp_path))
    assert s.influx is None
    assert s.snapshot()["influx"] == {"activo": False}


def test_influx_activo_sin_url_queda_apagado_y_lo_dice(tmp_path):
    s = Sistema(config(tmp_path, influx_activo=True, influx_url=""))
    assert s.influx is None
    info = s.snapshot()["influx"]
    assert info["activo"] is False and "INFLUX_URL" in info["error"]


def test_al_cambiar_de_estado_el_borde_encola_un_punto_al_instante(tmp_path):
    s = Sistema(config(tmp_path, influx_activo=True, influx_url="http://influx.local:8086", influx_token="t"))
    s.registrar_sensor({"id": "esp32", "nivel_pct": 85}, "http")
    lineas = list(s.influx.pendientes)
    assert any('estado="CERRADO"' in l and "fuente=sensor" in l and "nivel=85.0" in l for l in lineas)


def test_la_muestra_periodica_lleva_estado_y_latencias(tmp_path):
    s = Sistema(config(tmp_path, influx_activo=True, influx_url="http://influx.local:8086", influx_token="t"))
    s.lat.agregar("captura_a_decision_ms", 37.0)
    s.muestra_influx(time.time(), latencias=True)
    lineas = list(s.influx.pendientes)
    assert any(l.startswith("paso_seguro_estado,cruce=vado-ruta-623,") for l in lineas)
    assert any(l.startswith("paso_seguro_latencia,cruce=vado-ruta-623,tramo=captura_a_decision_ms ") for l in lineas)
