"""Orquestador del borde.

Junta las entradas (cámara, ESP32 por HTTP o MQTT, lluvia del IMN, cierre manual), corre la
máquina de estados y reparte las salidas:
  - tablero, página del guía y página del turista por SSE (local, sin internet)
  - estado por MQTT y en la respuesta HTTP para el ESP32 (luces y zumbador)
  - feeds Waze CIFS (JSON/XML), GeoJSON y Google Maps Content Partners
  - alertas por webhook, n8n de prueba y PTT/PTV (stub)
Todo lo que toca el estado corre en el hilo del event loop. La cámara y MQTT corren en sus
hilos y entran con call_soon_threadsafe.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import time
from collections import deque
from dataclasses import replace
from pathlib import Path

import httpx

from app.alertas import Despachador, N8nPrueba, PttStub, Webhook
from app.config import BASE, Config
from app.cruce import cargar_cruce
from app.estado import Decision, Entradas, Estado, MaquinaEstados, Umbrales
from app.feeds.geo import COLORES, estado_geojson, google_cierres_geojson
from app.feeds.waze import CAJA_CR, GestorEpisodios, feed_cifs_json, feed_cifs_xml, iso, validar_cifs
from app.imn import ClienteIMN, IMNError, distancia_km, estacion_mas_cercana
from app.influx import ClienteInflux, EscritorInflux, puntos_estado, puntos_latencia
from app.latencia import Latencias
from app.mensajes import mensaje_persona, mensajes

log = logging.getLogger("paso_seguro")

COLOR_ESP32 = {Estado.LIBRE: "VERDE", Estado.CUIDADO: "AMARILLO", Estado.CERRADO: "ROJO"}
CAMPOS_SENSOR = ("nivel_pct", "nivel_raw", "flotador", "semaforo_local", "modo", "rssi", "rtt_ms", "seq", "uptime_s", "ip")
XSD_CIFS = Path(__file__).parent / "feeds" / "cifsv2.xsd"
VERSION = "0.1.0"


def _num(v) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None  # NaN o infinito romperían el JSON del tablero


def _limpio(v):
    """Valor seguro para guardar y mostrar: números finitos, booleanos o texto corto."""
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v if math.isfinite(v) else None
    if isinstance(v, str):
        return v[:40]
    return None


def _nombre_seguro(texto: str, defecto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "", str(texto or ""))[:32] or defecto


class Sistema:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.datos = cfg.ruta(cfg.datos_dir)
        self.carpeta_eventos = self.datos / "eventos"
        self.carpeta_eventos.mkdir(parents=True, exist_ok=True)
        self.cruce = cargar_cruce(cfg.ruta(cfg.cruce_archivo))
        self.umbrales = Umbrales(
            cuidado=cfg.umbral_cuidado,
            cerrado=cfg.umbral_cerrado,
            histeresis=cfg.histeresis,
            bajada_s=cfg.bajada_s,
            tasa_cuidado=cfg.tasa_cuidado,
            vence_s=cfg.vence_s,
            lluvia_1h=cfg.lluvia_1h_mm,
            lluvia_3h=cfg.lluvia_3h_mm,
            politica=cfg.politica_nivel,
        )
        self.lat = Latencias()
        self.influx: EscritorInflux | None = None
        self.influx_error: str | None = None
        if cfg.influx_activo and cfg.influx_url:
            self.influx = EscritorInflux(ClienteInflux(
                cfg.influx_url, cfg.influx_bucket, org=cfg.influx_org, token=cfg.influx_token,
                version=cfg.influx_version, usuario=cfg.influx_usuario, clave=cfg.influx_clave))
        elif cfg.influx_activo:
            self.influx_error = "Falta INFLUX_URL en el .env"
        self.episodios = GestorEpisodios(
            self.cruce.id,
            bloque_s=cfg.waze_bloque_h * 3600,
            retencion_s=cfg.waze_retencion_min * 60,
            archivo=self.datos / "episodios.json",
        )
        self.despachador = Despachador(
            [
                Webhook(cfg.lista(cfg.webhook_urls)),
                N8nPrueba(cfg.n8n_webhook_url, activo=cfg.n8n_activo),
                PttStub(self.datos / "ptt_pendientes.jsonl", activo=cfg.ptt_activo),
            ],
            self.lat,
        )
        self.eventos: deque[dict] = deque(maxlen=200)
        self.camara = None
        self.vision = None
        self.calibracion = None
        self.mqtt = None
        self.lluvia: dict | None = None
        self.lluvia_estaciones: list[dict] = []
        self.imn_estado = {"activo": cfg.imn_activo, "ok": None, "error": None, "consultado_iso": None,
                           "estacion": None, "distancia_km": None, "desde_cache": False}
        self.nube = {"activa": cfg.nube_activa, "ok": None}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subs: set[asyncio.Queue] = set()
        self._tareas: set[asyncio.Task] = set()
        self._xsd = None
        self._reiniciar_estado()
        self._retomar_episodio()

    def _retomar_episodio(self) -> None:
        """Si el borde se reinició con un aviso vigente, se retoma: nunca se reabre de golpe."""
        ep = self.episodios.activo
        if ep is None:
            return
        self.maquina = MaquinaEstados(self.umbrales, estado_inicial=ep.estado, t0=ep.inicio)
        self.decision = replace(self.decision, estado=ep.estado, anterior=ep.estado, objetivo=ep.estado,
                                desde=ep.inicio,
                                razones=[f"Retomado tras un reinicio: seguía {ep.estado} desde las {iso(ep.inicio)[11:16]}"])
        log.warning("Reinicio con el cruce %s desde %s: se retoma ese estado", ep.estado, iso(ep.inicio))

    # -- estado interno ------------------------------------------------------------

    def _reiniciar_estado(self) -> None:
        ahora = time.time()
        self.arranque = ahora
        self.maquina = MaquinaEstados(self.umbrales, t0=ahora)
        self.entradas = Entradas()
        self.decision = Decision(
            estado=Estado.LIBRE, anterior=Estado.LIBRE, cambio=False, objetivo=Estado.LIBRE,
            nivel=None, fuente="ninguna", tasa=None,
            razones=["Arrancando: esperando datos de la cámara y del sensor"],
            degradado=True, desde=ahora, t=ahora,
        )
        self.sensores: dict[str, dict] = {}
        self.vision_info: dict = {}
        self.personas: dict = {"cantidad": 0, "en_zona": 0, "metodo": self.cfg.personas_metodo}
        self.manual: dict | None = None
        self.lluvia_demo: dict | None = None
        self.alarma_persona_hasta = 0.0
        self._t_alerta_persona = 0.0
        self._ultimo_mqtt = 0.0

    def _hay_datos(self) -> bool:
        e = self.entradas
        return any(v is not None for v in (e.nivel_camara, e.nivel_sensor, e.flotador, self.manual, self.lluvia_demo))

    def _lluvia_vigente(self, t: float) -> dict:
        if self.lluvia_demo and t < self.lluvia_demo["hasta"]:
            return {"mm_1h": self.lluvia_demo["mm_1h"], "mm_3h": self.lluvia_demo["mm_3h"], "t": t,
                    "estacion": "simulación", "fuente": "simulación"}
        if self.lluvia:
            return {"mm_1h": self.lluvia.get("mm_1h"), "mm_3h": self.lluvia.get("mm_3h"),
                    "t": self.lluvia.get("t_ultimo"), "estacion": self.lluvia.get("estacion"), "fuente": "IMN"}
        return {}

    def _manual_vigente(self, t: float) -> Estado | None:
        if self.manual and t >= self.manual["hasta"]:
            self.manual = None
        return Estado(self.manual["estado"]) if self.manual else None

    def _entradas(self, t: float) -> Entradas:
        lluvia = self._lluvia_vigente(t)
        return replace(
            self.entradas,
            lluvia_1h=lluvia.get("mm_1h"),
            lluvia_3h=lluvia.get("mm_3h"),
            t_lluvia=lluvia.get("t"),
            estacion_lluvia=lluvia.get("estacion"),
            minimo_manual=self._manual_vigente(t),
        )

    # -- evaluación ------------------------------------------------------------------

    def evaluar(self, motivo: str = "tick", t: float | None = None) -> Decision:
        t = time.time() if t is None else t
        if not self._hay_datos() and t - self.arranque < self.cfg.arranque_s:
            return self.decision  # unos segundos de gracia al arrancar, sin alarmas falsas
        d = self.maquina.evaluar(self._entradas(t), t)
        self.decision = d
        cambio_feed = self.episodios.actualizar(d.estado, t)
        if self.vision:
            self.vision.estado_txt = str(d.estado)
        if d.cambio:
            self._emitir(self._evento_cambio(d, t, motivo))
            self.muestra_influx(t)  # el cambio queda en la historia con su hora exacta
        if d.cambio or cambio_feed:
            self._publicar_mqtt_estado()
        return d

    # -- entradas ----------------------------------------------------------------------

    def registrar_sensor(self, datos: dict, origen: str) -> dict:
        t = time.time()
        disp = _nombre_seguro(datos.get("id"), "esp32")
        nivel = _num(datos.get("nivel_pct"))
        if nivel is not None:
            self.entradas.nivel_sensor = max(0.0, min(110.0, nivel))
            self.entradas.t_sensor = t
        if datos.get("flotador") is not None:
            self.entradas.flotador = bool(datos["flotador"])
            self.entradas.t_flotador = t
        rtt = _num(datos.get("rtt_ms"))
        if rtt is not None and 0 < rtt < 60000:
            self.lat.agregar("esp32_rtt_ms", rtt)
        self.sensores[disp] = {**{k: _limpio(datos[k]) for k in CAMPOS_SENSOR if k in datos},
                               "id": disp, "origen": origen, "t_ms": round(t * 1000), "t_iso": iso(t)}
        self.evaluar(f"sensor:{origen}", t)
        self.lat.agregar("sensor_a_decision_ms", (time.time() - t) * 1000)
        return self.respuesta_esp32()

    def registrar_camara(self, res, per, t_cap: float, ms: float) -> None:
        self.lat.agregar("vision_ms", ms)
        self.vision_info = {**res.a_dict(), "t_captura_ms": round(t_cap * 1000)}
        e = self.entradas
        e.t_camara = t_cap
        if res.nivel_pct is not None:
            e.nivel_camara, e.confianza_camara = res.nivel_pct, res.confianza
        else:  # la cámara está, pero no ve: la máquina lo marca y usa el sensor
            e.nivel_camara = e.nivel_camara if e.nivel_camara is not None else 0.0
            e.confianza_camara = 0.0
        if per is not None:
            self.personas = {**per.a_dict(), "t_ms": round(t_cap * 1000)}
        self.evaluar("camara")
        self.lat.agregar("captura_a_decision_ms", (time.time() - t_cap) * 1000)
        if per is not None:
            self._revisar_persona(per.en_zona, per.metodo, time.time())

    def _desde_vision(self, res, per, t_cap: float, ms: float) -> None:  # hilo de visión
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self.registrar_camara, res, per, t_cap, ms)

    def _desde_mqtt(self, datos: dict) -> None:  # hilo de MQTT
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self.registrar_sensor, datos, "mqtt")

    def respuesta_esp32(self) -> dict:
        d = self.decision
        ahora = time.time()
        return {
            "estado": str(d.estado),
            "color": COLOR_ESP32[d.estado],
            "nivel": d.nivel,
            "buzzer": d.estado == Estado.CERRADO,
            "alarma_persona": ahora < self.alarma_persona_hasta,
            "t_srv": round(ahora * 1000),
        }

    # -- eventos y alertas ---------------------------------------------------------------

    def _nuevo_id(self, t: float) -> str:
        base = f"ev{int(t * 1000)}"
        usados = {e["id"] for e in self.eventos}
        eid, n = base, 1
        while eid in usados:
            n += 1
            eid = f"{base}-{n}"
        return eid

    def _enlaces(self, eid: str) -> dict:
        b = self.cfg.url_publica.rstrip("/")
        return {
            "tablero": f"{b}/",
            "guia": f"{b}/guia",
            "turista": f"{b}/turista",
            "video": f"{b}/video.mjpg" if self.vision else None,
            "captura": f"{b}/media/eventos/{eid}/captura.jpg" if self.vision else None,
        }

    def _evento(self, tipo: str, t: float, estado: Estado, anterior: Estado, razones: list[str],
                textos: dict, motivo: str) -> dict:
        eid = self._nuevo_id(t)
        d = self.decision
        return {
            "id": eid, "tipo": tipo, "estado": str(estado), "anterior": str(anterior),
            "nivel": d.nivel, "fuente": d.fuente, "razones": razones, "degradado": d.degradado,
            "motivo": motivo, "t_evento_ms": round(t * 1000, 1), "t_iso": iso(t),
            "mensajes": textos, "enlaces": self._enlaces(eid), "media": None, "envios": [], "acks": [],
        }

    def _evento_cambio(self, d: Decision, t: float, motivo: str) -> dict:
        return self._evento("cambio_estado", t, d.estado, d.anterior, d.razones,
                            mensajes(d.estado, self.cruce, d.nivel), motivo)

    def _revisar_persona(self, en_zona: int, metodo: str, t: float) -> None:
        d = self.decision
        if en_zona <= 0 or d.estado == Estado.LIBRE or t - self._t_alerta_persona < 30:
            return
        self._t_alerta_persona = t
        self.alarma_persona_hasta = t + 15
        razones = [f"{en_zona} persona(s) en la zona del cruce (detección: {metodo})"]
        self._emitir(self._evento("persona_en_cruce", t, d.estado, d.estado, razones,
                                  mensaje_persona(d.estado, self.cruce), "personas"))
        self._publicar_mqtt_estado()

    def _emitir(self, ev: dict) -> None:
        self.eventos.appendleft(ev)
        self._guardar_linea("eventos.jsonl", {k: v for k, v in ev.items() if k not in ("envios", "acks")})
        self._difundir("alerta", ev)
        if self.mqtt:
            self.mqtt.publicar(f"{self.cruce.id}/alerta", {k: ev[k] for k in ("id", "tipo", "estado", "nivel", "t_evento_ms")})
        if self.vision:
            ev["media"] = {"captura": f"/media/eventos/{ev['id']}/captura.jpg", "clip": []}
            self._en_hilo(self._guardar_media, ev)
        self._tarea(self._despachar(ev))

    def _guardar_media(self, ev: dict) -> None:  # corre en un hilo aparte
        try:
            nombres = self.vision.guardar_evento(self.carpeta_eventos / ev["id"])
            ev["media"]["clip"] = [f"/media/eventos/{ev['id']}/{n}" for n in nombres]
        except Exception:  # sin disco o sin permisos: la alerta ya salió igual
            log.exception("No se pudo guardar la captura del evento %s", ev["id"])

    def _payload_alerta(self, ev: dict) -> dict:
        c = self.cruce
        return {
            "id": ev["id"], "tipo": ev["tipo"], "estado": ev["estado"], "anterior": ev["anterior"],
            "nivel_pct": ev["nivel"], "fuente": ev["fuente"], "razones": ev["razones"],
            "mensaje_es": ev["mensajes"].get("es"), "mensaje_en": ev["mensajes"].get("en"),
            "mensaje_guia": ev["mensajes"].get("guia"), "t_evento": ev["t_iso"], "t_evento_ms": ev["t_evento_ms"],
            "cruce": {"id": c.id, "nombre": c.nombre, "rio": c.rio, "lugar": c.lugar, "punto": list(c.punto)},
            "enlaces": ev["enlaces"],
        }

    async def _despachar(self, ev: dict) -> None:
        res = await self.despachador.despachar(self._payload_alerta(ev))
        ev["envios"] = res
        if res:
            self._difundir("envios", {"id": ev["id"], "envios": res})

    def buscar_evento(self, eid: str) -> dict | None:
        return next((e for e in self.eventos if e["id"] == eid), None)

    def ack(self, eid: str, cliente: str, t_recibido_ms: float | None = None) -> dict:
        ev = self.buscar_evento(eid)
        if ev is None:
            raise KeyError(eid)
        ahora_ms = time.time() * 1000
        # el cliente corrige su reloj con /ping; si no manda la hora (o es basura), se cuenta hasta el ack
        recibido = _num(t_recibido_ms)
        entrega = (recibido if recibido is not None else ahora_ms) - ev["t_evento_ms"]
        self.lat.agregar("alerta_entrega_ms", entrega)
        registro = {"cliente": _nombre_seguro(cliente, "cliente"), "entrega_ms": round(entrega, 1), "t_iso": iso(ahora_ms / 1000)}
        ev["acks"].append(registro)
        self._difundir("ack", {"id": eid, **registro})
        return {"ok": True, **registro}

    def latencia_cliente(self, cliente: str, rtts: list[float]) -> dict:
        nombre = _nombre_seguro(cliente, "cliente")
        validos = [r for r in (_num(x) for x in rtts) if r is not None and 0 < r < 60000]
        for r in validos:
            self.lat.agregar(f"cliente_rtt_ms:{nombre}", r)
        return {"ok": True, "n": len(validos)}

    # -- operador y demo -----------------------------------------------------------------

    def fijar_manual(self, estado: Estado | None, motivo: str = "", minutos: float = 120) -> dict:
        ahora = time.time()
        if estado is None or estado == Estado.LIBRE:
            self.manual = None
        else:
            self.manual = {"estado": str(estado), "motivo": motivo[:120], "hasta": ahora + minutos * 60,
                           "desde_iso": iso(ahora), "hasta_iso": iso(ahora + minutos * 60)}
        d = self.evaluar("manual", ahora)
        return {"estado": str(d.estado), "manual": self.manual}

    def demo_nivel(self, nivel: float, fuente: str = "camara") -> dict:
        t = time.time()
        if fuente == "sensor":
            self.entradas.nivel_sensor, self.entradas.t_sensor = nivel, t
        else:
            self.entradas.nivel_camara, self.entradas.t_camara, self.entradas.confianza_camara = nivel, t, 1.0
        d = self.evaluar("demo", t)
        return {"estado": str(d.estado), "nivel": d.nivel, "razones": d.razones}

    def demo_lluvia(self, mm_1h: float, mm_3h: float | None = None, minutos: float = 10) -> dict:
        t = time.time()
        self.lluvia_demo = {"mm_1h": mm_1h, "mm_3h": mm_3h if mm_3h is not None else mm_1h, "hasta": t + minutos * 60}
        d = self.evaluar("demo", t)
        return {"estado": str(d.estado), "razones": d.razones}

    def demo_persona(self) -> dict:
        self._t_alerta_persona = 0.0
        self._revisar_persona(1, "simulación", time.time())
        return {"estado": str(self.decision.estado), "alarma_persona": time.time() < self.alarma_persona_hasta}

    def reiniciar(self) -> dict:
        # el aviso vigente se cierra con hora fija (sigue 1 h en el feed, como pide Waze); no se borra
        self.episodios.actualizar(Estado.LIBRE, time.time())
        self._reiniciar_estado()
        self.eventos.clear()
        self._publicar_mqtt_estado()
        return {"estado": str(self.decision.estado)}

    # -- feeds ---------------------------------------------------------------------------

    def feed_waze_json(self, envuelto: bool = False) -> dict:
        return feed_cifs_json(self.episodios.vigentes(time.time()), self.cruce, envuelto)

    def feed_waze_xml(self) -> str:
        t = time.time()
        return feed_cifs_xml(self.episodios.vigentes(t), self.cruce, t)

    def feed_estado_geojson(self) -> dict:
        d = self.decision
        return estado_geojson(self.cruce, d.estado, time.time(), d.nivel, d.fuente, d.razones,
                              mensajes(d.estado, self.cruce, d.nivel))

    def feed_google(self) -> dict:
        return google_cierres_geojson(self.episodios.vigentes(time.time()), self.cruce)

    def validar_feeds(self) -> dict:
        return {
            "waze_json": validar_cifs(self.feed_waze_json(), CAJA_CR).a_dict(),
            "waze_xml_xsd": self._validar_xsd(self.feed_waze_xml()),
            "spec": "https://developers.google.com/waze/data-feed/cifs-specification",
            "xsd": "https://www.gstatic.com/road-incidents/cifsv2.xsd",
        }

    def _validar_xsd(self, xml: str) -> dict:
        try:
            import xmlschema
        except ImportError:
            return {"ok": None, "errores": ["Falta el paquete xmlschema"]}
        if self._xsd is None:
            self._xsd = xmlschema.XMLSchema(str(XSD_CIFS))
        errores = [str(getattr(e, "reason", e))[:200] for e in self._xsd.iter_errors(xml)]
        return {"ok": not errores, "errores": errores}

    # -- cámara ----------------------------------------------------------------------------

    def jpeg_actual(self, crudo: bool = False) -> bytes | None:
        if not self.vision:
            return None
        if crudo:
            if self.vision.crudo is None:
                return None
            import cv2

            ok, buf = cv2.imencode(".jpg", self.vision.crudo, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return buf.tobytes() if ok else None
        return self.vision.jpeg

    def calibrar(self, datos: dict) -> dict:
        from app.vision.nivel import calibracion_desde_clics, guardar_calibracion

        if not self.vision or self.vision.crudo is None:
            raise RuntimeError("No hay cuadro de cámara para calibrar")
        alto, ancho = self.vision.crudo.shape[:2]
        x, y = datos["punto_agua"]
        if not (0 <= x < ancho and 0 <= y < alto):
            raise RuntimeError(f"El punto del agua ({x}, {y}) queda fuera del cuadro de {ancho}×{alto}")
        if datos["y_cero"] == datos["y_cien"]:
            raise RuntimeError("Las marcas de 0 % y 100 % no pueden estar en la misma fila")
        cal = calibracion_desde_clics(self.vision.crudo, roi=tuple(datos["roi"]), y_cero=datos["y_cero"],
                                      y_cien=datos["y_cien"], punto_agua=tuple(datos["punto_agua"]),
                                      base=self.calibracion)
        if datos.get("modo") in ("columna", "marcador"):
            cal = replace(cal, modo=datos["modo"])
        if "ref_roi" in datos:
            cal = replace(cal, ref_roi=tuple(datos["ref_roi"]) if datos["ref_roi"] else None)
        guardar_calibracion(cal, self.cfg.ruta(self.cfg.calibracion_archivo))
        self.calibracion = cal
        self.vision.aplicar_calibracion(cal)
        return cal.a_dict()

    # -- vista para el tablero ---------------------------------------------------------------

    def _lluvia_info(self, t: float) -> dict:
        ll = self._lluvia_vigente(t)
        if not ll:
            return {"fuente": None}
        edad = None if ll.get("t") is None else round((t - ll["t"]) / 60)
        return {"fuente": ll["fuente"], "mm_1h": ll.get("mm_1h"), "mm_3h": ll.get("mm_3h"),
                "estacion": ll.get("estacion"), "edad_min": edad,
                "distancia_km": (self.lluvia or {}).get("distancia_km") if ll["fuente"] == "IMN" else None}

    def snapshot(self) -> dict:
        t = time.time()
        d, e, u = self.decision, self.entradas, self.umbrales

        def edad(tx: float | None) -> float | None:
            return None if tx is None else round(t - tx, 1)

        return {
            "version": VERSION,
            "estado": str(d.estado),
            "color": COLORES[d.estado],
            "objetivo": str(d.objetivo),
            "nivel": d.nivel,
            "fuente": d.fuente,
            "tasa": None if d.tasa is None else round(d.tasa, 1),
            "razones": d.razones,
            "degradado": d.degradado,
            "discrepancia": d.discrepancia,
            "desde_ms": round(d.desde * 1000),
            "desde_iso": iso(d.desde),
            "bajada_en_s": None if d.bajada_en_s is None else round(d.bajada_en_s),
            "t_ms": round(t * 1000),
            "t_iso": iso(t),
            "mensajes": mensajes(d.estado, self.cruce, d.nivel),
            "alarma_persona": t < self.alarma_persona_hasta,
            "entradas": {
                "camara": {"nivel": e.nivel_camara, "confianza": e.confianza_camara, "edad_s": edad(e.t_camara),
                           "motivo": self.vision_info.get("motivo", "")},
                "sensor": {"nivel": e.nivel_sensor, "edad_s": edad(e.t_sensor)},
                "flotador": {"activo": e.flotador, "edad_s": edad(e.t_flotador)},
                "lluvia": self._lluvia_info(t),
                "manual": self.manual,
            },
            "personas": self.personas,
            "sensores": list(self.sensores.values()),
            "camara": self.camara.estado() if self.camara else {"activa": False},
            "mqtt": {"activo": self.cfg.mqtt_activo, "conectado": bool(self.mqtt and self.mqtt.conectado)},
            "imn": self.imn_estado,
            "nube": self.nube,
            "influx": self._estado_influx(),
            "umbrales": {"cuidado": u.cuidado, "cerrado": u.cerrado, "histeresis": u.histeresis,
                         "bajada_s": u.bajada_s, "tasa_cuidado": u.tasa_cuidado},
            "modo_demo": self.cfg.modo_demo,
            "waze": {"incidentes": len(self.episodios.vigentes(t)), "publica": self.cruce.publica_en_waze},
        }

    def salud(self) -> dict:
        return {"ok": True, "version": VERSION, "estado": str(self.decision.estado),
                "arranque_iso": iso(self.arranque), "camara": self.camara.estado() if self.camara else {"activa": False},
                "mqtt": {"activo": self.cfg.mqtt_activo, "conectado": bool(self.mqtt and self.mqtt.conectado)},
                "imn": self.imn_estado, "nube": self.nube, "influx": self._estado_influx()}

    def _estado_influx(self) -> dict:
        if self.influx:
            return self.influx.estado()
        return {"activo": False, "error": self.influx_error} if self.influx_error else {"activo": False}

    # -- SSE ---------------------------------------------------------------------------------

    def suscribir(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subs.add(q)
        return q

    def desuscribir(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    def _difundir(self, tipo: str, datos: dict) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait((tipo, datos))
            except asyncio.QueueFull:
                pass  # un cliente lento no frena a los demás

    # -- utilidades ----------------------------------------------------------------------------

    def _publicar_mqtt_estado(self) -> None:
        if self.mqtt:
            self.mqtt.publicar(f"{self.cruce.id}/estado", self.respuesta_esp32(), retener=True)
            self._ultimo_mqtt = time.time()

    def muestra_influx(self, t: float, latencias: bool = False) -> None:
        """Encola el estado (y, si se pide, las latencias) para InfluxDB. No espera a la red."""
        if not self.influx:
            return
        t_ms = round(t * 1000)
        lineas = puntos_estado(self.decision, self.cruce.id, t_ms)
        if latencias:
            lineas += puntos_latencia(self.lat.resumen(), self.cruce.id, t_ms)
        self.influx.agregar(lineas)

    def _guardar_linea(self, nombre: str, datos: dict) -> None:
        try:
            with (self.datos / nombre).open("a", encoding="utf-8") as f:
                f.write(json.dumps(datos, ensure_ascii=False, default=str) + "\n")
        except OSError:
            log.exception("No se pudo escribir %s", nombre)

    def _tarea(self, coro) -> None:
        try:
            tarea = asyncio.get_running_loop().create_task(coro)
        except RuntimeError:  # sin event loop (uso directo en scripts): se descarta
            coro.close()
            return
        self._tareas.add(tarea)
        tarea.add_done_callback(self._tareas.discard)

    def _en_hilo(self, funcion, *args) -> None:
        try:
            asyncio.get_running_loop().run_in_executor(None, funcion, *args)
        except RuntimeError:
            funcion(*args)

    # -- ciclo de vida ----------------------------------------------------------------------------

    async def iniciar(self) -> None:
        self._loop = asyncio.get_running_loop()
        if self.cfg.camara_activa:
            self._iniciar_camara()
        if self.cfg.mqtt_activo:
            from app.mqtt_cliente import ClienteMqtt

            self.mqtt = ClienteMqtt(self.cfg.mqtt_host, self.cfg.mqtt_puerto, self.cfg.mqtt_base, self._desde_mqtt,
                                    self.cfg.mqtt_usuario, self.cfg.mqtt_clave)
            self.mqtt.iniciar()
        self.evaluar("arranque")
        self._tarea(self._bucle_tick())
        if self.cfg.imn_activo:
            self._tarea(self._bucle_imn())
        if self.cfg.nube_activa:
            self._tarea(self._bucle_nube())
        if self.influx:
            self._tarea(self._bucle_influx())
        log.info("Paso Seguro listo · cruce %s · cámara=%s mqtt=%s imn=%s influx=%s", self.cruce.id,
                 bool(self.camara), bool(self.mqtt), self.cfg.imn_activo, bool(self.influx))

    def _iniciar_camara(self) -> None:
        from app.camara import Camara
        from app.vision.nivel import CalibracionNivel, cargar_calibracion
        from app.vision.personas import DetectorPersonas
        from app.vision.trabajador import TrabajadorVision

        self.calibracion = cargar_calibracion(self.cfg.ruta(self.cfg.calibracion_archivo)) or CalibracionNivel()
        self.camara = Camara(self.cfg.lista(self.cfg.camara_fuentes), ancho=self.cfg.camara_ancho, base=BASE,
                             lector=self.cfg.camara_lector)
        detector = DetectorPersonas(self.cfg.personas_metodo, self.cfg.zona_personas, self.cfg.personas_cada_n)
        self.vision = TrabajadorVision(self.camara, self.calibracion, detector, self.cfg.camara_fps_analisis,
                                       self._desde_vision, (self.umbrales.cuidado, self.umbrales.cerrado),
                                       mediana=self.cfg.vision_mediana)
        self.camara.iniciar()
        self.vision.iniciar()

    async def detener(self) -> None:
        for tarea in list(self._tareas):
            tarea.cancel()
        await asyncio.gather(*self._tareas, return_exceptions=True)
        if self.vision:
            self.vision.detener()
        if self.camara:
            self.camara.detener()
        if self.mqtt:
            self.mqtt.detener()

    async def _bucle_tick(self) -> None:
        ultimo_estado = ultimo_lat = 0.0
        while True:
            try:
                self.evaluar("tick")
                ahora = time.time()
                if ahora - ultimo_estado >= 0.5:
                    self._difundir("estado", self.snapshot())
                    ultimo_estado = ahora
                if ahora - ultimo_lat >= 2:
                    self._difundir("latencia", self.lat.resumen())
                    ultimo_lat = ahora
                if ahora - self._ultimo_mqtt >= 2:  # latido: el ESP32 por MQTT pasa a modo local a los 5 s sin estado
                    self._publicar_mqtt_estado()
            except Exception:
                log.exception("Error en el ciclo principal")
            await asyncio.sleep(self.cfg.tick_s)

    async def _bucle_imn(self) -> None:
        cache = self.datos / "imn_cache.json"
        if cache.exists():
            try:
                c = json.loads(cache.read_text(encoding="utf-8"))
                self.lluvia, self.lluvia_estaciones = c.get("lluvia"), c.get("estaciones", [])
                self.imn_estado.update(c.get("estado", {}), desde_cache=True)
            except (ValueError, OSError):
                pass
        cliente = ClienteIMN(self.cfg.imn_url)
        estaciones = []
        while True:
            try:
                if not estaciones:
                    estaciones = await cliente.estaciones()
                if self.cfg.imn_estacion:
                    est = next((x for x in estaciones if x.id == self.cfg.imn_estacion), None)
                    if est is None:
                        raise IMNError(f"No existe la estación {self.cfg.imn_estacion}")
                    km = distancia_km(*self.cruce.punto, est.lat, est.lon)
                else:
                    est, km = estacion_mas_cercana(estaciones, *self.cruce.punto)
                todas = await cliente.lluvia_todas(estaciones)
                propia = next((r for r in todas if r.estacion_id == est.id), None)
                if propia:
                    propia.distancia_km = round(km, 1)
                    self.lluvia = propia.a_dict()
                self.lluvia_estaciones = [
                    {"estacion_id": r.estacion_id, "estacion": r.estacion, "mm_1h": r.mm_1h, "mm_24h": r.mm_24h,
                     "max_1h": r.max_1h, "t_max_iso": iso(r.t_max) if r.t_max else None,
                     "ultimo_iso": iso(r.t_ultimo)}
                    for r in todas
                ]
                self.imn_estado.update(ok=True, error=None, consultado_iso=iso(time.time()), estacion=est.nombre,
                                       distancia_km=round(km, 1), desde_cache=False)
                cache.write_text(json.dumps({"lluvia": self.lluvia, "estaciones": self.lluvia_estaciones,
                                             "estado": self.imn_estado}, ensure_ascii=False), encoding="utf-8")
            except IMNError as e:
                self.imn_estado.update(ok=False, error=str(e))
            except Exception as e:  # nunca tumbar el borde por un dato externo
                log.exception("Error leyendo el IMN")
                self.imn_estado.update(ok=False, error=f"{type(e).__name__}: {e}")
            await asyncio.sleep(self.cfg.imn_intervalo_s)

    async def _bucle_nube(self) -> None:
        async with httpx.AsyncClient(timeout=5.0) as c:
            while True:
                t0 = time.perf_counter()
                try:
                    r = await c.get(self.cfg.nube_url)
                    ms = (time.perf_counter() - t0) * 1000
                    self.lat.agregar("nube_rtt_ms", ms)
                    self.nube = {"activa": True, "ok": r.status_code < 500, "ms": round(ms, 1),
                                 "destino": httpx.URL(self.cfg.nube_url).host}
                except httpx.HTTPError as e:
                    self.nube = {"activa": True, "ok": False, "error": type(e).__name__,
                                 "destino": httpx.URL(self.cfg.nube_url).host}
                await asyncio.sleep(self.cfg.nube_intervalo_s)

    async def _bucle_influx(self) -> None:
        ultima_lat = 0.0
        while True:
            try:
                ahora = time.time()
                con_lat = ahora - ultima_lat >= self.cfg.influx_latencia_intervalo_s
                self.muestra_influx(ahora, latencias=con_lat)
                if con_lat:
                    ultima_lat = ahora
                await self.influx.enviar()
            except Exception:  # nunca tumbar el borde por InfluxDB
                log.exception("Error escribiendo en InfluxDB")
            await asyncio.sleep(self.cfg.influx_intervalo_s)
