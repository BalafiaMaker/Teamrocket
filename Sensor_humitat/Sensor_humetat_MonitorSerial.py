"""
PROGRAMA DE LECTURA DE SENSOR DE HUMEDAD DEL SUELO - VERSIÓN ESTABILIZADA
---------------------------------------------------------------------
Este programa muestra el paquete de datos para CanSat con lecturas estabilizadas
"""

# ============================================================
# 1. IMPORTAR LAS LIBRERÍAS NECESARIAS
# ============================================================
import time
import board
import busio
import json
import statistics  # Para calcular mediana
from collections import deque  # Para buffer circular
from datetime import datetime

from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15 import ads1x15

# ============================================================
# 2. CONFIGURAR LA COMUNICACIÓN I2C
# ============================================================
print("Iniciando comunicación I2C...")
i2c = busio.I2C(board.SCL, board.SDA)

# ============================================================
# 3. INICIALIZAR EL CONVERSOR ANALÓGICO-DIGITAL ADS1115
# ============================================================
print("Inicializando ADS1115...")
ads = ADS1115(i2c)
ads.gain = 1  # gain = 1 permite medir hasta 4.096V
canal_sensor = AnalogIn(ads, ads1x15.Pin.A0)

# ============================================================
# 4. CONFIGURACIÓN DE FILTRADO
# ============================================================
# Buffer circular para guardar las últimas 5 lecturas
buffer_lecturas = deque(maxlen=5)

def leer_sensor_estabilizado():
    """
    Lee el sensor y estabiliza el valor usando:
    1. Toma 5 lecturas rápidas
    2. Elimina el valor máximo y mínimo
    3. Promedia los 3 valores restantes
    """
    lecturas = []
    
    # Tomar 5 lecturas rápidas (sin esperar 1 segundo)
    for _ in range(5):
        lecturas.append(canal_sensor.value)
        time.sleep(0.05)  # 50ms entre lecturas
    
    # Ordenar las lecturas
    lecturas.sort()
    
    # Eliminar la más alta y la más baja, promediar el resto
    lecturas_filtradas = lecturas[1:4]  # Quita primera y última
    valor_estabilizado = sum(lecturas_filtradas) / len(lecturas_filtradas)
    
    return valor_estabilizado

# ============================================================
# 5. CARGAR LOS VALORES DE CALIBRACIÓN
# ============================================================
print("Cargando calibración del sensor...")

try:
    with open("calibracion_sensor.json", "r") as archivo:
        calibracion = json.load(archivo)

    VALOR_SECO = calibracion["seco"]
    VALOR_AGUA = calibracion["agua"]
    RANGO = calibracion["rango"]

    print("✅ Calibración cargada correctamente")
    print(f"   Valor en seco: {VALOR_SECO:.2f}")
    print(f"   Valor en agua: {VALOR_AGUA:.2f}")

except FileNotFoundError:
    print("❌ ERROR: No se encuentra el archivo 'calibracion_sensor.json'")
    exit()

except Exception as error:
    print(f"❌ ERROR al leer la calibración: {error}")
    exit()

# ============================================================
# 6. FUNCIÓN PARA CONVERTIR LECTURA A PORCENTAJE
# ============================================================
def calcular_porcentaje_humedad(valor_lectura):
    """Convierte el valor del sensor a porcentaje de humedad (0-100%)"""
    if VALOR_AGUA < VALOR_SECO:  # mayor humedad = menor valor
        if valor_lectura >= VALOR_SECO:
            return 0
        elif valor_lectura <= VALOR_AGUA:
            return 100
        else:
            return ((VALOR_SECO - valor_lectura) / (VALOR_SECO - VALOR_AGUA)) * 100
    else:  # mayor humedad = mayor valor
        if valor_lectura <= VALOR_SECO:
            return 0
        elif valor_lectura >= VALOR_AGUA:
            return 100
        else:
            return ((valor_lectura - VALOR_SECO) / (VALOR_AGUA - VALOR_SECO)) * 100

# ============================================================
# 7. FUNCIÓN PARA DETERMINAR ESTADO DEL SENSOR (0, 1, 2)
# ============================================================
def determinar_estado(humedad):
    """
    Clasifica el estado de humedad en 3 valores:
    2 = Hi ha aigua líquida (más de 80% humedad)
    1 = Potser hi ha aigua (entre 30% y 80% humedad)
    0 = No hi ha aigua (menos de 30% humedad)
    """
    if humedad >= 80:
        return 2  # Hi ha aigua líquida
    elif humedad >= 30:
        return 1  # Potser hi ha aigua
    else:
        return 0  # No hi ha aigua

# ============================================================
# 8. PROGRAMA PRINCIPAL - MOSTRAR PAQUETE ESTABILIZADO
# ============================================================
print("\n" + "=" * 70)
print("     CANSAT - PAQUETE DE DATOS DE HUMEDAD (ESTABILIZADO)")
print("=" * 70)
print("📦 FORMATO DEL PAQUETE (datos cada 1 segundo):")
print("   paquete,humedad(%),estado_suelo,estabilidad")
print("")
print("   donde:")
print("   - paquete: número de secuencia (empieza en 1)")
print("   - humedad: porcentaje de humedad (0-100%)")
print("   - estado_suelo: 0=seco, 1=húmedo, 2=agua")
print("   - estabilidad: 'estable' o 'variable' (diagnóstico)")
print("-" * 70)

try:
    contador = 1
    ultimas_humedades = deque(maxlen=3)  # Guarda últimas 3 humedades
    
    while True:
        # 8.1 LEER EL SENSOR CON ESTABILIZACIÓN
        # -------------------------
        valor_estabilizado = leer_sensor_estabilizado()
        
        # 8.2 CALCULAR HUMEDAD Y ESTADO
        # -------------------------
        humedad = calcular_porcentaje_humedad(valor_estabilizado)
        estado = determinar_estado(humedad)
        
        # 8.3 VERIFICAR ESTABILIDAD (para diagnóstico)
        # -------------------------
        ultimas_humedades.append(humedad)
        if len(ultimas_humedades) == 3:
            # Si la humedad varía más de 20% entre lecturas
            if max(ultimas_humedades) - min(ultimas_humedades) > 20:
                estabilidad = "F"
            else:
                estabilidad = "E"
        else:
            estabilidad = "E"
        
        # 8.4 MOSTRAR EL PAQUETE COMPLETO
        # -------------------------
        print(f"{contador},{humedad:.1f},{estado},{estabilidad}")
        
        # 8.5 ESPERAR 1 SEGUNDO
        # -------------------------
        time.sleep(1)
        contador += 1

except KeyboardInterrupt:
    print("\n" + "-" * 70)
    print("⏹️  Programa detenido por el usuario")
    print(f"   Total de paquetes: {contador-1}")
    print("   ¡Hasta luego!")