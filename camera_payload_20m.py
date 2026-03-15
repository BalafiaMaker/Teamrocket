#!/usr/bin/env python3

import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from datetime import datetime


# --------------------------------
# CONFIG
# --------------------------------

ALT_FILE = "/home/pi/cansat/altitude.txt"
WATER_FILE = "/home/pi/cansat/water_status.txt"
PHOTO_DIR = "/home/pi/cansat/photos"

ALTITUDE_STEP = 20

os.makedirs(PHOTO_DIR, exist_ok=True)


# --------------------------------
# CAMARA
# --------------------------------

picam2 = Picamera2()

config = picam2.create_still_configuration(
    main={"size": (1280,720)}
)

picam2.configure(config)

picam2.start()

time.sleep(2)

print("Camera payload iniciado")


# --------------------------------
# FUNCIONES
# --------------------------------

def read_altitude():

    try:

        with open(ALT_FILE,"r") as f:

            return float(f.read().strip())

    except:

        return None


def detect_water(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return 0

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([90,50,50])
    upper_blue = np.array([140,255,255])

    mask = cv2.inRange(hsv,lower_blue,upper_blue)

    water_pixels = np.sum(mask > 0)
    total_pixels = mask.size

    ratio = water_pixels / total_pixels

    if ratio > 0.15:
        return 1
    else:
        return 0


def write_water(value):

    try:

        with open(WATER_FILE,"w") as f:

            f.write(str(value))

    except:

        pass


# --------------------------------
# LOOP
# --------------------------------

last_capture_alt = None
photo_counter = 0

while True:

    alt = read_altitude()

    if alt is None:

        time.sleep(1)
        continue


    if last_capture_alt is None:

        last_capture_alt = alt


    diff = abs(alt - last_capture_alt)

    if diff >= ALTITUDE_STEP:

        photo_counter += 1

        timestamp = datetime.now().strftime("%H%M%S")

        filename = f"{PHOTO_DIR}/img_{photo_counter}_{timestamp}.jpg"

        picam2.capture_file(filename)

        print("Foto capturada:", filename, "alt:", alt)

        water = detect_water(filename)

        print("Agua:", water)

        write_water(water)

        last_capture_alt = alt


    time.sleep(1)
