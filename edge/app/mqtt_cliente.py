"""Cliente MQTT del borde (paho-mqtt 2.x) contra el Mosquitto local.

Temas:
  <base>/<dispositivo>/sensor   ESP32 o simulador -> borde (mismo JSON que POST /api/sensor)
  <base>/<cruce>/estado         borde -> equipos, retenido: estado, color, nivel, zumbador
  <base>/<cruce>/alerta         borde -> equipos: cada evento
"""

from __future__ import annotations

import json
import logging
from typing import Callable

import paho.mqtt.client as mqtt

log = logging.getLogger("paso_seguro.mqtt")


def leer_mensaje_sensor(topico: str, payload: bytes, base: str) -> dict | None:
    partes = topico.split("/")
    if len(partes) != 3 or partes[0] != base or partes[2] != "sensor" or not partes[1]:
        return None
    try:
        datos = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(datos, dict):
        return None
    return {"id": partes[1], **{k: v for k, v in datos.items() if k != "id"}}


class ClienteMqtt:
    def __init__(
        self,
        host: str,
        puerto: int,
        base: str,
        al_sensor: Callable[[dict], None],
        usuario: str = "",
        clave: str = "",
        id_cliente: str = "paso-seguro-borde",
    ):
        self.host, self.puerto, self.base = host, puerto, base
        self.al_sensor = al_sensor
        self.conectado = False
        self._c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=id_cliente)
        if usuario:
            self._c.username_pw_set(usuario, clave or None)
        self._c.on_connect = self._al_conectar
        self._c.on_disconnect = self._al_desconectar
        self._c.on_message = self._al_mensaje
        self._c.reconnect_delay_set(1, 10)

    def iniciar(self) -> None:
        try:
            self._c.connect_async(self.host, self.puerto, keepalive=30)
        except Exception as e:  # nombre que no resuelve, etc.: paho reintenta solo
            log.warning("MQTT: no se pudo iniciar la conexión a %s:%s (%s)", self.host, self.puerto, e)
        self._c.loop_start()

    def detener(self) -> None:
        try:
            self._c.disconnect()
        except Exception:
            pass
        self._c.loop_stop()

    def publicar(self, subtema: str, datos: dict, retener: bool = False) -> bool:
        if not self.conectado:
            return False
        self._c.publish(f"{self.base}/{subtema}", json.dumps(datos, ensure_ascii=False), qos=0, retain=retener)
        return True

    def _al_conectar(self, cliente, _userdata, _flags, reason_code, _props) -> None:
        self.conectado = not reason_code.is_failure
        if self.conectado:
            cliente.subscribe(f"{self.base}/+/sensor", qos=0)
            log.info("MQTT conectado a %s:%s", self.host, self.puerto)
        else:
            log.warning("MQTT rechazó la conexión: %s", reason_code)

    def _al_desconectar(self, _cliente, _userdata, _flags, reason_code, _props) -> None:
        self.conectado = False
        log.warning("MQTT desconectado (%s)", reason_code)

    def _al_mensaje(self, _cliente, _userdata, msg) -> None:
        datos = leer_mensaje_sensor(msg.topic, msg.payload, self.base)
        if datos:
            self.al_sensor(datos)
