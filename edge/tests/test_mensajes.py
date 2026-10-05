"""Tests de los mensajes para turista (ES/EN) y para el guía."""

import pytest

from app.cruce import Cruce
from app.estado import Estado
from app.mensajes import mensaje_persona, mensajes


def cruce():
    return Cruce(
        id="vado",
        nombre="Vado de la Ruta 623",
        rio="Río Vainilla",
        ruta_alterna_es="Use el puente de la entrada.",
        ruta_alterna_en="Use the bridge at the entrance.",
    )


@pytest.mark.parametrize("estado", list(Estado))
def test_hay_mensaje_en_espanol_en_ingles_y_para_el_guia(estado):
    m = mensajes(estado, cruce(), nivel=50)
    assert m["es"] and m["en"] and m["guia"]
    assert m["es"] != m["en"]


def test_cerrado_dice_cerrado_closed_y_da_la_ruta_alterna():
    m = mensajes(Estado.CERRADO, cruce())
    assert "CERRADO" in m["es"] and "CLOSED" in m["en"]
    assert "Use el puente de la entrada." in m["es"]
    assert "Use the bridge at the entrance." in m["en"]


def test_cuidado_es_caution_y_libre_es_open():
    assert "CAUTION" in mensajes(Estado.CUIDADO, cruce())["en"]
    assert "OPEN" in mensajes(Estado.LIBRE, cruce())["en"]


def test_mensaje_del_guia_es_corto_para_leerlo_en_voz():
    m = mensajes(Estado.CERRADO, cruce(), nivel=74)
    assert len(m["guia"]) <= 160
    assert "74" in m["guia"]


def test_alerta_de_persona_en_el_cruce():
    m = mensaje_persona(Estado.CERRADO, cruce())
    assert "persona" in m["es"].lower()
    assert "person" in m["en"].lower()
    assert m["guia"]
