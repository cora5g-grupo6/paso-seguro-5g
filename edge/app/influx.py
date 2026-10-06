"""Historia en InfluxDB (opcional): nivel, estado, fuente y latencias del borde.

Sirve para gráficos (Grafana) o para alimentar un gemelo digital. No decide ni avisa: si InfluxDB
no responde, el borde sigue igual y los puntos esperan en memoria, con tope, hasta el próximo envío.

Formato: protocolo de líneas, sin librerías extra.
  - InfluxDB 2.x, Cloud y 3.x: POST /api/v2/write?org=…&bucket=…&precision=ms con «Authorization: Token …»
  - InfluxDB 1.x: POST /write?db=…&precision=ms con usuario y clave por Basic Auth (nunca en la URL)
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque

import httpx

from app.estado import Decision
from app.feeds.waze import iso

log = logging.getLogger("paso_seguro.influx")

MEDICION_ESTADO = "paso_seguro_estado"
MEDICION_LATENCIA = "paso_seguro_latencia"


def _nombre(texto, especiales: str) -> str:
    s = str(texto)
    for ch in especiales:
        s = s.replace(ch, "\\" + ch)
    return s


def _valor(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, bool):  # antes que int: bool es un int en Python
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}i"
    if isinstance(v, float):
        return repr(v) if math.isfinite(v) else None
    texto = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{texto}"'


def linea(medicion: str, etiquetas: dict, campos: dict, t_ms: int) -> str | None:
    """Un punto en protocolo de líneas, o None si no queda ningún campo con valor."""
    valores = {k: _valor(v) for k, v in campos.items()}
    partes = [f"{_nombre(k, ',= ')}={v}" for k, v in sorted(valores.items()) if v is not None]
    if not partes:
        return None
    tags = "".join(f",{_nombre(k, ',= ')}={_nombre(v, ',= ')}"
                   for k, v in sorted(etiquetas.items()) if v not in (None, ""))
    return f"{_nombre(medicion, ', ')}{tags} {','.join(partes)} {int(t_ms)}"


def _decimal(x) -> float | None:
    # siempre float: si un punto llega como entero, InfluxDB rechaza los siguientes por cambio de tipo
    return None if x is None else float(x)


def puntos_estado(d: Decision, cruce_id: str, t_ms: int) -> list[str]:
    campos = {
        "nivel": _decimal(d.nivel),
        "estado": str(d.estado),
        "estado_num": d.estado.orden,
        "tasa": _decimal(d.tasa),
        "degradado": d.degradado,
        "discrepancia": d.discrepancia,
    }
    p = linea(MEDICION_ESTADO, {"cruce": cruce_id, "fuente": d.fuente}, campos, t_ms)
    return [p] if p else []


def puntos_latencia(resumen: dict[str, dict], cruce_id: str, t_ms: int) -> list[str]:
    lineas = []
    for tramo, r in resumen.items():
        if not r.get("n"):
            continue
        campos = {"n": int(r["n"]), **{k: _decimal(r.get(k)) for k in ("p50", "p95", "ultimo")}}
        p = linea(MEDICION_LATENCIA, {"cruce": cruce_id, "tramo": tramo}, campos, t_ms)
        if p:
            lineas.append(p)
    return lineas


class InfluxError(Exception):
    pass


class ClienteInflux:
    def __init__(self, url: str, bucket: str, org: str = "", token: str = "", version: str = "2",
                 usuario: str = "", clave: str = "", timeout: float = 5.0,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.url = url.rstrip("/")
        self.bucket, self.org, self.version = bucket, org, str(version).strip()
        self._token, self._usuario, self._clave = token, usuario, clave
        self.timeout, self.transport = timeout, transport

    @property
    def destino(self) -> str:
        try:
            return httpx.URL(self.url).host or self.url
        except Exception:
            return ""

    def _pedido(self) -> tuple[str, dict, dict, tuple[str, str] | None]:
        if self.version == "1":
            auth = (self._usuario, self._clave) if self._usuario else None
            return f"{self.url}/write", {"db": self.bucket, "precision": "ms"}, {}, auth
        params = {"org": self.org} if self.org else {}
        params.update(bucket=self.bucket, precision="ms")
        headers = {"Authorization": f"Token {self._token}"} if self._token else {}
        return f"{self.url}/api/v2/write", params, headers, None

    async def escribir(self, lineas: list[str]) -> None:
        url, params, headers, auth = self._pedido()
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as c:
            r = await c.post(url, params=params, auth=auth, content="\n".join(lineas).encode("utf-8"),
                             headers={**headers, "Content-Type": "text/plain; charset=utf-8"})
        if r.status_code >= 300:
            raise InfluxError(f"HTTP {r.status_code}")


class EscritorInflux:
    """Cola en memoria con tope: agrega puntos sin esperar a la red y los manda en lotes con reintentos."""

    def __init__(self, cliente: ClienteInflux, max_pendientes: int = 5000, lote: int = 500):
        self.cliente = cliente
        self.max_pendientes, self.lote = max_pendientes, lote
        self.pendientes: deque[str] = deque()
        self.enviados = self.descartados = self.errores = 0
        self.ok: bool | None = None
        self.ultimo_error: str | None = None
        self.ultimo_envio: float | None = None

    def agregar(self, lineas: list[str]) -> None:
        self.pendientes.extend(lineas)
        self._recortar()

    def _recortar(self) -> None:
        while len(self.pendientes) > self.max_pendientes:  # se pierden los más viejos, no los nuevos
            self.pendientes.popleft()
            self.descartados += 1

    async def enviar(self) -> bool:
        if not self.pendientes:
            return True
        lote = [self.pendientes.popleft() for _ in range(min(self.lote, len(self.pendientes)))]
        try:
            await self.cliente.escribir(lote)
        except Exception as e:  # nunca tumbar el borde por InfluxDB
            self.pendientes.extendleft(reversed(lote))  # vuelven adelante, en el mismo orden
            self._recortar()
            self.errores += 1
            self.ok = False
            # sin el texto de la excepción: podría traer la URL; el token y la clave nunca salen de aquí
            self.ultimo_error = str(e) if isinstance(e, InfluxError) else type(e).__name__
            if not isinstance(e, (InfluxError, httpx.HTTPError)):
                log.exception("Error inesperado escribiendo en InfluxDB")
            return False
        self.enviados += len(lote)
        self.ok, self.ultimo_error, self.ultimo_envio = True, None, time.time()
        return True

    def estado(self) -> dict:
        return {
            "activo": True,
            "ok": self.ok,
            "destino": self.cliente.destino,
            "bucket": self.cliente.bucket,
            "version": self.cliente.version,
            "pendientes": len(self.pendientes),
            "enviados": self.enviados,
            "descartados": self.descartados,
            "errores": self.errores,
            "ultimo_error": self.ultimo_error,
            "ultimo_envio_iso": iso(self.ultimo_envio) if self.ultimo_envio else None,
        }
