#!/usr/bin/env python3

import time
import serial
import board
import neopixel
import RPi.GPIO as GPIO

from cansat_sensors import create_default_sensor_manager


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

    # arranque

    for i in range(6):
        led_boot()


    sensors = create_default_sensor_manager()
    sensors.init_all()

    # test sensores

    data = sensors.read_all()

    if data.get("temperature_C") != None:
        led_color(0,0,255)
        time.sleep(0.5)

    if data.get("accel_x") != None:
        led_color(180,0,255)
        time.sleep(0.5)

    if data.get("gps_fix") != None:
        led_color(255,255,0)
        time.sleep(0.5)

    if data.get("soil_raw") != None:
        led_color(0,255,255)
        time.sleep(0.5)

    led_color(0,255,0)
    time.sleep(1)


    packet = 0
    landing_counter = 0
    landed = False
    search_mode = False


    while True:

        data = sensors.read_all()

        sensors.save_csv("cansat_data.csv",data)


        # comprobar sensores

        sensor_error = False

        for v in data.values():

            if v is None:
                sensor_error = True

        if sensor_error:
            led_warning()


        # enviar telemetría

        line = str(packet) + "," + ",".join(str(v) for v in data.values())

        lora.write((line+"\n").encode())

        led_tx()


        # detección aterrizaje

        vel = data.get("gps_speed_mps",0)

        if vel < 0.5:
            landing_counter += 1
        else:
            landing_counter = 0


        if landing_counter > 5 and not landed:

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