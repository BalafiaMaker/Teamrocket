import time
import board
import busio
import json

from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15 import ads1x15

# Configuración del I2C para Raspberry Pi
i2c = busio.I2C(board.SCL, board.SDA)

# Crear objeto ADS1115
ads = ADS1115(i2c)
ads.gain = 1  # hasta 4.096 V aprox.

# Canal A0
chan = AnalogIn(ads, ads1x15.Pin.A0)

# Archivo para guardar la calibración
CALIB_FILE = "calibracion_sensor.json"

def calibrar_sensor():
    print("\n" + "=" * 50)
    print("CALIBRACIÓN DEL SENSOR DE HUMEDAD")
    print("=" * 50)

    calibracion = {}

    input("\n1. Pon el sensor en SUELO SECO y presiona ENTER para medir...")
    print("Midiendo...", end="")
    time.sleep(2)

    valores_seco = []
    for _ in range(10):
        valores_seco.append(chan.value)
        print(".", end="")
        time.sleep(0.1)

    valor_seco = sum(valores_seco) / len(valores_seco)
    calibracion["seco"] = valor_seco
    print(f"\n✅ Valor en seco: {valor_seco:.2f} ({chan.voltage:.3f} V)")

    input("\n2. Pon el sensor en AGUA y presiona ENTER para medir...")
    print("Midiendo...", end="")
    time.sleep(2)

    valores_agua = []
    for _ in range(10):
        valores_agua.append(chan.value)
        print(".", end="")
        time.sleep(0.1)

    valor_agua = sum(valores_agua) / len(valores_agua)
    calibracion["agua"] = valor_agua
    print(f"\n✅ Valor en agua: {valor_agua:.2f} ({chan.voltage:.3f} V)")

    calibracion["rango"] = abs(valor_seco - valor_agua)

    with open(CALIB_FILE, "w") as f:
        json.dump(calibracion, f, indent=4)

    print(f"\n📁 Calibración guardada en {CALIB_FILE}")
    print(f"📊 Rango de medición: {calibracion['rango']:.2f}")
    print("\n" + "=" * 50)
    print("CALIBRACIÓN COMPLETADA")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Iniciando calibración del sensor de humedad...")
    print("ADC ADS1115 conectado - Leyendo del canal A0")

    calibrar_sensor()

    print("\n📋 Resumen de calibración:")
    with open(CALIB_FILE, "r") as f:
        calibracion = json.load(f)

    print(f"  Sensor seco: {calibracion['seco']:.2f}")
    print(f"  Sensor en agua: {calibracion['agua']:.2f}")
    print(f"  Rango: {calibracion['rango']:.2f}")