#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LIBRERÍA FINAL DE SENSORES PARA CANSAT
"""

import time
import math
import json
import csv
import os
import struct
import logging

from datetime import datetime
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# CLASE BASE
# --------------------------------------------------

class SensorBase(ABC):

    def __init__(self, name):
        self.name = name
        self._data = {}

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def read(self):
        pass

    def get_data(self):
        return self._data.copy()


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

            # modo config
            self.bus.write_byte_data(self.address, 0x3D, 0x00)
            time.sleep(0.1)

            # reset
            self.bus.write_byte_data(self.address, 0x3F, 0x20)
            time.sleep(1)

            # modo NDOF
            self.bus.write_byte_data(self.address, 0x3D, 0x0C)
            time.sleep(0.1)

            return True

        except Exception as e:

            logger.error(e)
            return False

    def read(self):

        try:

            # cuaterniones
            q = self.bus.read_i2c_block_data(self.address, 0x20, 8)

            qw = struct.unpack('<h', bytes(q[0:2]))[0] / 16384.0
            qx = struct.unpack('<h', bytes(q[2:4]))[0] / 16384.0
            qy = struct.unpack('<h', bytes(q[4:6]))[0] / 16384.0
            qz = struct.unpack('<h', bytes(q[6:8]))[0] / 16384.0

            # aceleración
            a = self.bus.read_i2c_block_data(self.address, 0x08, 6)

            ax = struct.unpack('<h', bytes(a[0:2]))[0] / 100.0
            ay = struct.unpack('<h', bytes(a[2:4]))[0] / 100.0
            az = struct.unpack('<h', bytes(a[4:6]))[0] / 100.0

            self._data = {

                "quat_w": round(qw, 4),
                "quat_x": round(qx, 4),
                "quat_y": round(qy, 4),
                "quat_z": round(qz, 4),

                "accel_x": round(ax, 3),
                "accel_y": round(ay, 3),
                "accel_z": round(az, 3)

            }

            return True

        except Exception as e:

            logger.error(e)
            return False


# --------------------------------------------------
# GNSS
# --------------------------------------------------

class GNSSSensor(SensorBase):

    def __init__(self):

        super().__init__("gnss")

        self.sensor = None

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

            lat = self.sensor.get_latitud()
            lon = self.sensor.get_longitud()
            alt = self.sensor.get_altitud()

            sat = self.sensor.get_satelites()

            speed = 0
            course = 0

            if hasattr(self.sensor, "get_velocidad"):
                speed = self.sensor.get_velocidad()

            if hasattr(self.sensor, "get_rumbo"):
                course = self.sensor.get_rumbo()

            gps_fix = sat >= 4

            self._data = {

                "gps_fix": gps_fix,
                "satellites": sat,

                "latitude": lat,
                "longitude": lon,
                "gps_altitude": alt,

                "gps_speed_mps": speed,
                "gps_speed_kmh": speed * 3.6,

                "gps_course": course
            }

            return True

        except Exception as e:

            logger.error(f"GNSS read error {e}")
            return False


# --------------------------------------------------
# SENSOR HUMEDAD SUELO
# --------------------------------------------------

class WaterSoilSensor(SensorBase):

    def __init__(self, i2c, calib_file="calibracion_sensor.json"):

        super().__init__("soil")

        self.i2c = i2c
        self.calib_file = calib_file
        self.sensor = None

        self.valor_seco = 20000
        self.valor_agua = 10000

    def init(self):

        try:

            from adafruit_ads1x15.ads1115 import ADS1115
            from adafruit_ads1x15.analog_in import AnalogIn
            from adafruit_ads1x15 import ads1x15

            ads = ADS1115(self.i2c)
            ads.gain = 1

            self.sensor = AnalogIn(ads, ads1x15.Pin.A0)

            self._load_calibration()

            return True

        except Exception as e:

            logger.error(e)
            return False

    def _load_calibration(self):

        try:

            with open(self.calib_file) as f:

                calib = json.load(f)

                self.valor_seco = calib["seco"]
                self.valor_agua = calib["agua"]

        except Exception:

            logger.warning("calibracion_sensor.json no encontrado")

    def _read_stable(self):

        values = []

        for _ in range(5):

            values.append(self.sensor.value)
            time.sleep(0.05)

        values.sort()

        values = values[1:4]

        return sum(values) / len(values)

    def _humidity(self, v):

        if self.valor_agua < self.valor_seco:

            if v >= self.valor_seco: return 0
            if v <= self.valor_agua: return 100

            return ((self.valor_seco - v) / (self.valor_seco - self.valor_agua)) * 100

        else:

            if v <= self.valor_seco: return 0
            if v >= self.valor_agua: return 100

            return ((v - self.valor_seco) / (self.valor_agua - self.valor_seco)) * 100

    def _state(self, h):

        if h >= 80: return "A"
        if h >= 30: return "P"
        return "N"

    def read(self):

        try:

            raw = self._read_stable()

            hum = self._humidity(raw)

            state = self._state(hum)

            self._data = {

                "soil_raw": round(raw, 1),
                "soil_humidity_pct": round(hum, 1),
                "soil_state": state

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
        if bme.init(): self.sensors["bme280"] = bme

        bno = BNO055Sensor()
        if bno.init(): self.sensors["bno055"] = bno

        gps = GNSSSensor()
        if gps.init(): self.sensors["gnss"] = gps

        soil = WaterSoilSensor(self.i2c)
        if soil.init(): self.sensors["soil"] = soil

        logger.info(f"Sensores activos {list(self.sensors.keys())}")

        return True

    def read_all(self):

        t = time.time() - self.mission_start_time

        data = {"time_s": round(t, 2)}

        for s in self.sensors.values():

            if s.read():

                data.update(s.get_data())

        return data

    def save_csv(self, file, data):

        exists = os.path.isfile(file)

        with open(file, "a", newline="") as f:

            writer = csv.DictWriter(f, fieldnames=data.keys())

            if not exists:

                f.write(f"mission_start,{self.mission_start_timestamp}\n\n")

                writer.writeheader()

            writer.writerow(data)

    def shutdown(self):

        self.sensors.clear()


def create_default_sensor_manager():

    return SensorManager()
