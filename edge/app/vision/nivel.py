"""Lectura del nivel del agua por color, en CPU (OpenCV), sin modelos ni GPU.

Maqueta: tubo transparente con agua teñida (colorante) y una regla pintada al lado.
- modo "columna": busca la columna de agua del color calibrado y toma su borde de arriba.
- modo "marcador": sigue un flotador de color (pelota) dentro del tubo.

La calibración usa píxeles del cuadro ya reducido al ancho de análisis:
  roi = zona del tubo (x, y, ancho, alto), y_cero = fila del 0 %, y_cien = fila del 100 %,
  y el rango HSV del agua. Se puede hacer con clics en /calibrar.
Si hay una marca de referencia fija configurada y no se ve, la lectura no vale
(cámara movida o tapada): la IA dice cuándo no ve.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

import cv2
import numpy as np

log = logging.getLogger("paso_seguro.vision")

Rect = tuple[int, int, int, int]
HSV = tuple[int, int, int]


@dataclass(frozen=True)
class CalibracionNivel:
    roi: Rect = (0, 0, 0, 0)
    y_cero: int = 0
    y_cien: int = 0
    hsv_bajo: HSV = (90, 80, 40)  # agua teñida de azul (OpenCV: tono 0-179)
    hsv_alto: HSV = (130, 255, 255)
    fraccion_fila: float = 0.35  # fracción de píxeles de agua para que una fila cuente
    hueco_max_pct: float = 4.0  # huecos tolerados en la columna (rayas de la regla, burbujas)
    modo: str = "columna"  # "columna" o "marcador"
    area_min_marcador: int = 60
    ref_roi: Rect | None = None  # marca de referencia fija (opcional)
    ref_hsv_bajo: HSV = (140, 80, 80)  # magenta
    ref_hsv_alto: HSV = (170, 255, 255)
    ref_fraccion_min: float = 0.05
    brillo_min: float = 25.0
    contraste_min: float = 4.0

    @property
    def calibrada(self) -> bool:
        _, _, w, h = self.roi
        return w > 4 and h > 4 and self.y_cero != self.y_cien

    def a_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, d: dict) -> "CalibracionNivel":
        validos = {f.name for f in fields(cls)}
        datos = {k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items() if k in validos}
        return cls(**datos)


def cargar_calibracion(ruta: str | Path) -> CalibracionNivel | None:
    """None si no existe o está dañada: el borde arranca igual y pide calibrar."""
    p = Path(ruta)
    if not p.exists():
        return None
    try:
        return CalibracionNivel.desde_dict(json.loads(p.read_text(encoding="utf-8")))
    except (ValueError, TypeError, OSError) as e:
        log.warning("Calibración dañada en %s (%s): hay que calibrar de nuevo", p, e)
        return None


def guardar_calibracion(cal: CalibracionNivel, ruta: str | Path) -> None:
    p = Path(ruta)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")  # escritura atómica: nunca queda un archivo a medias
    tmp.write_text(json.dumps(cal.a_dict(), indent=1), encoding="utf-8")
    tmp.replace(p)


@dataclass
class ResultadoNivel:
    nivel_pct: float | None
    confianza: float
    y_superficie: int | None = None
    motivo: str = ""

    def a_dict(self) -> dict:
        return asdict(self)


def _mascara(hsv: np.ndarray, bajo: HSV, alto: HSV) -> np.ndarray:
    if bajo[0] <= alto[0]:
        return cv2.inRange(hsv, np.array(bajo, np.uint8), np.array(alto, np.uint8))
    # el tono da la vuelta (rojos): dos rangos
    m1 = cv2.inRange(hsv, np.array(bajo, np.uint8), np.array((179, alto[1], alto[2]), np.uint8))
    m2 = cv2.inRange(hsv, np.array((0, bajo[1], bajo[2]), np.uint8), np.array(alto, np.uint8))
    return m1 | m2


def _recortar(frame: np.ndarray, rect: Rect) -> tuple[np.ndarray, int, int]:
    x, y, w, h = (int(v) for v in rect)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
    return frame[y0:y1, x0:x1], x0, y0


def _a_pct(cal: CalibracionNivel, y: float) -> float:
    return (cal.y_cero - y) / (cal.y_cero - cal.y_cien) * 100.0


def medir_nivel(frame: np.ndarray | None, cal: CalibracionNivel) -> ResultadoNivel:
    if frame is None or not cal.calibrada:
        return ResultadoNivel(None, 0.0, motivo="Falta calibrar la cámara")
    gris = cv2.cvtColor(cv2.resize(frame, (160, 120)), cv2.COLOR_BGR2GRAY)
    if gris.mean() < cal.brillo_min:
        return ResultadoNivel(None, 0.0, motivo="Imagen muy oscura: ¿cámara tapada o sin luz?")
    if gris.std() < cal.contraste_min:
        return ResultadoNivel(None, 0.0, motivo="Imagen sin detalle: ¿cámara tapada o desenfocada?")
    if cal.ref_roi:
        ref, _, _ = _recortar(frame, cal.ref_roi)
        visto = 0.0
        if ref.size:
            visto = float((_mascara(cv2.cvtColor(ref, cv2.COLOR_BGR2HSV), cal.ref_hsv_bajo, cal.ref_hsv_alto) > 0).mean())
        if visto < cal.ref_fraccion_min:
            return ResultadoNivel(None, 0.0, motivo="No se ve la marca de referencia: ¿cámara movida o tapada?")
    zona, ox, oy = _recortar(frame, cal.roi)
    if zona.size == 0:
        return ResultadoNivel(None, 0.0, motivo="La zona del tubo quedó fuera del cuadro")
    m = _mascara(cv2.cvtColor(zona, cv2.COLOR_BGR2HSV), cal.hsv_bajo, cal.hsv_alto)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    if cal.modo == "marcador":
        return _medir_marcador(m, cal, oy)
    return _medir_columna(m, cal, oy)


def _medir_columna(m: np.ndarray, cal: CalibracionNivel, oy: int) -> ResultadoNivel:
    frac = (m > 0).mean(axis=1)
    agua = frac >= cal.fraccion_fila
    alto = len(agua)
    fila0 = int(np.clip(cal.y_cero - oy, 0, alto - 1))
    hueco_max = max(2, int(abs(cal.y_cero - cal.y_cien) * cal.hueco_max_pct / 100))
    # base de la columna: primera fila con agua subiendo desde el 0 %
    i = fila0
    while i >= 0 and not agua[i] and fila0 - i <= hueco_max:
        i -= 1
    if i < 0 or not agua[i]:
        return ResultadoNivel(0.0, 0.9, y_superficie=int(cal.y_cero))  # tubo vacío
    # subir mientras haya agua, tolerando huecos cortos
    sup, hueco, j = i, 0, i
    while j >= 0:
        if agua[j]:
            sup, hueco = j, 0
        else:
            hueco += 1
            if hueco > hueco_max:
                break
        j -= 1
    y_sup = sup + oy
    solidez = float(frac[sup : i + 1].mean())
    nivel = float(np.clip(_a_pct(cal, y_sup), 0, 110))
    return ResultadoNivel(round(nivel, 1), round(min(1.0, solidez / 0.7), 2), int(y_sup))


def _medir_marcador(m: np.ndarray, cal: CalibracionNivel, oy: int) -> ResultadoNivel:
    n, _, stats, centros = cv2.connectedComponentsWithStats(m)
    if n <= 1:
        return ResultadoNivel(None, 0.0, motivo="No se ve el flotador de color en el tubo")
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = int(stats[k, cv2.CC_STAT_AREA])
    if area < cal.area_min_marcador:
        return ResultadoNivel(None, 0.0, motivo="El flotador de color se ve muy pequeño")
    cy = float(centros[k][1]) + oy
    nivel = float(np.clip(_a_pct(cal, cy), 0, 110))
    return ResultadoNivel(round(nivel, 1), round(min(1.0, area / (cal.area_min_marcador * 4)), 2), int(cy))


def calibracion_desde_clics(
    frame: np.ndarray,
    roi: Rect,
    y_cero: int,
    y_cien: int,
    punto_agua: tuple[int, int],
    radio: int = 6,
    base: CalibracionNivel | None = None,
) -> CalibracionNivel:
    """Arma la calibración con 4 datos tomados con clics y una muestra del color del agua."""
    x, y = (int(v) for v in punto_agua)
    parche = frame[max(0, y - radio) : y + radio + 1, max(0, x - radio) : x + radio + 1]
    h, s, v = np.median(cv2.cvtColor(parche, cv2.COLOR_BGR2HSV).reshape(-1, 3), axis=0)
    bajo = (int((h - 12) % 180), int(max(40, s - 70)), int(max(40, v - 80)))
    alto = (int((h + 12) % 180), 255, 255)
    return replace(
        base or CalibracionNivel(),
        roi=tuple(int(a) for a in roi),
        y_cero=int(y_cero),
        y_cien=int(y_cien),
        hsv_bajo=bajo,
        hsv_alto=alto,
    )


COLORES_BGR = {"LIBRE": (62, 142, 30), "CUIDADO": (0, 171, 249), "CERRADO": (37, 48, 217)}


def dibujar(
    frame: np.ndarray,
    cal: CalibracionNivel,
    res: ResultadoNivel,
    umbrales: tuple[float, float] = (40, 70),
    estado: str | None = None,
    personas: list[Rect] | None = None,
) -> np.ndarray:
    """Copia del cuadro con la zona del tubo, los umbrales, la superficie y el estado."""
    out = frame.copy()
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    if cal.calibrada:
        x, y, w, h = cal.roi
        cv2.rectangle(out, (x, y), (x + w, y + h), (255, 255, 255), 1)
        for pct, color in zip(umbrales, ((0, 200, 255), (0, 0, 255))):
            yy = int(round(cal.y_cero - (cal.y_cero - cal.y_cien) * pct / 100))
            cv2.line(out, (x - 12, yy), (x + w + 12, yy), color, 1)
            cv2.putText(out, f"{pct:.0f}%", (x + w + 14, yy + 4), fuente, 0.4, color, 1, cv2.LINE_AA)
        if res.y_superficie is not None:
            cv2.line(out, (x - 18, res.y_superficie), (x + w + 18, res.y_superficie), (255, 255, 0), 2)
    if cal.ref_roi:
        rx, ry, rw, rh = cal.ref_roi
        cv2.rectangle(out, (rx, ry), (rx + rw, ry + rh), (255, 0, 255), 1)
    for (px, py, pw, ph) in personas or []:
        cv2.rectangle(out, (px, py), (px + pw, py + ph), (0, 0, 255), 2)
        cv2.putText(out, "persona", (px, max(12, py - 4)), fuente, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
    texto = f"Nivel {res.nivel_pct:.0f} %" if res.nivel_pct is not None else (res.motivo or "Sin lectura")
    color_estado = COLORES_BGR.get(estado or "", (90, 90, 90))
    cv2.rectangle(out, (0, 0), (out.shape[1], 26), (20, 20, 20), -1)
    if estado:
        cv2.rectangle(out, (0, 0), (110, 26), color_estado, -1)
        cv2.putText(out, estado, (6, 18), fuente, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(out, texto, (118 if estado else 6, 18), fuente, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return out
