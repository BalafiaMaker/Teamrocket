#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PROGRAMA PRINCIPAL CANSAT
Raspberry Pi Zero
OLED SH1106
"""

import time
from datetime import datetime

from cansat_sensors import create_default_sensor_manager

# OLED
from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont


# --------------------------------------------------
# CONFIGURACIÓN OLED
# --------------------------------------------------

serial = spi(device=0, port=0, gpio_DC=13, gpio_RST=6)
device = sh1106(serial)

font = ImageFont.load_default()

# Offset vertical para evitar recorte superior
OLED_Y_OFFSET = 3


# --------------------------------------------------
# PANTALLA ARRANQUE
# --------------------------------------------------

def boot_screen():

    with canvas(device) as draw:

        draw.text((0,0+OLED_Y_OFFSET),"TEAM ROCKET",font=font,fill=255)
        draw.text((0,15+OLED_Y_OFFSET),"CANSAT INIT",font=font,fill=255)
        draw.text((0,35+OLED_Y_OFFSET),"Starting sensors",font=font,fill=255)


# --------------------------------------------------
# PANTALLA ESTADO SENSORES
# --------------------------------------------------

def sensor_status_screen(sensor_manager):

    y = 0

    with canvas(device) as draw:

        draw.text((0,y+OLED_Y_OFFSET),"SENSORS STATUS",font=font,fill=255)

        y += 15

        for name in sensor_manager.sensors:

            draw.text((0,y+OLED_Y_OFFSET),f"{name}: OK",font=font,fill=255)

            y += 12


# --------------------------------------------------
# PANTALLA TELEMETRÍA
# --------------------------------------------------

def telemetry_screen(packet,data):

    time_mission = data.get("time_s",0)

    gps_fix = data.get("gps_fix",False)

    gps_text = "FIX" if gps_fix else "NO"

    with canvas(device) as draw:

        draw.text((0,0+OLED_Y_OFFSET),"PKT:",font=font,fill=255)
        draw.text((60,0+OLED_Y_OFFSET),str(packet),font=font,fill=255)

        draw.text((0,15+OLED_Y_OFFSET),"LORA:",font=font,fill=255)
        draw.text((60,15+OLED_Y_OFFSET),"TX",font=font,fill=255)

        draw.text((0,30+OLED_Y_OFFSET),"GPS:",font=font,fill=255)
        draw.text((60,30+OLED_Y_OFFSET),gps_text,font=font,fill=255)

        draw.text((0,45+OLED_Y_OFFSET),"TIME:",font=font,fill=255)
        draw.text((60,45+OLED_Y_OFFSET),f"{time_mission:.1f}",font=font,fill=255)


# --------------------------------------------------
# PANTALLA DATOS CIENTÍFICOS
# --------------------------------------------------

def science_screen(data):

    alt = data.get("altitude_barometric_m",0)
    temp = data.get("temperature_C",0)
    speed = data.get("gps_speed_kmh",0)

    with canvas(device) as draw:

        draw.text((0,0+OLED_Y_OFFSET),"ALT:",font=font,fill=255)
        draw.text((60,0+OLED_Y_OFFSET),f"{alt:.1f}",font=font,fill=255)

        draw.text((0,15+OLED_Y_OFFSET),"TEMP:",font=font,fill=255)
        draw.text((60,15+OLED_Y_OFFSET),f"{temp:.1f}",font=font,fill=255)

        draw.text((0,30+OLED_Y_OFFSET),"VEL:",font=font,fill=255)
        draw.text((60,30+OLED_Y_OFFSET),f"{speed:.1f}",font=font,fill=255)

        draw.text((0,45+OLED_Y_OFFSET),"DATA OK",font=font,fill=255)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    # pantalla inicial
    boot_screen()

    time.sleep(2)

    # iniciar sensores
    sensors = create_default_sensor_manager()

    sensors.init_all()

    # mostrar sensores activos
    sensor_status_screen(sensors)

    time.sleep(3)

    csv_file = "cansat_data.csv"

    packet = 0

    screen = 0

    last_screen_change = time.time()

    while True:

        packet += 1

        data = sensors.read_all()

        sensors.save_csv(csv_file,data)

        # cambiar pantalla cada 2 s
        if time.time() - last_screen_change > 2:

            screen = 1 - screen

            last_screen_change = time.time()

        if screen == 0:

            telemetry_screen(packet,data)

        else:

            science_screen(data)

        time.sleep(1)


# --------------------------------------------------

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("Cansat detenido")