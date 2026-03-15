```python
#!/usr/bin/env python3

import time
import serial
import board
import neopixel
import RPi.GPIO as GPIO
import os

from cansat_sensors import create_default_sensor_manager


# -----------------------------
# ARCHIVOS DE INTERCAMBIO
# -----------------------------

ALT_FILE = "/home/pi/cansat/altitude.txt"
WATER_FILE = "/home/pi/cansat/water_status.txt"


def write_altitude(alt):

    try:
        with open(ALT_FILE,"w") as f:
            f.write(str(alt))
    except:
        pass


def read_water_status():

    try:
        with open(WATER_FILE,"r") as f:
            return int(f.read().strip())
    except:
        return 0


# -----------------------------
# LORA
# -----------------------------

lora = serial.Serial(
    "/dev/serial0",
    baudrate=9600,
    timeout=1
)


# -----------------------------
# NEOPIXEL
# -----------------------------

PIXEL_PIN = board.D18

pixels = neopixel.NeoPixel(
    PIXEL_PIN,
    1,
    brightness=0.3,
    auto_write=False
)


def led_color(r,g,b):

    pixels[0] = (r,g,b)
    pixels.show()


def led_boot():

    led_color(255,0,0)
    time.sleep(0.3)

    led_color(0,0,0)
    time.sleep(0.3)


def led_tx():

    led_color(0,255,0)
    time.sleep(0.05)

    led_color(0,0,0)


def led_warning():

    led_color(255,120,0)


def led_error():

    led_color(255,0,0)


# -----------------------------
# BUZZER
# -----------------------------

BUZZER_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

buzzer = GPIO.PWM(BUZZER_PIN,440)


def tone(freq,duration):

    buzzer.ChangeFrequency(freq)
    buzzer.start(70)

    time.sleep(duration)

    buzzer.stop()

    time.sleep(0.02)


# notas

A4=440
C5=523
E5=659
F5=698
G5=784


def star_wars():

    melody=[

        (A4,0.5),(A4,0.5),(A4,0.5),
        (F5,0.35),(C5,0.15),

        (A4,0.5),(F5,0.35),(C5,0.15),(A4,0.9),

        (E5,0.5),(E5,0.5),(E5,0.5),
        (F5,0.35),(C5,0.15),

        (G5,0.5),(F5,0.35),(C5,0.15),(A4,0.9)

    ]

    for note,d in melody:

        tone(note,d)


def search_beacon():

    while True:

        star_wars()
        time.sleep(20)


# -----------------------------
# MAIN
# -----------------------------

def main():

    # animación arranque

    for i in range(6):
        led_boot()

    sensors = create_default_sensor_manager()
    sensors.init_all()

    # comprobación sensores inicial

    data = sensors.read_all()

    if data.get("temperature_C") != None:
        led_color(0,0,255)
        time.sleep(0.5)

    if data.get("quat_x") != None:
        led_color(180,0,255)
        time.sleep(0.5)

    if data.get("gps_fix") != None:
        led_color(255,255,0)
        time.sleep(0.5)

    led_color(0,255,0)
    time.sleep(1)


    packet = 0
    landing_counter = 0
    landed = False
    search_mode = False


    while True:

        # leer sensores
        data = sensors.read_all()

        # obtener altitud barométrica
        alt = data.get("altitude_barometric_m",0)

        # guardar altitud para el payload de cámara
        write_altitude(alt)

        # leer resultado del análisis de imagen
        water = read_water_status()

        # añadir campos nuevos
        data["water_detected"] = water
        data["packet"] = packet


        # guardar CSV
        sensors.save_csv("cansat_data.csv",data)


        # comprobar sensores

        sensor_error = False

        for v in data.values():

            if v is None:
                sensor_error = True

        if sensor_error:
            led_warning()


        # -------------------------
        # TELEMETRIA LORA
        # -------------------------

        line = ",".join(str(v) for v in data.values())

        lora.write((line+"\n").encode())

        led_tx()


        # -------------------------
        # DETECCION ATERRIZAJE
        # -------------------------

        vel = data.get("gps_altitude",0)

        if vel < 2:
            landing_counter += 1
        else:
            landing_counter = 0


        if landing_counter > 10 and not landed:

            star_wars()

            landed = True
            search_mode = True


        if search_mode:

            search_beacon()


        packet += 1

        time.sleep(1)


if __name__ == "__main__":

    try:

        main()

    except:

        led_error()
        GPIO.cleanup()
```
