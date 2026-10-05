"""Despachador de alertas con adaptadores.

Canales locales siempre activos (no pasan por aquí porque no dependen de internet):
el tablero web por SSE y el estado por MQTT para el ESP32.

Adaptadores opcionales:
- Webhook: POST JSON a las URL de WEBHOOK_URLS.
- N8nPrueba: APAGADO por defecto. Solo acepta URL de prueba ("prueba" o "test" en la ruta)
  y marca cada alerta con "prueba": true. El flujo de n8n tiene que ser aparte y escribir
  solo a un número de prueba. Nunca a producción.
- PttStub: Nokia Team Comms (PTT/PTV) hasta conocer su API. Deja cada alerta en una cola
  JSONL para que un integrador (o una persona en la consola) la dispare. Ver README.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.latencia import Latencias


class Adaptador:
    nombre = "base"
    activo = True

    async def enviar(self, alerta: dict) -> dict:  # pragma: no cover - interfaz
        raise NotImplementedError

    def a_dict(self) -> dict:
        return {"nombre": self.nombre, "activo": self.activo}


async def _post(url: str, cuerpo: dict, timeout: float, transport) -> str | None:
    """Devuelve None si salió bien, o el error en texto."""
    try:
        async with httpx.AsyncClient(timeout=timeout, transport=transport) as c:
            r = await c.post(url, json=cuerpo)
            r.raise_for_status()
        return None
    except httpx.HTTPError as e:
        return f"{type(e).__name__}"


class Webhook(Adaptador):
    def __init__(self, urls: list[str], nombre: str = "webhook", timeout: float = 5.0,
                 transport: httpx.AsyncBaseTransport | None = None, activo: bool | None = None):
        self.urls = [u.strip() for u in urls if u and u.strip()]
        self.nombre = nombre
        self.timeout = timeout
        self.transport = transport
        self.activo = bool(self.urls) if activo is None else activo

    async def enviar(self, alerta: dict) -> dict:
        errores = []
        for url in self.urls:
            err = await _post(url, alerta, self.timeout, self.transport)
            if err:
                errores.append(f"{urlparse(url).netloc}: {err}")
        return {"ok": not errores, "detalle": "; ".join(errores) or f"enviado a {len(self.urls)} URL"}


PALABRAS_DE_PRUEBA = {"prueba", "pruebas", "test", "tests"}


def es_url_de_prueba(url: str) -> bool:
    """True si la ruta (ya normalizada, sin '..') tiene la palabra exacta prueba o test.

    Así pasan /webhook-test/... (las URL de prueba de n8n) y /webhook/paso-seguro-prueba,
    pero no /webhook/alertas-latest ni /aprueba-cierre ni /webhook/prueba/../produccion.
    """
    try:
        ruta = httpx.URL(url).path.lower()
    except Exception:
        return False
    palabras = {p for tramo in ruta.split("/") for p in re.split(r"[-_.]", tramo) if p}
    return bool(palabras & PALABRAS_DE_PRUEBA)


class N8nPrueba(Adaptador):
    nombre = "n8n-prueba"

    def __init__(self, url: str = "", activo: bool = False, timeout: float = 5.0,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.url = url.strip()
        self.activo = activo
        self.timeout = timeout
        self.transport = transport

    async def enviar(self, alerta: dict) -> dict:
        if not self.url:
            return {"ok": False, "detalle": "Falta N8N_WEBHOOK_URL"}
        if not es_url_de_prueba(self.url):
            return {"ok": False, "detalle": "La URL de n8n no es de prueba (debe tener 'prueba' o 'test' en la ruta). No se envió."}
        err = await _post(self.url, {**alerta, "prueba": True}, self.timeout, self.transport)
        return {"ok": err is None, "detalle": err or "enviado al flujo de prueba"}


class PttStub(Adaptador):
    """Punto de enganche para Nokia Team Comms (PTT/PTV).

    Contrato esperado cuando se conozca la API (por confirmar con la PCII):
      - destino: grupo de conversación del guía (licencia Team Comms en el XR20)
      - voz: texto `mensaje_guia` convertido a voz, o un audio pregrabado por estado
      - video (PTV): enlace al video en vivo `enlaces.video` o a la captura `enlaces.captura`
    Mientras tanto, cada alerta queda en una cola JSONL y el guía la recibe por /guia.
    """

    nombre = "ptt-ptv"

    def __init__(self, archivo: str | Path, activo: bool = False):
        self.archivo = Path(archivo)
        self.activo = activo

    async def enviar(self, alerta: dict) -> dict:
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        linea = {**alerta, "t_cola": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with self.archivo.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")
        return {"ok": False, "detalle": f"Stub: falta la API de Nokia Team Comms (PTT/PTV). Quedó en cola: {self.archivo.name}"}


class Despachador:
    def __init__(self, adaptadores: list[Adaptador], latencias: Latencias):
        self.adaptadores = adaptadores
        self.lat = latencias

    async def despachar(self, alerta: dict) -> list[dict]:
        async def uno(a: Adaptador) -> dict:
            t0 = time.perf_counter()
            try:
                r = await a.enviar(alerta)
            except Exception as e:  # un canal roto no puede frenar a los demás
                r = {"ok": False, "detalle": f"{type(e).__name__}: {e}"}
            ms = (time.perf_counter() - t0) * 1000
            self.lat.agregar(f"alerta_envio_ms:{a.nombre}", ms)
            return {"canal": a.nombre, "ms": round(ms, 1), **r}

        return list(await asyncio.gather(*(uno(a) for a in self.adaptadores if a.activo)))
