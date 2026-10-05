"""Configuración por variables de entorno o archivo .env (ver .env.example).

Sin secretos en el repositorio: claves y URL privadas van solo en .env, que no se versiona.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE = Path(__file__).resolve().parent.parent  # carpeta edge/


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE / ".env", env_file_encoding="utf-8", extra="ignore")

    # General
    cruce_archivo: str = "config/cruce.json"
    calibracion_archivo: str = "config/calibracion.json"
    datos_dir: str = "datos"
    url_publica: str = ""  # p. ej. http://10.0.0.20:8000, para los enlaces de las alertas
    modo_demo: bool = True  # habilita /api/demo/* (inyectar nivel, lluvia o persona)
    tick_s: float = 0.2
    arranque_s: float = 8  # tiempo de espera de datos al arrancar antes de pasar a modo degradado

    # Máquina de estados (ver app/estado.py)
    umbral_cuidado: float = 40
    umbral_cerrado: float = 70
    histeresis: float = 10
    bajada_s: float = 30  # demo; en un río real, 900 s o más
    tasa_cuidado: float = 15  # %/min
    vence_s: float = 10
    lluvia_1h_mm: float = 10
    lluvia_3h_mm: float = 25
    politica_nivel: str = "camara_primero"  # o "maximo"

    # Cámara y visión
    camara_activa: bool = True
    camara_fuentes: str = ""  # lista por orden de preferencia, separada por comas
    camara_lector: str = "auto"  # auto | opencv | pyav (auto: PyAV para RTSP si OpenCV no trae FFmpeg)
    camara_ancho: int = 640
    camara_fps_analisis: float = 5
    camara_mjpeg_fps: float = 8
    vision_mediana: int = 3  # cuadros para el filtro de mediana del nivel
    personas_metodo: str = "hog"  # hog | movimiento | apagado
    personas_cada_n: int = 3
    personas_zona: str = ""  # "x,y,ancho,alto" en píxeles del cuadro analizado; vacío = todo

    # ESP32 por MQTT (además de HTTP)
    mqtt_activo: bool = True
    mqtt_host: str = "localhost"
    mqtt_puerto: int = 1883
    mqtt_base: str = "pasoseguro"
    mqtt_usuario: str = ""
    mqtt_clave: str = ""

    # IMN (necesita internet)
    imn_activo: bool = True
    imn_url: str = "http://wis2box.imn.ac.cr/oapi"
    imn_estacion: str = ""  # vacío = la más cercana al cruce
    imn_intervalo_s: float = 600

    # Alertas
    webhook_urls: str = ""
    n8n_activo: bool = False  # siempre apagado salvo pruebas con un flujo y número de prueba
    n8n_webhook_url: str = ""
    ptt_activo: bool = False

    # Comparación borde vs nube (necesita internet)
    nube_activa: bool = True
    nube_url: str = "https://www.google.com/generate_204"
    nube_intervalo_s: float = 15

    # Feeds
    waze_bloque_h: float = 3
    waze_retencion_min: float = 60

    def ruta(self, p: str) -> Path:
        q = Path(p).expanduser()
        return q if q.is_absolute() else BASE / q

    @staticmethod
    def lista(texto: str) -> list[str]:
        return [x.strip() for x in texto.split(",") if x.strip()]

    @property
    def zona_personas(self) -> tuple[int, int, int, int] | None:
        partes = self.lista(self.personas_zona)
        if len(partes) != 4:
            return None
        return tuple(int(float(x)) for x in partes)  # type: ignore[return-value]
