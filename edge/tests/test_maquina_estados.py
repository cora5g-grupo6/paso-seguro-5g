"""Tests de la máquina de estados LIBRE / CUIDADO / CERRADO.

Umbrales de prueba = los del kit del Grupo 6: CUIDADO >= 40 %, CERRADO >= 70 %,
histéresis de 10 puntos y 30 s sostenidos para bajar un escalón.
"""

from app.estado import Entradas, Estado, MaquinaEstados, Umbrales

U = Umbrales(
    cuidado=40,
    cerrado=70,
    histeresis=10,
    bajada_s=30,
    tasa_cuidado=15,
    ventana_tasa_s=20,
    vence_s=10,
)

LIBRE, CUIDADO, CERRADO = Estado.LIBRE, Estado.CUIDADO, Estado.CERRADO


def cam(nivel, t, conf=1.0, **extra):
    """Lectura de cámara fresca en el instante t."""
    return Entradas(nivel_camara=nivel, t_camara=t, confianza_camara=conf, **extra)


def maquina(estado=LIBRE, **kw):
    return MaquinaEstados(Umbrales(**{**U.__dict__, **kw}), estado_inicial=estado, t0=0)


# --- Subida -----------------------------------------------------------------

def test_nivel_bajo_queda_libre():
    d = maquina().evaluar(cam(20, 0), 0)
    assert d.estado == LIBRE
    assert not d.cambio
    assert d.fuente == "camara"
    assert d.nivel == 20


def test_sube_a_cuidado_y_luego_a_cerrado_en_los_umbrales():
    m = maquina()
    assert m.evaluar(cam(39.9, 0), 0).estado == LIBRE
    d = m.evaluar(cam(40, 1), 1)
    assert (d.estado, d.anterior, d.cambio) == (CUIDADO, LIBRE, True)
    d = m.evaluar(cam(70, 2), 2)
    assert (d.estado, d.anterior, d.cambio) == (CERRADO, CUIDADO, True)


def test_salta_directo_de_libre_a_cerrado():
    d = maquina().evaluar(cam(85, 0), 0)
    assert d.estado == CERRADO and d.anterior == LIBRE and d.cambio


# --- Histéresis y bajada ----------------------------------------------------

def test_histeresis_no_baja_dentro_de_la_banda():
    m = maquina()
    m.evaluar(cam(75, 0), 0)
    for t in range(1, 200):
        d = m.evaluar(cam(65, t), t)  # 65 > 70 - 10: sigue en la banda de CERRADO
    assert d.estado == CERRADO


def test_baja_un_escalon_solo_despues_del_tiempo_de_bajada():
    m = maquina()
    m.evaluar(cam(75, 0), 0)
    for t in range(1, 31):
        d = m.evaluar(cam(50, t), t)  # 50 < 60: el objetivo es CUIDADO desde t=1
    assert d.estado == CERRADO  # en t=30 solo lleva 29 s
    d = m.evaluar(cam(50, 31), 31)
    assert (d.estado, d.anterior, d.cambio) == (CUIDADO, CERRADO, True)


def test_baja_de_a_un_escalon_aunque_el_rio_ya_este_bajo():
    m = maquina()
    m.evaluar(cam(75, 0), 0)
    estados = {t: m.evaluar(cam(10, t), t).estado for t in range(1, 70)}
    assert estados[30] == CERRADO
    assert estados[31] == CUIDADO  # primer escalón
    assert estados[60] == CUIDADO
    assert estados[61] == LIBRE  # segundo escalón, otros 30 s después


def test_el_reloj_de_bajada_se_reinicia_si_el_rio_vuelve_a_subir():
    m = maquina()
    m.evaluar(cam(75, 0), 0)
    for t in range(1, 21):
        m.evaluar(cam(50, t), t)
    m.evaluar(cam(72, 21), 21)  # repunte: vuelve a pedir CERRADO
    for t in range(22, 52):
        d = m.evaluar(cam(50, t), t)
    assert d.estado == CERRADO  # en t=51 lleva 29 s desde t=22
    assert m.evaluar(cam(50, 52), 52).estado == CUIDADO


def test_no_aletea_con_ruido_alrededor_del_umbral():
    m = maquina()
    cambios = 0
    for t in range(0, 300):
        nivel = 38 if t % 2 else 42
        cambios += m.evaluar(cam(nivel, t), t).cambio
    assert cambios == 1  # solo LIBRE -> CUIDADO; 38 queda dentro de la banda
    assert m.estado == CUIDADO


def test_desde_marca_el_inicio_del_estado_actual():
    m = maquina()
    m.evaluar(cam(10, 0), 0)
    d = m.evaluar(cam(45, 5), 5)
    assert d.desde == 5
    d = m.evaluar(cam(46, 9), 9)
    assert d.desde == 5 and not d.cambio


# --- Flotador, datos vencidos y fuentes -------------------------------------

def test_flotador_cierra_aunque_la_camara_diga_nivel_bajo():
    d = maquina().evaluar(cam(10, 0, flotador=True, t_flotador=0), 0)
    assert d.estado == CERRADO
    assert any("lotador" in r for r in d.razones)


def test_flotador_vencido_no_cuenta():
    d = maquina().evaluar(cam(10, 30, flotador=True, t_flotador=0), 30)
    assert d.estado == LIBRE


def test_sin_datos_sube_a_cuidado_y_marca_degradado():
    m = maquina()
    m.evaluar(cam(10, 0), 0)
    d = m.evaluar(cam(10, 0), 11)  # la lectura de t=0 ya venció (11 s > 10 s)
    assert d.estado == CUIDADO
    assert d.degradado
    assert d.fuente == "ninguna"


def test_sin_datos_nunca_baja_un_cierre():
    m = maquina()
    m.evaluar(cam(80, 0), 0)
    for t in range(11, 500, 7):
        d = m.evaluar(Entradas(), t)
    assert d.estado == CERRADO and d.degradado


def test_usa_el_sensor_si_la_camara_vencio():
    e = Entradas(nivel_camara=10, t_camara=0, nivel_sensor=50, t_sensor=20)
    d = maquina().evaluar(e, 20)
    assert d.fuente == "sensor"
    assert d.nivel == 50
    assert d.estado == CUIDADO


def test_camara_con_baja_confianza_se_ignora():
    e = Entradas(nivel_camara=10, t_camara=0, confianza_camara=0.1, nivel_sensor=45, t_sensor=0)
    d = maquina().evaluar(e, 0)
    assert d.fuente == "sensor"
    assert d.estado == CUIDADO


def test_si_camara_y_sensor_no_coinciden_manda_el_peor_caso():
    # p. ej. la cámara "no ve" el agua (colorante gastado) y lee 0 %, pero el sensor marca 60 %
    e = Entradas(nivel_camara=10, t_camara=0, nivel_sensor=60, t_sensor=0)
    d = maquina().evaluar(e, 0)
    assert d.discrepancia
    assert (d.nivel, d.fuente, d.estado) == (60, "sensor", CUIDADO)


def test_si_coinciden_manda_la_camara():
    d = maquina().evaluar(Entradas(nivel_camara=50, t_camara=0, nivel_sensor=45, t_sensor=0), 0)
    assert not d.discrepancia
    assert (d.nivel, d.fuente) == (50, "camara")


def test_politica_maximo_usa_siempre_el_mayor():
    d = maquina(politica="maximo").evaluar(Entradas(nivel_camara=45, t_camara=0, nivel_sensor=50, t_sensor=0), 0)
    assert (d.nivel, d.fuente) == (50, "sensor")


# --- Tasa de subida ---------------------------------------------------------

def test_subida_rapida_activa_cuidado_antes_del_umbral():
    m = maquina()
    for t, n in [(0, 10), (5, 15), (10, 20), (15, 26)]:
        d = m.evaluar(cam(n, t), t)
    assert d.nivel < 40
    assert d.tasa is not None and d.tasa >= 15
    assert d.estado == CUIDADO
    assert any("ubida" in r for r in d.razones)


def test_subida_lenta_no_activa_nada():
    m = maquina()
    for t, n in [(0, 10), (10, 11), (20, 12)]:
        d = m.evaluar(cam(n, t), t)
    assert d.estado == LIBRE


def test_cambio_de_fuente_no_se_confunde_con_subida_rapida():
    m = maquina()
    for t in range(0, 10):
        m.evaluar(Entradas(nivel_camara=5, t_camara=t, nivel_sensor=30, t_sensor=t), t)
    # la cámara se cae y entra el sensor (30 %): no es una crecida
    for t in range(10, 25):
        d = m.evaluar(Entradas(nivel_camara=5, t_camara=9, nivel_sensor=30, t_sensor=t), t)
    assert d.fuente == "sensor"
    assert d.estado == LIBRE


# --- Lluvia del IMN y cierre manual ----------------------------------------

def test_lluvia_fuerte_del_imn_pone_cuidado():
    e = cam(10, 0, lluvia_1h=40.4, t_lluvia=-600, estacion_lluvia="Aeropuerto Daniel Oduber")
    d = maquina().evaluar(e, 0)
    assert d.estado == CUIDADO
    assert any("40,4" in r for r in d.razones)


def test_lluvia_de_hace_horas_no_cuenta():
    e = cam(10, 0, lluvia_1h=40.4, t_lluvia=-4 * 3600)
    assert maquina().evaluar(e, 0).estado == LIBRE


def test_lluvia_acumulada_en_3_horas_pone_cuidado():
    e = cam(10, 0, lluvia_1h=2, lluvia_3h=30, t_lluvia=0)
    assert maquina().evaluar(e, 0).estado == CUIDADO


def test_cierre_manual_sube_el_estado():
    d = maquina().evaluar(cam(10, 0, minimo_manual=CERRADO), 0)
    assert d.estado == CERRADO
    assert any("manual" in r for r in d.razones)


def test_lo_manual_no_puede_abrir_un_cruce_peligroso():
    d = maquina().evaluar(cam(80, 0, minimo_manual=LIBRE), 0)
    assert d.estado == CERRADO
