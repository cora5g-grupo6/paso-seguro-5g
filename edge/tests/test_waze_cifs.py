"""Tests del feed CIFS de Waze (Closure and Incident Feed Specification).

Fuentes (leídas el 5-oct-2026):
- https://developers.google.com/waze/data-feed/cifs-specification
- https://developers.google.com/waze/data-feed/road-closure-information
- https://www.gstatic.com/road-incidents/cifsv2.xsd  (copia sin cambios en app/feeds/)
"""

import re
from datetime import datetime
from pathlib import Path

import pytest
import xmlschema

from app.cruce import Cruce, cargar_cruce
from app.estado import Estado
from app.feeds.waze import (
    GestorEpisodios,
    feed_cifs_json,
    feed_cifs_xml,
    iso,
    validar_cifs,
    ZONA_CR,
)

AQUI = Path(__file__).parent
XSD = xmlschema.XMLSchema(str(AQUI.parent / "app" / "feeds" / "cifsv2.xsd"))
CONFIG = AQUI.parent / "config" / "cruce.json"

# Formato exigido por la spec: yyyy-MM-dd'T'HH:mm:ss+HH:mm (segundos y zona horaria)
FORMATO_HORA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
OBLIGATORIOS = ("id", "type", "polyline", "street", "starttime")  # tabla "CIFS Elements"
T0 = datetime(2026, 10, 9, 9, 0, 0, tzinfo=ZONA_CR).timestamp()  # viernes del pitch
HORA = 3600.0


@pytest.fixture
def cruce():
    return Cruce(
        id="vado-prueba",
        nombre="Vado de prueba",
        rio="Río Vainilla",
        lugar="Lepanto, Puntarenas",
        tipo_via="vehicular",
        calle="Ruta 623",
        direccion="BOTH_DIRECTIONS",
        punto=(9.908952, -85.206468),
        polilinea=[
            (9.910472, -85.207366),
            (9.909622, -85.206588),
            (9.908952, -85.206468),
            (9.908089, -85.206299),
            (9.907315, -85.207280),
        ],
    )


def gestor(cruce, **kw):
    return GestorEpisodios(cruce.id, **kw)


def incidentes(feed):
    return feed["incidents"]


# --- Feed vacío y campos obligatorios --------------------------------------

def test_sin_crecida_el_feed_queda_vacio_y_es_valido(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.LIBRE, T0)
    feed = feed_cifs_json(g.vigentes(T0), cruce)
    assert feed == {"incidents": []}
    assert validar_cifs(feed).ok
    XSD.validate(feed_cifs_xml(g.vigentes(T0), cruce, T0))


def test_cerrado_genera_road_closed_con_todos_los_campos_obligatorios(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    [inc] = incidentes(feed_cifs_json(g.vigentes(T0), cruce))
    for campo in OBLIGATORIOS:
        assert inc.get(campo), f"falta {campo}"
    assert inc["type"] == "ROAD_CLOSED"
    assert inc["subtype"] == "ROAD_CLOSED_HAZARD"
    assert inc["direction"] == "BOTH_DIRECTIONS"
    assert inc["street"] == "Ruta 623"
    assert inc["description"]  # el XSD la exige
    assert inc["endtime"]  # "requested": sin ella Waze asume 14 días


def test_cuidado_genera_alerta_de_inundacion(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CUIDADO, T0)
    [inc] = incidentes(feed_cifs_json(g.vigentes(T0), cruce))
    assert (inc["type"], inc["subtype"]) == ("HAZARD", "HAZARD_WEATHER_FLOOD")


def test_horas_con_segundos_y_zona_horaria_de_costa_rica(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    [inc] = incidentes(feed_cifs_json(g.vigentes(T0), cruce))
    for campo in ("starttime", "endtime", "creationtime", "updatetime"):
        assert FORMATO_HORA.match(inc[campo]), inc[campo]
        assert inc[campo].endswith("-06:00")
    assert inc["starttime"] == "2026-10-09T09:00:00-06:00"


def test_polilinea_lat_lon_separada_por_espacios_con_6_decimales(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    [inc] = incidentes(feed_cifs_json(g.vigentes(T0), cruce))
    numeros = inc["polyline"].split(" ")
    assert len(numeros) == 2 * len(cruce.polilinea)
    assert all(re.match(r"^-?\d+\.\d{6}$", n) for n in numeros)
    assert numeros[:2] == ["9.910472", "-85.207366"]  # latitud primero


def test_id_alfanumerico_unico_y_de_al_menos_3_caracteres(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CUIDADO, T0)
    g.actualizar(Estado.CERRADO, T0 + 60)
    ids = [i["id"] for i in incidentes(feed_cifs_json(g.vigentes(T0 + 60), cruce))]
    assert len(ids) == 2 and len(set(ids)) == 2
    assert all(re.match(r"^[A-Za-z0-9]{3,}$", i) for i in ids)


# --- XSD oficial -------------------------------------------------------------

def test_xml_valida_contra_el_xsd_oficial_de_waze(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CUIDADO, T0)
    g.actualizar(Estado.CERRADO, T0 + 120)
    xml = feed_cifs_xml(g.vigentes(T0 + 120), cruce, T0 + 120)
    XSD.validate(xml)  # lanza excepción si no cumple
    assert xml.count("<incident ") == 2
    assert "<type>ROAD_CLOSED</type>" in xml
    assert "cifsv2.xsd" in xml


def test_xml_escapa_caracteres_especiales(cruce):
    cruce.calle = 'Ruta 623 "Vainilla" & <Lepanto>'
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    XSD.validate(feed_cifs_xml(g.vigentes(T0), cruce, T0))


# --- Ciclo de vida del cierre ------------------------------------------------

def test_id_y_starttime_estables_mientras_dura_el_cierre(cruce):
    g = gestor(cruce)
    vistos = set()
    for k in range(0, 600, 30):
        g.actualizar(Estado.CERRADO, T0 + k)
        [inc] = incidentes(feed_cifs_json(g.vigentes(T0 + k), cruce))
        vistos.add((inc["id"], inc["starttime"]))
    assert len(vistos) == 1  # la spec pide no cambiar un starttime ya activo


def test_endtime_se_extiende_por_bloques_y_no_con_la_hora_actual(cruce):
    g = gestor(cruce, bloque_s=3 * HORA, margen_s=30 * 60)
    finales = set()
    for minuto in range(0, 8 * 60, 5):  # 8 horas cerrado
        t = T0 + minuto * 60
        g.actualizar(Estado.CERRADO, t)
        [inc] = incidentes(feed_cifs_json(g.vigentes(t), cruce))
        finales.add(inc["endtime"])
    esperados = {iso(T0 + k * 3 * HORA) for k in (1, 2, 3)}
    assert finales == esperados  # solo saltos de 3 h: 12:00, 15:00 y 18:00


def test_al_reabrir_queda_endtime_fijo_y_sale_del_feed_tras_la_retencion(cruce):
    g = gestor(cruce, retencion_s=HORA)
    g.actualizar(Estado.CERRADO, T0)
    reapertura = T0 + 2 * HORA
    g.actualizar(Estado.LIBRE, reapertura)
    [inc] = incidentes(feed_cifs_json(g.vigentes(reapertura + 59 * 60), cruce))
    assert inc["endtime"] == iso(reapertura)
    g.actualizar(Estado.LIBRE, reapertura + 61 * 60)
    assert incidentes(feed_cifs_json(g.vigentes(reapertura + 61 * 60), cruce)) == []


def test_pasar_de_cuidado_a_cerrado_termina_la_alerta_y_abre_el_cierre(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CUIDADO, T0)
    g.actualizar(Estado.CERRADO, T0 + 300)
    alerta, cierre = incidentes(feed_cifs_json(g.vigentes(T0 + 300), cruce))
    assert alerta["type"] == "HAZARD" and alerta["endtime"] == iso(T0 + 300)
    assert cierre["type"] == "ROAD_CLOSED" and cierre["starttime"] == iso(T0 + 300)


def test_un_episodio_de_menos_de_un_segundo_no_queda_en_el_feed(cruce):
    # CUIDADO y CERRADO en el mismo segundo: el CUIDADO tendría endtime == starttime (inválido)
    g = gestor(cruce)
    g.actualizar(Estado.CUIDADO, T0 + 0.2)
    g.actualizar(Estado.CERRADO, T0 + 0.7)
    feed = feed_cifs_json(g.vigentes(T0 + 1), cruce)
    assert [i["type"] for i in incidentes(feed)] == ["ROAD_CLOSED"]
    assert validar_cifs(feed).ok


def test_si_no_se_puede_guardar_el_archivo_el_feed_sigue(cruce, tmp_path):
    estorbo = tmp_path / "no_es_carpeta"
    estorbo.write_text("x")  # un archivo donde debería ir una carpeta: no se puede escribir
    g = GestorEpisodios(cruce.id, archivo=estorbo / "episodios.json")
    g.actualizar(Estado.CERRADO, T0)  # no debe lanzar excepción
    assert incidentes(feed_cifs_json(g.vigentes(T0), cruce))[0]["type"] == "ROAD_CLOSED"


def test_cruce_peatonal_no_se_publica_en_waze(cruce):
    cruce.tipo_via = "peatonal"  # la spec no admite cierres en vías peatonales
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    assert incidentes(feed_cifs_json(g.vigentes(T0), cruce)) == []


# --- Validador ---------------------------------------------------------------

def _feed_valido(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    return feed_cifs_json(g.vigentes(T0), cruce)


def test_el_feed_generado_pasa_el_validador_sin_errores(cruce):
    r = validar_cifs(_feed_valido(cruce), bbox=(5.0, -88.0, 12.0, -82.0))
    assert r.ok, r.errores


@pytest.mark.parametrize("campo", ["id", "type", "polyline", "street", "description"])
def test_validador_detecta_campo_obligatorio_faltante(cruce, campo):
    feed = _feed_valido(cruce)
    del feed["incidents"][0][campo]
    r = validar_cifs(feed)
    assert not r.ok
    assert any(campo in e for e in r.errores)


def test_validador_exige_starttime_en_cierres(cruce):
    feed = _feed_valido(cruce)
    del feed["incidents"][0]["starttime"]
    assert any("starttime" in e for e in validar_cifs(feed).errores)


def test_validador_detecta_subtipo_que_no_corresponde_al_tipo(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"][0]["subtype"] = "HAZARD_WEATHER_FLOOD"  # con type ROAD_CLOSED
    assert any("subtype" in e for e in validar_cifs(feed).errores)


def test_validador_detecta_hora_sin_zona_horaria(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"][0]["starttime"] = "2026-10-09T09:00:00"
    assert any("starttime" in e for e in validar_cifs(feed).errores)


def test_validador_detecta_endtime_anterior_al_inicio(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"][0]["endtime"] = "2026-10-09T08:00:00-06:00"
    assert any("endtime" in e for e in validar_cifs(feed).errores)


def test_validador_detecta_lat_lon_invertidas_con_la_caja_del_pais(cruce):
    feed = _feed_valido(cruce)
    pares = feed["incidents"][0]["polyline"].split(" ")
    invertida = " ".join(f"{pares[i + 1]} {pares[i]}" for i in range(0, len(pares), 2))
    feed["incidents"][0]["polyline"] = invertida
    r = validar_cifs(feed, bbox=(5.0, -88.0, 12.0, -82.0))
    assert any("polyline" in e for e in r.errores)


def test_validador_rechaza_cierre_de_un_solo_punto(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"][0]["polyline"] = "9.908952 -85.206468"
    assert any("polyline" in e for e in validar_cifs(feed).errores)


def test_validador_avisa_si_la_descripcion_pasa_de_40_caracteres(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"][0]["description"] = "x" * 41
    r = validar_cifs(feed)
    assert r.ok  # se acepta, pero puede verse mal en la app
    assert any("40" in a for a in r.avisos)


def test_validador_detecta_ids_repetidos(cruce):
    feed = _feed_valido(cruce)
    feed["incidents"].append(dict(feed["incidents"][0]))
    assert any("id" in e for e in validar_cifs(feed).errores)


def test_formato_envuelto_de_la_documentacion_tambien_se_genera_y_valida(cruce):
    g = gestor(cruce)
    g.actualizar(Estado.CERRADO, T0)
    feed = feed_cifs_json(g.vigentes(T0), cruce, envuelto=True)
    assert set(feed["incidents"][0]) == {"incident"}
    assert validar_cifs(feed).ok


# --- Cruce configurado ---------------------------------------------------------

def test_polilinea_del_cruce_configurado_cumple_las_guias_de_waze():
    c = cargar_cruce(CONFIG)
    g = GestorEpisodios(c.id)
    g.actualizar(Estado.CERRADO, T0)
    feed = feed_cifs_json(g.vigentes(T0), c)
    r = validar_cifs(feed, bbox=(5.0, -88.0, 12.0, -82.0))
    assert r.ok, r.errores
    assert not [a for a in r.avisos if "30 m" in a or "20 km" in a]
    assert len(c.polilinea) >= 3  # Waze pide seguir la forma de la vía
    XSD.validate(feed_cifs_xml(g.vigentes(T0), c, T0))
