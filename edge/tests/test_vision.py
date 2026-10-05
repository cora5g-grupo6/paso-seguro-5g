"""Tests de visión con cuadros sintéticos: tubo con agua teñida y regla pintada."""

from dataclasses import replace

import cv2
import numpy as np
import pytest

from app.camara import Camara
from app.vision.nivel import (
    CalibracionNivel,
    calibracion_desde_clics,
    cargar_calibracion,
    dibujar,
    guardar_calibracion,
    medir_nivel,
)
from app.vision.personas import DetectorPersonas

ALTO, ANCHO = 480, 640
X0, X1 = 280, 360  # paredes del tubo
Y_CIEN, Y_CERO = 60, 420  # filas de las marcas de 100 % y 0 %
AZUL = (200, 90, 20)  # BGR del agua teñida con colorante azul
MAGENTA = (255, 0, 255)


def tubo(nivel_pct, agua=AZUL, marcas=True, ref=True, semilla=1):
    rng = np.random.default_rng(semilla)
    img = np.full((ALTO, ANCHO, 3), 205, np.uint8)
    img = np.clip(img.astype(int) + rng.integers(-8, 9, img.shape), 0, 255).astype(np.uint8)
    cv2.rectangle(img, (X0 - 3, Y_CIEN - 12), (X1 + 3, Y_CERO + 3), (165, 165, 165), 2)
    if nivel_pct > 0:
        y_sup = int(round(Y_CERO - (Y_CERO - Y_CIEN) * nivel_pct / 100))
        img[y_sup:Y_CERO, X0:X1] = agua
    if marcas:  # regla pintada: rayas negras cada 10 %
        for p in range(0, 101, 10):
            y = int(round(Y_CERO - (Y_CERO - Y_CIEN) * p / 100))
            cv2.line(img, (X0, y), (X0 + 25, y), (30, 30, 30), 2)
    if ref:  # marca de referencia fija junto al tubo
        cv2.rectangle(img, (X1 + 20, Y_CIEN - 5), (X1 + 40, Y_CIEN + 15), MAGENTA, -1)
    return img


CAL = CalibracionNivel(
    roi=(X0, Y_CIEN - 20, X1 - X0, Y_CERO - Y_CIEN + 30),
    y_cero=Y_CERO,
    y_cien=Y_CIEN,
    hsv_bajo=(90, 80, 40),
    hsv_alto=(130, 255, 255),
)


@pytest.mark.parametrize("nivel", [10, 35, 50, 72, 95])
def test_lee_el_nivel_del_agua_tenida(nivel):
    r = medir_nivel(tubo(nivel), CAL)
    assert r.nivel_pct == pytest.approx(nivel, abs=3)
    assert r.confianza >= 0.8


def test_tubo_vacio_lee_cero():
    r = medir_nivel(tubo(0), CAL)
    assert r.nivel_pct == pytest.approx(0, abs=2)
    assert r.confianza >= 0.5


def test_camara_tapada_no_da_lectura():
    r = medir_nivel(np.zeros((ALTO, ANCHO, 3), np.uint8), CAL)
    assert r.nivel_pct is None
    assert r.confianza == 0
    assert r.motivo


def test_sin_la_marca_de_referencia_no_confia():
    cal = replace(CAL, ref_roi=(X1 + 15, Y_CIEN - 10, 30, 30), ref_hsv_bajo=(140, 80, 80), ref_hsv_alto=(170, 255, 255))
    assert medir_nivel(tubo(50, ref=True), cal).confianza >= 0.8
    r = medir_nivel(tubo(50, ref=False), cal)
    assert r.confianza == 0
    assert "referencia" in r.motivo


def test_sin_calibrar_no_mide():
    r = medir_nivel(tubo(50), CalibracionNivel())
    assert r.nivel_pct is None and r.confianza == 0


def test_calibracion_con_clics_toma_el_color_del_agua():
    img = tubo(60, agua=(40, 160, 40))  # agua teñida de verde
    cal = calibracion_desde_clics(img, roi=CAL.roi, y_cero=Y_CERO, y_cien=Y_CIEN, punto_agua=(320, 400))
    assert medir_nivel(img, cal).nivel_pct == pytest.approx(60, abs=3)


def test_modo_marcador_sigue_un_flotador_de_color():
    img = tubo(0)
    y = Y_CERO - (Y_CERO - Y_CIEN) * 45 // 100
    cv2.circle(img, (320, y), 18, (0, 140, 255), -1)  # pelota naranja
    cal = replace(CAL, modo="marcador", hsv_bajo=(5, 120, 120), hsv_alto=(22, 255, 255))
    assert medir_nivel(img, cal).nivel_pct == pytest.approx(45, abs=3)


def test_dibujar_marca_la_lectura_sobre_el_cuadro():
    img = tubo(50)
    out = dibujar(img, CAL, medir_nivel(img, CAL), estado="CUIDADO")
    assert out.shape == img.shape
    assert not np.array_equal(out, img)


def test_calibracion_truncada_no_impide_arrancar(tmp_path):
    archivo = tmp_path / "calibracion.json"
    archivo.write_text('{"roi": [1, 2,')  # se cortó al guardar
    assert cargar_calibracion(archivo) is None


def test_calibracion_valida_se_guarda_y_se_lee(tmp_path):
    archivo = tmp_path / "config" / "calibracion.json"
    guardar_calibracion(CAL, archivo)
    assert cargar_calibracion(archivo) == CAL


def test_cuadro_vacio_o_roto_no_se_acepta():
    cam = Camara([])
    assert cam.recibir_jpeg(b"") is False
    assert cam.recibir_jpeg(b"no es un jpeg") is False


def test_movimiento_en_la_zona_cuenta_como_persona():
    det = DetectorPersonas(metodo="movimiento", zona=(0, 0, 200, 480), cada_n=1)
    fondo = tubo(20)
    for _ in range(15):
        det.procesar(fondo)  # aprende el fondo
    con_persona = fondo.copy()
    cv2.rectangle(con_persona, (60, 150), (140, 400), (60, 60, 60), -1)
    assert det.procesar(con_persona).en_zona >= 1


def test_hog_no_inventa_personas():
    r = DetectorPersonas(metodo="hog", cada_n=1).procesar(tubo(50))
    assert r.cantidad == 0


def test_detector_apagado_no_hace_nada():
    r = DetectorPersonas(metodo="apagado").procesar(tubo(50))
    assert r.cantidad == 0 and r.metodo == "apagado"
