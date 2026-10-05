"""Lector de cámara en su propio hilo.

CAMARA_FUENTES: lista por orden de preferencia, separada por comas.
  rtsp://usuario:clave@IP:554/ruta   cámara 5G por la red privada (plan A)
  0                                  webcam USB (índice de OpenCV) (plan B)
  http://IP:8080/video               MJPEG por HTTP, p. ej. un teléfono como cámara IP (plan B)
  ../tools/videos/rio_prueba.mp4     video de prueba en bucle (ensayos)
Además, cualquier equipo puede empujar cuadros JPEG a POST /api/camara/frame (plan C).

Se guarda solo el cuadro más reciente: si el análisis se atrasa, se saltan cuadros
en vez de acumular retraso.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from pathlib import Path

# RTSP por TCP y sin búfer: menos cortes y menos retraso. Tiene que estar antes de abrir capturas.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay")

import cv2  # noqa: E402
import numpy as np  # noqa: E402

log = logging.getLogger("paso_seguro.camara")


def ocultar_clave(fuente: str | None) -> str | None:
    if fuente is None:
        return None
    return re.sub(r"//[^@/]+@", "//***@", fuente)


def _opencv_tiene_ffmpeg() -> bool:
    m = re.search(r"FFMPEG:\s*(\w+)", cv2.getBuildInformation())
    return bool(m and m.group(1).upper() == "YES")


# El OpenCV de pip para Linux y Windows trae FFmpeg (lee RTSP); el de Mac no.
OPENCV_FFMPEG = _opencv_tiene_ffmpeg()


class LectorPyAV:
    """Lector RTSP/HTTP/archivo con PyAV (FFmpeg incluido en el paquete `av`).

    Se usa cuando OpenCV no trae FFmpeg (Mac) o si CAMARA_LECTOR=pyav.
    Imita lo poco que el bucle usa de cv2.VideoCapture.
    """

    def __init__(self, fuente: str, timeout_s: float = 5.0):
        import av

        opciones = {}
        if "://" in fuente:  # en vivo: sin búfer; en archivos se decodifica todo normal
            opciones = {"fflags": "nobuffer", "flags": "low_delay"}
        if fuente.startswith("rtsp://"):
            opciones["rtsp_transport"] = "tcp"
        self._c = av.open(fuente, options=opciones, timeout=timeout_s)
        self._s = self._c.streams.video[0]
        # sin hilos por cuadro: el decodificado multihilo retiene cuadros y suma retraso en vivo
        self._cuadros = self._c.decode(self._s)
        self._fps = float(self._s.average_rate or 0)

    def isOpened(self) -> bool:  # noqa: N802 (misma interfaz que OpenCV)
        return True

    def read(self):
        try:
            return True, next(self._cuadros).to_ndarray(format="bgr24")
        except Exception:  # fin del archivo, corte de red o cuadro dañado
            return False, None

    def get(self, prop) -> float:
        return self._fps if prop == cv2.CAP_PROP_FPS else 0.0

    def set(self, *_args) -> bool:
        return False

    def release(self) -> None:
        try:
            self._c.close()
        except Exception:
            pass


class Camara:
    def __init__(self, fuentes: list[str], ancho: int = 640, base: Path | None = None, espera_s: float = 3.0,
                 lector: str = "auto"):
        self.fuentes = fuentes
        self.ancho = ancho
        self.base = base
        self.espera_s = espera_s
        self.lector = lector  # auto | opencv | pyav
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self._t = 0.0
        self._seq = 0
        self._t_push = 0.0
        self.fuente_activa: str | None = None
        self.conectada = False
        self.fps = 0.0
        self.errores = 0
        self.ultimo_error = ""
        self._corriendo = False
        self._hilo: threading.Thread | None = None

    # -- ciclo de vida ---------------------------------------------------------

    def iniciar(self) -> None:
        if not self.fuentes or self._corriendo:
            return  # sin fuentes: solo recibe cuadros empujados
        self._corriendo = True
        self._hilo = threading.Thread(target=self._bucle, name="camara", daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=3)

    # -- lectura -----------------------------------------------------------------

    def ultimo(self) -> tuple[np.ndarray | None, float, int]:
        with self._lock:
            return self._frame, self._t, self._seq

    def recibir_jpeg(self, datos: bytes) -> bool:
        if not datos:
            return False
        try:
            img = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            return False
        if img is None:
            return False
        ahora = time.time()
        self._publicar(img, ahora)
        self._t_push = ahora
        self.fuente_activa = "push"
        self.conectada = True
        return True

    def estado(self) -> dict:
        _, t, seq = self.ultimo()
        return {
            "activa": True,
            "lector": self.lector if self.lector != "auto" else ("opencv" if OPENCV_FFMPEG else "pyav para RTSP"),
            "fuentes": [ocultar_clave(f) for f in self.fuentes],
            "fuente": ocultar_clave(self.fuente_activa),
            "conectada": self.conectada and (time.time() - t < 5 if t else False),
            "fps": round(self.fps, 1),
            "cuadros": seq,
            "edad_s": round(time.time() - t, 1) if t else None,
            "errores": self.errores,
            "ultimo_error": self.ultimo_error,
        }

    # -- interno -------------------------------------------------------------------

    def _publicar(self, img: np.ndarray, t: float) -> None:
        if self.ancho and img.shape[1] > self.ancho:
            alto = int(round(img.shape[0] * self.ancho / img.shape[1]))
            img = cv2.resize(img, (self.ancho, alto), interpolation=cv2.INTER_AREA)
        with self._lock:
            dt = t - self._t if self._t else 0.0
            self._frame, self._t, self._seq = img, t, self._seq + 1
        if dt > 0:
            self.fps = (0.9 * self.fps + 0.1 / dt) if self.fps else 1 / dt

    def _pyav(self, fuente: str):
        try:
            return LectorPyAV(fuente)
        except ImportError:
            self.ultimo_error = "Este OpenCV no lee RTSP: instale PyAV (pip install av) o use Docker/Linux"
        except Exception as e:
            self.ultimo_error = f"No abre {ocultar_clave(fuente)} ({type(e).__name__})"
        return None

    def _abrir(self, fuente: str):
        """Devuelve (captura, es_archivo). La captura es cv2.VideoCapture o LectorPyAV."""
        usar_pyav = self.lector == "pyav" or (self.lector == "auto" and not OPENCV_FFMPEG)
        if fuente.isdigit():
            cap, archivo = cv2.VideoCapture(int(fuente)), False
        elif "://" in fuente:
            if usar_pyav:
                return self._pyav(fuente), False
            params = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000]
            cap, archivo = cv2.VideoCapture(fuente, cv2.CAP_FFMPEG, params), False
        else:
            ruta = Path(fuente).expanduser()
            if not ruta.is_absolute() and self.base:
                ruta = self.base / ruta
            if not ruta.exists():
                self.ultimo_error = f"No existe el video {ruta}"
                return None, True
            cap, archivo = cv2.VideoCapture(str(ruta)), True
            if not cap.isOpened() and self.lector != "opencv":
                cap.release()
                return self._pyav(str(ruta)), True
        if not cap.isOpened():
            cap.release()
            self.ultimo_error = f"No abre {ocultar_clave(fuente)}"
            return None, archivo
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap, archivo

    def _bucle(self) -> None:
        i = 0
        while self._corriendo:
            if time.time() - self._t_push < 3:  # alguien está empujando cuadros: no competir
                time.sleep(0.2)
                continue
            fuente = self.fuentes[i % len(self.fuentes)]
            cap, archivo = self._abrir(fuente)
            if cap is None:
                self.errores += 1
                self.conectada = False
                i += 1
                if i % len(self.fuentes) == 0:
                    time.sleep(self.espera_s)
                continue
            log.info("Cámara conectada: %s", ocultar_clave(fuente))
            self.fuente_activa, self.conectada, self.ultimo_error = fuente, True, ""
            pausa = 1.0 / (cap.get(cv2.CAP_PROP_FPS) or 15.0) if archivo else 0.0
            fallos = 0
            while self._corriendo:
                t0 = time.time()
                ok, img = cap.read()
                if not ok:
                    fallos += 1
                    if archivo:  # fin del video: volver al principio
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        if fallos > 3:
                            break
                        continue
                    if fallos > 25:
                        self.ultimo_error = f"Se cortó {ocultar_clave(fuente)}"
                        break
                    time.sleep(0.04)
                    continue
                fallos = 0
                self._publicar(img, time.time())
                if pausa:
                    time.sleep(max(0.0, pausa - (time.time() - t0)))
            cap.release()
            self.conectada = False
            log.warning("Cámara desconectada: %s", ocultar_clave(fuente))
            i = 0  # tras un corte se vuelve a intentar la fuente preferida
            time.sleep(0.5)
