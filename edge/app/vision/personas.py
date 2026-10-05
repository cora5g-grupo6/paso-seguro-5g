"""Detección liviana de personas en CPU, opcional y apagable.

- "hog": detector de peatones HOG+SVM que trae OpenCV (sin descargar modelos). Pide el cuerpo
  entero visible y de pie; corre cada N cuadros sobre una imagen reducida.
- "movimiento": resta de fondo (MOG2) dentro de la zona del cruce. Más robusto en una maqueta:
  cualquier cosa que entre a la zona cuenta. Plan B si HOG falla con la luz o el encuadre.
- "apagado": no hace nada.
No hay reconocimiento facial ni se guardan caras: solo cajas y un conteo.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

import cv2
import numpy as np

Rect = tuple[int, int, int, int]


@dataclass
class ResultadoPersonas:
    cantidad: int = 0
    en_zona: int = 0
    cajas: list[Rect] = field(default_factory=list)
    ms: float = 0.0
    metodo: str = "apagado"

    def a_dict(self) -> dict:
        return asdict(self)


def _se_tocan(a: Rect, b: Rect) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


class DetectorPersonas:
    def __init__(
        self,
        metodo: str = "hog",
        zona: Rect | None = None,
        cada_n: int = 3,
        ancho: int = 400,
        umbral_hog: float = 0.5,
        umbral_movimiento: float = 0.02,
    ):
        self.metodo = metodo if metodo in ("hog", "movimiento") else "apagado"
        self.zona = zona
        self.cada_n = max(1, int(cada_n))
        self.ancho = ancho
        self.umbral_hog = umbral_hog
        self.umbral_movimiento = umbral_movimiento
        self._n = 0
        self._ultimo = ResultadoPersonas(metodo=self.metodo)
        if self.metodo == "hog":
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        elif self.metodo == "movimiento":
            self._fondo = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)

    def procesar(self, frame: np.ndarray | None) -> ResultadoPersonas:
        if self.metodo == "apagado" or frame is None:
            return ResultadoPersonas(metodo=self.metodo)
        self._n += 1
        if (self._n - 1) % self.cada_n:
            return self._ultimo
        t0 = time.perf_counter()
        r = self._por_hog(frame) if self.metodo == "hog" else self._por_movimiento(frame)
        r.ms = round((time.perf_counter() - t0) * 1000, 1)
        self._ultimo = r
        return r

    def _por_hog(self, frame: np.ndarray) -> ResultadoPersonas:
        esc = min(1.0, self.ancho / frame.shape[1])
        peq = cv2.resize(frame, None, fx=esc, fy=esc) if esc < 1 else frame
        cajas, pesos = self._hog.detectMultiScale(
            cv2.cvtColor(peq, cv2.COLOR_BGR2GRAY), winStride=(8, 8), padding=(8, 8), scale=1.05
        )
        pesos = np.ravel(pesos) if len(pesos) else []
        sel = [tuple(int(v / esc) for v in c) for c, w in zip(cajas, pesos) if w >= self.umbral_hog]
        en_zona = sum(1 for c in sel if self.zona is None or _se_tocan(c, self.zona))
        return ResultadoPersonas(len(sel), en_zona, sel, metodo="hog")

    def _por_movimiento(self, frame: np.ndarray) -> ResultadoPersonas:
        x, y, w, h = self.zona or (0, 0, frame.shape[1], frame.shape[0])
        recorte = frame[y : y + h, x : x + w]
        if recorte.size == 0:
            return ResultadoPersonas(metodo="movimiento")
        m = self._fondo.apply(recorte)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        if float((m > 0).mean()) < self.umbral_movimiento:
            return ResultadoPersonas(metodo="movimiento")
        bx, by, bw, bh = cv2.boundingRect(cv2.findNonZero(m))
        return ResultadoPersonas(1, 1, [(bx + x, by + y, bw, bh)], metodo="movimiento")
