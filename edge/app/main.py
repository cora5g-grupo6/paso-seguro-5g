"""API y tablero del servidor de borde de Paso Seguro 5G.

Arranque:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.config import BASE, Config
from app.estado import Estado
from app.sistema import VERSION, Sistema

ESTATICO = BASE / "static"
SIN_CACHE = {"Cache-Control": "no-store", "Access-Control-Allow-Origin": "*"}


class Entrada(BaseModel):
    # NaN o infinito romperían el JSON del tablero: se rechazan con 422
    model_config = ConfigDict(allow_inf_nan=False)


class LecturaSensor(Entrada):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    id: str = Field("esp32", max_length=64)
    nivel_pct: float | None = None
    flotador: bool | None = None
    rtt_ms: float | None = None


class PedidoManual(Entrada):
    estado: Estado | None = None
    motivo: str = Field("", max_length=200)
    minutos: float = Field(120, gt=0, le=24 * 60)


class PedidoAck(Entrada):
    cliente: str = Field("guia", max_length=64)
    t_recibido_ms: float | None = None


class PedidoLatenciaCliente(Entrada):
    cliente: str = Field(max_length=64)
    rtt_ms: list[float] = Field(default_factory=list, max_length=200)


class DemoNivel(Entrada):
    nivel_pct: float = Field(ge=0, le=110)
    fuente: str = "camara"


class DemoLluvia(Entrada):
    mm_1h: float = Field(ge=0, le=500)
    mm_3h: float | None = Field(None, ge=0, le=1500)
    minutos: float = Field(10, gt=0, le=240)


class PedidoCalibracion(Entrada):
    roi: list[int] = Field(min_length=4, max_length=4)
    y_cero: int
    y_cien: int
    punto_agua: list[int] = Field(min_length=2, max_length=2)
    modo: str | None = None
    ref_roi: list[int] | None = Field(None, min_length=4, max_length=4)


def _sse(tipo: str, datos) -> str:
    return f"event: {tipo}\ndata: {json.dumps(datos, ensure_ascii=False, default=str)}\n\n"


def crear_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config()
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sistema = Sistema(cfg)

    @asynccontextmanager
    async def ciclo(_app: FastAPI):
        await sistema.iniciar()
        try:
            yield
        finally:
            await sistema.detener()

    app = FastAPI(title="Paso Seguro 5G · servidor de borde", version=VERSION, lifespan=ciclo)
    app.state.sistema = sistema

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(_request: Request, exc: RequestValidationError):
        # sin repetir los valores recibidos: un NaN haría fallar la respuesta misma
        errores = [{"campo": ".".join(str(p) for p in e.get("loc", ())), "error": e.get("msg", "")} for e in exc.errors()]
        return JSONResponse({"detail": errores}, status_code=422)

    # -- páginas -------------------------------------------------------------------------
    def pagina(archivo: str):
        async def servir():
            return FileResponse(ESTATICO / archivo, headers={"Cache-Control": "no-cache"})

        return servir

    for ruta, archivo in (("/", "index.html"), ("/guia", "guia.html"), ("/turista", "turista.html"),
                          ("/calibrar", "calibrar.html"), ("/medir", "medir.html")):
        app.add_api_route(ruta, pagina(archivo), methods=["GET"], include_in_schema=False)

    # -- latencia y salud -------------------------------------------------------------------
    @app.get("/ping")
    async def ping():
        return JSONResponse({"pong": True, "t_srv": time.time() * 1000}, headers=SIN_CACHE)

    @app.get("/salud")
    async def salud():
        return sistema.salud()

    @app.get("/api/latencia")
    async def latencia():
        return sistema.lat.resumen()

    @app.post("/api/latencia/cliente")
    async def latencia_cliente(p: PedidoLatenciaCliente):
        return sistema.latencia_cliente(p.cliente, p.rtt_ms)

    # -- estado ---------------------------------------------------------------------------
    @app.get("/api/estado")
    async def estado():
        return JSONResponse(sistema.snapshot(), headers=SIN_CACHE)

    @app.get("/api/cruce")
    async def cruce():
        return sistema.cruce.a_dict()

    @app.post("/api/sensor")
    async def sensor(lectura: LecturaSensor):
        return sistema.registrar_sensor(lectura.model_dump(), "http")

    @app.post("/api/manual")
    async def manual(p: PedidoManual):
        return sistema.fijar_manual(p.estado, p.motivo, p.minutos)

    @app.get("/api/imn")
    async def imn():
        return {"estado": sistema.imn_estado, "cruce": sistema.lluvia, "estaciones": sistema.lluvia_estaciones}

    @app.get("/api/stream")
    async def stream(request: Request, max_eventos: int | None = None):
        cola = sistema.suscribir()

        async def generar():
            enviados = 0
            try:
                yield _sse("estado", sistema.snapshot())
                enviados += 1
                if max_eventos and enviados >= max_eventos:
                    return
                yield _sse("latencia", sistema.lat.resumen())
                while True:
                    try:
                        tipo, datos = await asyncio.wait_for(cola.get(), timeout=15)
                    except asyncio.TimeoutError:
                        if await request.is_disconnected():
                            return
                        yield ": latido\n\n"
                        continue
                    yield _sse(tipo, datos)
                    enviados += 1
                    if max_eventos and enviados >= max_eventos:
                        return
            finally:
                sistema.desuscribir(cola)

        return StreamingResponse(generar(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # -- eventos y alertas --------------------------------------------------------------------
    @app.get("/api/eventos")
    async def eventos(n: int = 50):
        return list(sistema.eventos)[: max(1, min(n, 200))]

    @app.get("/api/eventos/{eid}")
    async def evento(eid: str):
        ev = sistema.buscar_evento(eid)
        if ev is None:
            raise HTTPException(404, "No existe ese evento")
        return ev

    @app.post("/api/alertas/{eid}/ack")
    async def ack(eid: str, p: PedidoAck):
        try:
            return sistema.ack(eid, p.cliente, p.t_recibido_ms)
        except KeyError:
            raise HTTPException(404, "No existe esa alerta") from None

    # -- cámara ---------------------------------------------------------------------------------
    @app.get("/api/camara/captura.jpg")
    async def captura(crudo: bool = False):
        jpg = sistema.jpeg_actual(crudo)
        if jpg is None:
            raise HTTPException(503, "Sin cámara o todavía sin cuadros")
        return Response(jpg, media_type="image/jpeg", headers=SIN_CACHE)

    @app.get("/video.mjpg")
    async def video(request: Request):
        if not sistema.vision:
            raise HTTPException(503, "Sin cámara")

        async def generar():
            ultimo = None
            pausa = 1 / max(1.0, cfg.camara_mjpeg_fps)
            while not await request.is_disconnected():
                jpg = sistema.vision.jpeg
                if jpg is not None and jpg is not ultimo:
                    ultimo = jpg
                    yield (b"--cuadro\r\nContent-Type: image/jpeg\r\nContent-Length: "
                           + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                await asyncio.sleep(pausa)

        return StreamingResponse(generar(), media_type="multipart/x-mixed-replace; boundary=cuadro",
                                 headers={"Cache-Control": "no-store"})

    @app.post("/api/camara/frame")
    async def frame(request: Request):
        if not sistema.camara:
            raise HTTPException(503, "La cámara está apagada (CAMARA_ACTIVA=false)")
        datos = await request.body()
        if len(datos) > 5_000_000:
            raise HTTPException(413, "Cuadro demasiado grande")
        if not sistema.camara.recibir_jpeg(datos):
            raise HTTPException(400, "No es un JPEG válido")
        return {"ok": True}

    @app.get("/api/camara/calibracion")
    async def ver_calibracion():
        return sistema.calibracion.a_dict() if sistema.calibracion else {}

    @app.post("/api/camara/calibracion")
    async def calibrar(p: PedidoCalibracion):
        try:
            return sistema.calibrar(p.model_dump())
        except RuntimeError as e:
            raise HTTPException(409, str(e)) from None

    # -- feeds públicos ---------------------------------------------------------------------------
    @app.get("/feeds/waze.json")
    async def waze_json(envuelto: bool = False):
        return JSONResponse(sistema.feed_waze_json(envuelto), headers=SIN_CACHE)

    @app.get("/feeds/waze.xml")
    async def waze_xml():
        return Response(sistema.feed_waze_xml(), media_type="application/xml", headers=SIN_CACHE)

    @app.get("/feeds/estado.geojson")
    async def estado_geojson():
        return JSONResponse(sistema.feed_estado_geojson(), media_type="application/geo+json", headers=SIN_CACHE)

    @app.get("/feeds/google-cierres.geojson")
    async def google_cierres():
        return JSONResponse(sistema.feed_google(), media_type="application/geo+json", headers=SIN_CACHE)

    @app.get("/feeds/validacion")
    async def validacion():
        return sistema.validar_feeds()

    # -- modo demo (ensayos sin hardware) ------------------------------------------------------------
    if cfg.modo_demo:

        @app.post("/api/demo/nivel")
        async def demo_nivel(p: DemoNivel):
            return sistema.demo_nivel(p.nivel_pct, p.fuente)

        @app.post("/api/demo/lluvia")
        async def demo_lluvia(p: DemoLluvia):
            return sistema.demo_lluvia(p.mm_1h, p.mm_3h, p.minutos)

        @app.post("/api/demo/persona")
        async def demo_persona():
            return sistema.demo_persona()

        @app.post("/api/demo/reiniciar")
        async def demo_reiniciar():
            return sistema.reiniciar()

    app.mount("/static", StaticFiles(directory=ESTATICO), name="static")
    app.mount("/media/eventos", StaticFiles(directory=sistema.carpeta_eventos, check_dir=False), name="media")
    return app


def __getattr__(nombre: str):
    """`app.main:app` se crea al pedirlo (uvicorn), no al importar el módulo (tests)."""
    if nombre == "app":
        globals()["app"] = crear_app()
        return globals()["app"]
    raise AttributeError(nombre)
