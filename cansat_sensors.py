#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LIBRERÍA ROBUSTA DE SENSORES PARA CANSAT
Versión con recuperación automática I2C
"""

import time
import struct
import logging
import json
import csv
import os

from datetime import datetime
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cansat_sensors")


# --------------------------------------------------
# CLASE BASE
# --------------------------------------------------

class SensorBase(ABC):

    def __init__(self, name):

        self.name = name
        self._data = {}

        self.error_count = 0
        self.max_errors = 5


    @abstractmethod
    def init(self):
        pass


    @abstractmethod
    def read(self):
        pass


    def get_data(self):
        return self._data.copy()


    def handle_error(self):

        self.error_count += 1

        logger.warning(f"{self.name} error {self.error_count}")

        if self.error_count >= self.max_errors:

            logger.warning(f"Reinicializando {self.name}")

            try:
                self.init()
                self.error_count = 0
            except Exception as e:
                logger.error(f"Fallo reinicio {self.name}: {e}")


# --------------------------------------------------
# BME280
# --------------------------------------------------

class BME280Sensor(SensorBase):

    def __init__(self, i2c, address=0x77, sea_level_pressure=1013.25):

        super().__init__("bme280")

        self.i2c = i2c
        self.address = address
        self.sensor = None
        self.sea_level_pressure = sea_level_pressure


    def init(self):

        try:

            from adafruit_bme280 import basic as adafruit_bme280

            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(
                self.i2c,
                address=self.address
            )

            self.sensor.sea_level_pressure = self.sea_level_pressure

            return True

        except Exception as e:

            logger.error(e)
            return False


    def read(self):

        try:

            t = self.sensor.temperature
            p = self.sensor.pressure
            h = self.sensor.humidity

            alt = 44330 * (1 - (p / self.sea_level_pressure) ** (1 / 5.255))

            self._data = {

                "temperature_C": round(t, 2),
                "pressure_hPa": round(p, 2),
                "humidity_pct": round(h, 2),
                "altitude_barometric_m": round(alt, 1)

            }

            return True

        except Exception:
            return False


# --------------------------------------------------
# BNO055
# --------------------------------------------------

class BNO055Sensor(SensorBase):

    def __init__(self, bus_id=1, address=0x28):

        super().__init__("bno055")

        self.bus_id = bus_id
        self.address = address
        self.bus = None


    def init(self):

        try:

            import smbus2

            self.bus = smbus2.SMBus(self.bus_id)

            self.bus.write_byte_data(self.address, 0x3D, 0x00)
            time.sleep(0.1)

            self.bus.write_byte_data(self.address, 0x3F, 0x20)
            time.sleep(1)

            self.bus.write_byte_data(self.address, 0x3D, 0x0C)
            time.sleep(0.1)

            return True

        except Exception as e:

            logger.error(e)
            return False


    def read(self):

        try:

            q = self.bus.read_i2c_block_data(self.address, 0x20, 8)

            qw = struct.unpack('<h', bytes(q[0:2]))[0] / 16384.0
            qx = struct.unpack('<h', bytes(q[2:4]))[0] / 16384.0
            qy = struct.unpack('<h', bytes(q[4:6]))[0] / 16384.0
            qz = struct.unpack('<h', bytes(q[6:8]))[0] / 16384.0

            self._data = {

                "quat_w": round(qw, 4),
                "quat_x": round(qx, 4),
                "quat_y": round(qy, 4),
                "quat_z": round(qz, 4)

            }

            return True

        except Exception:
            return False


# --------------------------------------------------
# GNSS
# --------------------------------------------------

class GNSSSensor(SensorBase):

    def __init__(self):

        super().__init__("gnss")

        self.sensor = None

        self.last_read = 0
        self.read_interval = 2


    def init(self):

        try:

            from GNSSAndRTC import GNSSAndRTC

            self.sensor = GNSSAndRTC(bus=1, addr=0x66)

            if not self.sensor.detectar():
                return False

            return True

        except Exception as e:

            logger.error(e)
            return False


    def read(self):

        try:

            if time.time() - self.last_read < self.read_interval:
                return True

            self.last_read = time.time()

            lat = self.sensor.get_latitud()
            lon = self.sensor.get_longitud()
            alt = self.sensor.get_altitud()

            sat = self.sensor.get_satelites()

            self._data = {

                "gps_fix": sat >= 4,
                "satellites": sat,
                "latitude": lat,
                "longitude": lon,
                "gps_altitude": alt

            }

            return True

        except Exception:
            return False


# --------------------------------------------------
# SENSOR MANAGER
# --------------------------------------------------

class SensorManager:

    def __init__(self):

        self.sensors = {}

        self.i2c = None

        self.mission_start_time = None
        self.mission_start_timestamp = None


    def init_all(self):

        import board
        import busio

        self.i2c = busio.I2C(board.SCL, board.SDA)

        self.mission_start_time = time.time()
        self.mission_start_timestamp = datetime.now().isoformat(timespec="seconds")

        bme = BME280Sensor(self.i2c)
        if bme.init():
            self.sensors["bme280"] = bme

        bno = BNO055Sensor()
        if bno.init():
            self.sensors["bno055"] = bno

        gps = GNSSSensor()
        if gps.init():
            self.sensors["gnss"] = gps

        logger.info(f"Sensores activos {list(self.sensors.keys())}")

        return True


    def reset_i2c(self):

        logger.warning("Reiniciando bus I2C")

        import board
        import busio

        self.i2c = busio.I2C(board.SCL, board.SDA)

        for s in self.sensors.values():

            try:
                s.init()
            except Exception:
                pass


    def read_all(self):

        t = time.time() - self.mission_start_time

        data = {"time_s": round(t, 2)}

        errors = 0

        for s in self.sensors.values():

            try:

                ok = s.read()

                if ok:

                    data.update(s.get_data())
                    s.error_count = 0

                else:

                    errors += 1
                    s.handle_error()

            except Exception:

                errors += 1
                s.handle_error()

            time.sleep(0.02)

        if errors >= 3:
            self.reset_i2c()

        return data


    def save_csv(self, file, data):

        exists = os.path.isfile(file)

        with open(file, "a", newline="") as f:

            writer = csv.DictWriter(f, fieldnames=data.keys())

            if not exists:

                f.write(f"mission_start,{self.mission_start_timestamp}\n\n")

                writer.writeheader()

            writer.writerow(data)


def create_default_sensor_manager():

    return SensorManager()