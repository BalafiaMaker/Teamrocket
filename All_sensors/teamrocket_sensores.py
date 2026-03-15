#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ejemplo de uso de la librería teamrocket_sensors.py
Lee todos los sensores cada segundo y muestra los datos.
"""

import time
from teamrocket_sensors import SensorManager

def main():
    print("Iniciando CanSat Team Rocket - Sistema de Sensores")
    print("-" * 50)

    # Crear el gestor de sensores
    # Configuramos:
    # - BME280: activado
    # - BNO055: activado
    # - GNSS: activado (necesita antena y cielo abierto)
    # - Analógico: activado, con canales 0 y 1 (ejemplo: humedad suelo + otro sensor)
    manager = SensorManager(
        use_bme280=True,
        use_bno055=True,
        use_gnss=True,
        use_analog=True,
        analog_channels=[0, 1]  # Dos sensores analógicos en canales A0 y A1
    )

    # Inicializar todos los sensores
    if not manager.init_all():
        print("Error crítico: No se pudo inicializar ningún sensor.")
        return

    print("\nSensores activos:", list(manager.sensors.keys()))
    print("Leyendo datos cada 1 segundo. Pulsa Ctrl+C para detener.\n")

    try:
        while True:
            # Leer todos los sensores de una vez
            datos = manager.read_all()

            # Mostrar datos más relevantes de forma legible
            print(f"\n[{datos['timestamp']}]")
            print(f"  BME280: T={datos.get('temperature', 'N/A'):.1f}°C, "
                  f"P={datos.get('pressure', 'N/A'):.1f}hPa, "
                  f"H={datos.get('humidity', 'N/A'):.1f}%")

            print(f"  BNO055: Accel=({datos.get('accel_x', 0):.2f}, {datos.get('accel_y', 0):.2f}, {datos.get('accel_z', 0):.2f}) m/s², "
                  f"Euler=({datos.get('euler_heading', 0):.1f}°, {datos.get('euler_roll', 0):.1f}°, {datos.get('euler_pitch', 0):.1f}°)")

            # GNSS (puede tardar en tener fix)
            if datos.get('fix_valid', False):
                print(f"  GNSS: ({datos.get('latitude', 0):.6f}, {datos.get('longitude', 0):.6f}) "
                      f"Alt={datos.get('gps_altitude', 0):.1f}m, Sat={datos.get('satellites', 0)}")
            else:
                print(f"  GNSS: Buscando fix... (satélites: {datos.get('satellites', 0)})")

            # Sensores analógicos
            print(f"  Analog CH0: value={datos.get('analog_ch0_value', 0)}, voltage={datos.get('analog_ch0_voltage', 0):.3f}V")
            print(f"  Analog CH1: value={datos.get('analog_ch1_value', 0)}, voltage={datos.get('analog_ch1_voltage', 0):.3f}V")

            # También podemos acceder al diccionario completo si queremos volcarlo a JSON
            # print(json.dumps(datos))

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nPrograma detenido por el usuario.")
        manager.shutdown()

if __name__ == "__main__":
    main()