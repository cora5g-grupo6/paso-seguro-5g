"""Hilo de visión: toma el cuadro más reciente, mide nivel y personas, dibuja y comprime a JPEG.

El resultado sale por el callback `al_resultado(res_nivel, res_personas, t_captura, ms)`.
El sistema lo pasa al hilo del event loop con call_soon_threadsafe.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from pathlib import Path
from statistics import median
from typing import Callable

import cv2
import numpy as np

from app.vision.nivel import CalibracionNivel, ResultadoNivel, dibujar, medir_nivel
from app.vision.personas import DetectorPersonas, ResultadoPersonas

log = logging.getLogger("paso_seguro.vision")


class TrabajadorVision:
    def __init__(
        self,
        camara,
        calibracion: CalibracionNivel,
        detector: DetectorPersonas | None,
        fps: float,
        al_resultado: Callable[[ResultadoNivel, ResultadoPersonas | None, float, float], None],
        umbrales: tuple[float, float] = (40, 70),
        mediana: int = 3,
        clip_s: float = 10,
        clip_fps: float = 2,
    ):
        self.camara = camara
        self.cal = calibracion
        self.detector = detector
        self.fps = max(0.5, fps)
        self.al_resultado = al_resultado
        self.umbrales = umbrales
        self.estado_txt: str | None = None  # lo pone el sistema para dibujarlo en el video
        self.jpeg: bytes | None = None  # último cuadro dibujado (para el video MJPEG)
        self.crudo: np.ndarray | None = None  # último cuadro sin dibujar (para calibrar)
        self.ultimo: ResultadoNivel | None = None
        self.personas: ResultadoPersonas | None = None
        self._hist: deque[float] = deque(maxlen=max(1, mediana))
        self._clip: deque[bytes] = deque(maxlen=int(clip_s * clip_fps))
        self._clip_cada = 1.0 / clip_fps
        self._t_clip = 0.0
        self._corriendo = False
        self._hilo: threading.Thread | None = None

    def iniciar(self) -> None:
        self._corriendo = True
        self._hilo = threading.Thread(target=self._bucle, name="vision", daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=3)

    def aplicar_calibracion(self, cal: CalibracionNivel) -> None:
        self.cal = cal
        self._hist.clear()

    def _bucle(self) -> None:
        ultimo_seq = -1
        while self._corriendo:
            t_vuelta = time.time()
            frame, t_cap, seq = self.camara.ultimo()
            if frame is None or seq == ultimo_seq:
                time.sleep(0.02)
                continue
            ultimo_seq = seq
            try:
                self._procesar(frame, t_cap)
            except Exception:  # un cuadro raro no puede tumbar el hilo
                log.exception("Error analizando un cuadro")
            espera = 1.0 / self.fps - (time.time() - t_vuelta)
            if espera > 0:
                time.sleep(espera)

    def _procesar(self, frame: np.ndarray, t_cap: float) -> None:
        t0 = time.perf_counter()
        res = medir_nivel(frame, self.cal)
        if res.nivel_pct is not None and res.confianza >= 0.5:
            self._hist.append(res.nivel_pct)  # mediana: una mano frente al tubo no cierra el cruce
            res = ResultadoNivel(round(median(self._hist), 1), res.confianza, res.y_superficie, res.motivo)
        else:
            self._hist.clear()
        per = self.detector.procesar(frame) if self.detector else None
        ms = (time.perf_counter() - t0) * 1000
        self.ultimo, self.personas, self.crudo = res, per, frame
        self.al_resultado(res, per, t_cap, ms)
        img = dibujar(frame, self.cal, res, self.umbrales, self.estado_txt, per.cajas if per else None)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            self.jpeg = buf.tobytes()
            if time.time() - self._t_clip >= self._clip_cada:
                self._clip.append(self.jpeg)
                self._t_clip = time.time()

    def guardar_evento(self, carpeta: Path) -> list[str]:
        """Guarda la captura y los últimos segundos (2 cuadros/s) para la alerta con video."""
        carpeta.mkdir(parents=True, exist_ok=True)
        if self.jpeg:
            (carpeta / "captura.jpg").write_bytes(self.jpeg)
        nombres = []
        for k, jpg in enumerate(list(self._clip)):
            nombre = f"{k:02d}.jpg"
            (carpeta / nombre).write_bytes(jpg)
            nombres.append(nombre)
        return nombres
