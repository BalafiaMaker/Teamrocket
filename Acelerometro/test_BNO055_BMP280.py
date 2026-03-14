import time
import board
import busio
import adafruit_bno055
import adafruit_bmp280

# =========================
# CONFIGURACIÓN I2C
# =========================
i2c = busio.I2C(board.SCL, board.SDA)

# Cambia estas direcciones si i2cdetect muestra otras
BNO055_ADDR = 0x28
BMP280_ADDR = 0x76

# Crear objetos de sensor
bno = adafruit_bno055.BNO055_I2C(i2c, address=BNO055_ADDR)
bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=BMP280_ADDR)

# Presión de referencia a nivel del mar para estimar altitud
bmp.sea_level_pressure = 1013.25

def fmt3(v, unit=""):
    """Formatea tuplas de 3 elementos."""
    if v is None:
        return "No disponible"
    if len(v) != 3:
        return str(v)
    a, b, c = v
    return f"X={a:.3f} {unit}, Y={b:.3f} {unit}, Z={c:.3f} {unit}"

def fmt4(v, unit=""):
    """Formatea tuplas de 4 elementos."""
    if v is None:
        return "No disponible"
    if len(v) != 4:
        return str(v)
    a, b, c, d = v
    return f"W={a:.5f} {unit}, X={b:.5f} {unit}, Y={c:.5f} {unit}, Z={d:.5f} {unit}"

def fmt_euler(v):
    """Formatea heading, roll, pitch."""
    if v is None or len(v) != 3:
        return "No disponible"
    heading, roll, pitch = v
    if heading is None or roll is None or pitch is None:
        return "No disponible"
    return f"Heading={heading:.3f} °, Roll={roll:.3f} °, Pitch={pitch:.3f} °"

print("Iniciando test de BNO055 + BMP280...")
print("Pulsa Ctrl+C para detener.\n")

while True:
    try:
        # ========= BNO055 =========
        temperatura_bno = bno.temperature
        aceleracion = bno.acceleration
        aceleracion_lineal = bno.linear_acceleration
        gravedad = bno.gravity
        giroscopio = bno.gyro
        magnetometro = bno.magnetic
        euler = bno.euler
        quaternion = bno.quaternion
        calib = bno.calibration_status  # (sys, gyro, accel, mag)

        # ========= BMP280 =========
        temperatura_bmp = bmp.temperature
        presion = bmp.pressure
        altitud = bmp.altitude

        print("==============================================")
        print("BNO055")
        print(f"Temperatura interna: {temperatura_bno} °C")
        print(f"Aceleración: {fmt3(aceleracion, 'm/s²')}")
        print(f"Aceleración lineal: {fmt3(aceleracion_lineal, 'm/s²')}")
        print(f"Vector gravedad: {fmt3(gravedad, 'm/s²')}")
        print(f"Giroscopio: {fmt3(giroscopio, 'rad/s')}")
        print(f"Magnetómetro: {fmt3(magnetometro, 'uT')}")
        print(f"Orientación Euler: {fmt_euler(euler)}")
        print(f"Quaternion: {fmt4(quaternion)}")
        print(f"Calibración (SYS, GYRO, ACC, MAG): {calib}")

        print("\nBMP280")
        print(f"Temperatura: {temperatura_bmp:.2f} °C")
        print(f"Presión atmosférica: {presion:.2f} hPa")
        print(f"Altitud estimada: {altitud:.2f} m")

        print("==============================================\n")
        time.sleep(1)

    except KeyboardInterrupt:
        print("\nPrograma detenido por el usuario.")
        break
    except Exception as e:
        print(f"Error leyendo sensores: {e}")
        time.sleep(1)