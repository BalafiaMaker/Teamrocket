#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal CanSat: sensores + OLED (SH1106 SPI)
Versión corregida:
- Inicializa SensorManager antes de leer
- Usa la misma configuración OLED que el test_oled.py que sí funciona
- Muestra datos básicos en pantalla
- Deja preparado un punto para enviar telemetría por LoRa
"""

import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from PIL import ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from luma.core.render import canvas

from cansat_sensors import create_default_sensor_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cansat_main")


class OLEDManager:
    """Gestor simple para la OLED SH1106 por SPI."""

    def __init__(self, port: int = 0, device: int = 0, gpio_dc: int = 13, gpio_rst: int = 6):
        self.port = port
        self.device = device
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self.oled = None
        self.font = ImageFont.load_default()
        self.initialized = False

    def init(self) -> bool:
        try:
            serial = spi(device=self.device, port=self.port, gpio_DC=self.gpio_dc, gpio_RST=self.gpio_rst)
            self.oled = sh1106(serial)
            self.initialized = True
            self.show_lines(["OLED OK", "CanSat Team Rocket"])
            logger.info("OLED inicializada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error inicializando OLED: {e}")
            self.initialized = False
            return False

    def show_lines(self, lines):
        if not self.initialized or self.oled is None:
            return
        try:
            with canvas(self.oled) as draw:
                y = 0
                for line in lines[:6]:
                    draw.text((2, y), str(line)[:21], font=self.font, fill=255)
                    y += 10
        except Exception as e:
            logger.error(f"Error escribiendo en OLED: {e}")


class LoRaManager:
    """
    Punto de integración para LoRa.
    Ahora mismo deja el paquete listo y lo saca por log.
    Sustituye send() por tu librería real de LoRa si ya la tienes.
    """

    def __init__(self):
        self.initialized = True

    def send(self, payload: Dict[str, Any]) -> bool:
        try:
            packet = json.dumps(payload, ensure_ascii=False)
            logger.info(f"Telemetría preparada para LoRa: {packet}")
            return True
        except Exception as e:
            logger.error(f"Error preparando paquete LoRa: {e}")
            return False



def format_for_display(data: Dict[str, Any]):
    """Convierte los datos en líneas cortas para la OLED."""
    lines = []
    lines.append(datetime.now().strftime("%H:%M:%S"))

    if "temperature" in data:
        lines.append(f"T:{data['temperature']:.1f}C H:{data.get('humidity', 0):.0f}%")
    else:
        lines.append("T: -- H: --")

    if "pressure" in data:
        lines.append(f"P:{data['pressure']:.1f}hPa")
    else:
        lines.append("P: --")

    if "altitude_barometric" in data:
        lines.append(f"AltB:{data['altitude_barometric']:.1f}m")
    elif "gps_altitude" in data:
        lines.append(f"AltG:{data['gps_altitude']:.1f}m")
    else:
        lines.append("Alt: --")

    sats = data.get("satellites", 0)
    fix = "OK" if data.get("fix_valid", False) else "NO"
    lines.append(f"GPS:{fix} SAT:{sats}")

    if "bno_euler_pitch" in data and "bno_euler_roll" in data:
        lines.append(f"R:{data['bno_euler_roll']:.1f} P:{data['bno_euler_pitch']:.1f}")
    else:
        lines.append("IMU: --")

    return lines



def main():
    logger.info("Iniciando sistema CanSat...")

    # 1) OLED
    oled = OLEDManager(port=0, device=0, gpio_dc=13, gpio_rst=6)
    oled_ok = oled.init()

    if oled_ok:
        oled.show_lines([
            "Iniciando...",
            "Sensores"
        ])

    # 2) Sensores
    sensor_manager = create_default_sensor_manager()
    sensors_ok = sensor_manager.init_all()

    if not sensors_ok:
        logger.error("No se pudo inicializar ningún sensor")
        if oled_ok:
            oled.show_lines([
                "ERROR SENSORES",
                "Revisa I2C",
                "y alimentacion"
            ])
        return

    logger.info(f"Sensores activos: {sensor_manager.get_sensor_names()}")

    # 3) LoRa
    lora = LoRaManager()

    if oled_ok:
        oled.show_lines([
            "Sistema OK",
            "Leyendo datos..."
        ])
        time.sleep(1)

    # 4) Bucle principal
    while True:
        data = sensor_manager.read_all()

        # Añadir metadatos útiles
        data["team"] = "Team Rocket"
        data["frame_type"] = "telemetry"

        logger.info(data)

        # OLED
        if oled_ok:
            oled.show_lines(format_for_display(data))

        # LoRa
        lora.send(data)

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Programa detenido por el usuario")
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
