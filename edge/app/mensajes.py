"""Mensajes para el turista (español e inglés) y para el guía (corto, para voz)."""

from __future__ import annotations

from app.cruce import Cruce
from app.estado import Estado, num

NOMBRE_EN = {Estado.LIBRE: "OPEN", Estado.CUIDADO: "CAUTION", Estado.CERRADO: "CLOSED"}
_CIERRE_GUIA = {
    Estado.CERRADO: " No deje cruzar a nadie.",
    Estado.CUIDADO: " Prepare al grupo y espere instrucciones.",
    Estado.LIBRE: "",
}


def mensajes(estado: Estado, cruce: Cruce, nivel: float | None = None) -> dict:
    rio = cruce.rio_en_frase or "río"
    nombre = cruce.nombre
    if estado == Estado.CERRADO:
        es = (f"{nombre}: CERRADO. El {rio} está crecido y puede arrastrar personas y carros. "
              f"{cruce.ruta_alterna_es}").strip()
        en = (f"{nombre}: CLOSED. The river is flooding and can sweep away people and cars. "
              f"{cruce.ruta_alterna_en}").strip()
    elif estado == Estado.CUIDADO:
        es = f"{nombre}: CUIDADO. El {rio} está subiendo. Cruce solo con guía o espere."
        en = f"{nombre}: CAUTION. The river is rising. Cross only with a guide, or wait."
    else:
        es = f"{nombre}: LIBRE. El {rio} está en su nivel normal. Cruce con precaución."
        en = f"{nombre}: OPEN. The river is at its normal level. Cross with care."
    guia = f"Paso Seguro. {nombre}: {estado}."
    if nivel is not None:
        guia += f" Nivel {num(nivel, 0)} por ciento."
    guia += _CIERRE_GUIA[estado]
    return {
        "estado": str(estado),
        "titulo_es": str(estado),
        "titulo_en": NOMBRE_EN[estado],
        "es": es,
        "en": en,
        "guia": guia,
    }


def mensaje_persona(estado: Estado, cruce: Cruce) -> dict:
    return {
        "es": f"Atención: hay una persona en la zona del cruce ({cruce.nombre}) y el cruce está {estado}.",
        "en": f"Warning: a person is at the crossing ({cruce.nombre}) while it is {NOMBRE_EN[estado]}.",
        "guia": f"Alerta. Persona en el cruce, estado {estado}. Revise el video.",
    }
