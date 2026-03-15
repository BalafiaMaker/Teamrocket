#!/usr/bin/env python3

import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from datetime import datetime


# --------------------------------
# CONFIGURACIÓN
# --------------------------------

PHOTO_DIR = "/home/pi/cansat/photos"
WATER_FILE = "/home/pi/cansat/water_status.txt"

CAPTURE_INTERVAL = 5   # segundos

os.makedirs(PHOTO_DIR, exist_ok=True)


# --------------------------------
# INICIALIZAR CAMARA
# --------------------------------

picam2 = Picamera2()

config = picam2.create_still_configuration(
    main={"size": (1280,720)}
)

picam2.configure(config)

picam2.start()

time.sleep(2)

print("Sistema cámara iniciado")


# --------------------------------
# DETECCIÓN DE AGUA
# --------------------------------

def detect_water(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return 0

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # rango azul típico de agua
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    water_pixels = np.sum(mask > 0)
    total_pixels = mask.size

    ratio = water_pixels / total_pixels

    # umbral experimental
    if ratio > 0.15:
        return 1
    else:
        return 0


# --------------------------------
# GUARDAR RESULTADO
# --------------------------------

def write_water_status(value):

    try:

        with open(WATER_FILE, "w") as f:
            f.write(str(value))

    except Exception as e:

        print("Error guardando estado agua:", e)


# --------------------------------
# LOOP PRINCIPAL
# --------------------------------

counter = 0

while True:

    try:

        counter += 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{PHOTO_DIR}/img_{counter}_{timestamp}.jpg"

        picam2.capture_file(filename)

        print("Foto capturada:", filename)

        # análisis de imagen

        water = detect_water(filename)

        print("Agua detectada:", water)

        write_water_status(water)

        time.sleep(CAPTURE_INTERVAL)

    except Exception as e:

        print("Error cámara:", e)

        time.sleep(2)