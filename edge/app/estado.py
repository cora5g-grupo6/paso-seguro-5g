"""Máquina de estados del cruce: LIBRE / CUIDADO / CERRADO.

Reglas, en este orden:
1. Nivel efectivo: la cámara si está fresca y con confianza; si no, el sensor del ESP32.
2. Umbrales con histéresis: se sube apenas se cruza el umbral. Para bajar, el objetivo
   tiene que quedar por debajo del estado durante `bajada_s` segundos, y se baja de a
   un escalón (CERRADO -> CUIDADO -> LIBRE).
3. El flotador activado manda CERRADO (respaldo físico).
4. Subida rápida (%/min) o lluvia fuerte del IMN suben al menos a CUIDADO.
5. Sin datos de nivel: nunca baja y queda al menos en CUIDADO (modo degradado).
6. Una persona puede subir el estado (cierre manual), pero nunca bajarlo.

Todo es determinista: el tiempo `t` (segundos) entra como parámetro, así se prueba sin reloj.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from enum import StrEnum


class Estado(StrEnum):
    LIBRE = "LIBRE"
    CUIDADO = "CUIDADO"
    CERRADO = "CERRADO"

    @property
    def orden(self) -> int:
        return _ORDEN[self]


_ORDEN = {Estado.LIBRE: 0, Estado.CUIDADO: 1, Estado.CERRADO: 2}
_POR_ORDEN = {v: k for k, v in _ORDEN.items()}
_FUENTE_TXT = {"camara": "cámara", "sensor": "sensor del ESP32", "ninguna": "sin datos"}


def mayor(a: Estado, b: Estado) -> Estado:
    return a if a.orden >= b.orden else b


def num(x: float, dec: int = 1) -> str:
    """40.4 -> '40,4' · 30.0 -> '30' (formato para textos en español)."""
    s = f"{x:.{dec}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


@dataclass(frozen=True)
class Umbrales:
    cuidado: float = 40.0  # % de la regla
    cerrado: float = 70.0
    histeresis: float = 10.0  # puntos que debe bajar el nivel bajo el umbral para salir
    bajada_s: float = 30.0  # tiempo sostenido para bajar un escalón (real: 900 s o más)
    tasa_cuidado: float = 15.0  # %/min de subida que ya es CUIDADO
    ventana_tasa_s: float = 20.0
    tasa_min_puntos: int = 3
    tasa_min_lapso_s: float = 5.0
    vence_s: float = 10.0  # edad máxima de una lectura de nivel o del flotador
    confianza_min: float = 0.5  # por debajo, la lectura de cámara no se usa
    discrepancia_max: float = 30.0  # puntos de diferencia cámara/sensor que se marcan
    lluvia_1h: float = 10.0  # mm en 1 h -> CUIDADO
    lluvia_3h: float = 25.0  # mm en 3 h -> CUIDADO
    lluvia_vence_s: float = 3 * 3600  # el IMN reporta cada hora
    politica: str = "camara_primero"  # o "maximo": usa el mayor de cámara y sensor


@dataclass
class Entradas:
    """Últimos valores conocidos de cada fuente, con la hora (s) en que llegaron."""

    nivel_camara: float | None = None
    t_camara: float | None = None
    confianza_camara: float = 1.0
    nivel_sensor: float | None = None
    t_sensor: float | None = None
    flotador: bool | None = None
    t_flotador: float | None = None
    lluvia_1h: float | None = None
    lluvia_3h: float | None = None
    t_lluvia: float | None = None
    estacion_lluvia: str | None = None
    minimo_manual: Estado | None = None


@dataclass
class Decision:
    estado: Estado
    anterior: Estado
    cambio: bool
    objetivo: Estado
    nivel: float | None
    fuente: str
    tasa: float | None  # %/min
    razones: list[str] = field(default_factory=list)
    degradado: bool = False
    discrepancia: bool = False
    desde: float = 0.0
    t: float = 0.0
    bajada_en_s: float | None = None  # si está por bajar, cuánto falta

    def a_dict(self) -> dict:
        d = asdict(self)
        for k in ("estado", "anterior", "objetivo"):
            d[k] = str(d[k])
        return d


class MaquinaEstados:
    def __init__(
        self,
        umbrales: Umbrales | None = None,
        estado_inicial: Estado = Estado.LIBRE,
        t0: float = 0.0,
    ):
        self.u = umbrales or Umbrales()
        self.estado = estado_inicial
        self.desde = t0
        self._t_bajada: float | None = None
        self._historial: deque[tuple[float, float]] = deque()
        self._fuente_hist: str | None = None

    # -- utilidades ---------------------------------------------------------

    def _fresco(self, t_dato: float | None, t: float, vence: float | None = None) -> bool:
        return t_dato is not None and (t - t_dato) <= (self.u.vence_s if vence is None else vence)

    def _pendiente(self) -> float | None:
        """Pendiente por mínimos cuadrados en %/min, o None si hay pocos datos."""
        pts = list(self._historial)
        if len(pts) < self.u.tasa_min_puntos:
            return None
        if pts[-1][0] - pts[0][0] < self.u.tasa_min_lapso_s:
            return None
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        if sxx == 0:
            return None
        sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
        return sxy / sxx * 60.0

    def _por_nivel(self, n: float) -> Estado:
        u, s = self.u, self.estado
        if n >= u.cerrado:
            return Estado.CERRADO
        if s == Estado.CERRADO and n >= u.cerrado - u.histeresis:
            return Estado.CERRADO
        if n >= u.cuidado:
            return Estado.CUIDADO
        if s.orden >= 1 and n >= u.cuidado - u.histeresis:
            return Estado.CUIDADO
        return Estado.LIBRE

    # -- evaluación ----------------------------------------------------------

    def evaluar(self, e: Entradas, t: float) -> Decision:
        u = self.u
        razones: list[str] = []

        # 1. Nivel efectivo
        cam_ok = e.nivel_camara is not None and self._fresco(e.t_camara, t)
        if cam_ok and e.confianza_camara < u.confianza_min:
            cam_ok = False
            razones.append(
                f"Cámara sin confianza ({num(e.confianza_camara * 100, 0)} %): ¿tapada o movida?"
            )
        sen_ok = e.nivel_sensor is not None and self._fresco(e.t_sensor, t)
        discrepancia = bool(
            cam_ok and sen_ok and abs(e.nivel_camara - e.nivel_sensor) > u.discrepancia_max
        )
        if cam_ok and sen_ok and (u.politica == "maximo" or discrepancia):
            # ante la duda, el peor caso: si no coinciden, manda la lectura más alta
            if e.nivel_camara >= e.nivel_sensor:
                nivel, fuente = e.nivel_camara, "camara"
            else:
                nivel, fuente = e.nivel_sensor, "sensor"
        elif cam_ok:
            nivel, fuente = e.nivel_camara, "camara"
        elif sen_ok:
            nivel, fuente = e.nivel_sensor, "sensor"
        else:
            nivel, fuente = None, "ninguna"
        if discrepancia:
            razones.append(
                f"Cámara ({num(e.nivel_camara, 0)} %) y sensor ({num(e.nivel_sensor, 0)} %) no coinciden: se usa el mayor"
            )

        # 2. Tasa de subida (el historial se reinicia si cambia la fuente)
        if fuente != self._fuente_hist:
            self._historial.clear()
            self._fuente_hist = fuente
        tasa = None
        if nivel is not None:
            self._historial.append((t, nivel))
            while self._historial and t - self._historial[0][0] > u.ventana_tasa_s:
                self._historial.popleft()
            tasa = self._pendiente()

        # 3. Objetivo
        if nivel is None:
            objetivo = mayor(self.estado, Estado.CUIDADO)
            razones.append("Sin datos de nivel: no se reabre hasta que vuelvan")
        else:
            objetivo = self._por_nivel(nivel)
            ftxt = _FUENTE_TXT[fuente]
            if objetivo == Estado.CERRADO:
                if nivel >= u.cerrado:
                    razones.append(f"Nivel {num(nivel, 0)} % ({ftxt}): sobre el umbral de cierre ({num(u.cerrado, 0)} %)")
                else:
                    razones.append(f"Nivel {num(nivel, 0)} % ({ftxt}): aún no baja de {num(u.cerrado - u.histeresis, 0)} %")
            elif objetivo == Estado.CUIDADO:
                if nivel >= u.cuidado:
                    razones.append(f"Nivel {num(nivel, 0)} % ({ftxt}): sobre el umbral de cuidado ({num(u.cuidado, 0)} %)")
                else:
                    razones.append(f"Nivel {num(nivel, 0)} % ({ftxt}): aún no baja de {num(u.cuidado - u.histeresis, 0)} %")
            else:
                razones.append(f"Nivel {num(nivel, 0)} % ({ftxt}): normal")

        if tasa is not None and tasa >= u.tasa_cuidado:
            objetivo = mayor(objetivo, Estado.CUIDADO)
            razones.append(f"Subida rápida: {num(tasa)} %/min")

        if e.flotador and self._fresco(e.t_flotador, t):
            objetivo = Estado.CERRADO
            razones.append("Flotador activado: el agua llegó a la marca de cierre")

        if self._fresco(e.t_lluvia, t, u.lluvia_vence_s):
            donde = f" en {e.estacion_lluvia}" if e.estacion_lluvia else ""
            if e.lluvia_1h is not None and e.lluvia_1h >= u.lluvia_1h:
                objetivo = mayor(objetivo, Estado.CUIDADO)
                razones.append(f"Lluvia fuerte (IMN{donde}): {num(e.lluvia_1h)} mm en 1 h")
            elif e.lluvia_3h is not None and e.lluvia_3h >= u.lluvia_3h:
                objetivo = mayor(objetivo, Estado.CUIDADO)
                razones.append(f"Lluvia acumulada (IMN{donde}): {num(e.lluvia_3h)} mm en 3 h")

        if e.minimo_manual is not None and e.minimo_manual.orden > 0:
            objetivo = mayor(objetivo, e.minimo_manual)
            razones.append(
                "Cierre manual del operador"
                if e.minimo_manual == Estado.CERRADO
                else "Precaución manual del operador"
            )

        # 4. Transición: sube ya; baja de a un escalón tras `bajada_s` sostenidos
        anterior = self.estado
        bajada_en = None
        if objetivo.orden > anterior.orden:
            nuevo = objetivo
            self._t_bajada = None
        elif objetivo.orden < anterior.orden:
            if self._t_bajada is None:
                self._t_bajada = t
            transcurrido = t - self._t_bajada
            if transcurrido >= u.bajada_s:
                nuevo = _POR_ORDEN[anterior.orden - 1]
                self._t_bajada = t if nuevo.orden > objetivo.orden else None
            else:
                nuevo = anterior
                bajada_en = u.bajada_s - transcurrido
                razones.append(
                    f"Pasa a {_POR_ORDEN[anterior.orden - 1]} si sigue así {num(bajada_en, 0)} s más"
                )
        else:
            nuevo = anterior
            self._t_bajada = None

        if nuevo != anterior:
            self.estado = nuevo
            self.desde = t

        return Decision(
            estado=nuevo,
            anterior=anterior,
            cambio=nuevo != anterior,
            objetivo=objetivo,
            nivel=nivel,
            fuente=fuente,
            tasa=tasa,
            razones=razones,
            degradado=nivel is None,
            discrepancia=discrepancia,
            desde=self.desde,
            t=t,
            bajada_en_s=bajada_en,
        )
