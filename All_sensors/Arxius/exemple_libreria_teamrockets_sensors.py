
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ejemplo de uso de la librería cansat_sensors.py
Lee todos los sensores cada segundo y muestra los datos.
VERSIÓN CON CUATERNIONES DEL BNO055
"""

import time
import json
from cansat_sensors import SensorManager, scan_i2c_devices

def formatear_valor(valor, formato=".1f", por_defecto="N/A"):
    """
    Formatea un valor de manera segura, manejando strings y None.
    """
    if isinstance(valor, (int, float)):
        if abs(valor) < 0.0001 and formato.startswith('.'):
            return "0" + formato.replace('.', '.0')
        return f"{valor:{formato}}"
    return str(por_defecto)

def main():
    print("=" * 70)
    print("  CANSAT TEAM ROCKET - SISTEMA DE SENSORES")
    print("  VERSIÓN CON CUATERNIONES DEL BNO055")
    print("=" * 70)
    
    # Escanear dispositivos I2C (opcional, para diagnóstico)
    print("\n🔍 Escaneando bus I2C...")
    dispositivos = scan_i2c_devices()
    if dispositivos:
        print(f"   Dispositivos encontrados: {[hex(d) for d in dispositivos]}")
        print(f"   BNO055 esperado: 0x28/0x29 {'✅' if (0x28 in dispositivos or 0x29 in dispositivos) else '❌'}")
        print(f"   BME280 esperado: 0x76/0x77 {'✅' if (0x76 in dispositivos or 0x77 in dispositivos) else '❌'}")
        print(f"   ADS1115 esperado: 0x48 {'✅' if 0x48 in dispositivos else '❌'}")
        print(f"   GNSS esperado: 0x66 {'✅' if 0x66 in dispositivos else '❌'}")
    else:
        print("   No se encontraron dispositivos I2C")
    
    print("\n" + "-" * 70)
    print("Inicializando sensores...")
    print("-" * 70)

    # Crear el gestor de sensores con configuración personalizada
    manager = SensorManager(
        use_bme280=True,      # BME280 para temperatura, presión, humedad y altitud barométrica
        use_bno055=True,      # BNO055 para aceleración, giro, magnetómetro, Euler y CUATERNIONES
        use_gnss=True,        # GNSS para latitud, longitud, altitud GPS y velocidad
        use_analog=True,      # Sensores analógicos
        analog_channels=[0, 1],  # Canales A0 y A1
        sea_level_pressure=1013.25  # Presión a nivel del mar para altitud barométrica
    )

    # Inicializar todos los sensores
    if not manager.init_all():
        print("\n⚠️  Advertencia: Solo algunos sensores se inicializaron correctamente.")
    else:
        print("\n✅ Todos los sensores inicializados correctamente.")

    # Mostrar sensores activos
    sensores_activos = manager.get_sensor_names()
    print(f"\n📡 Sensores activos ({len(sensores_activos)}):")
    for sensor in sensores_activos:
        print(f"   - {sensor}")
    
    print("\n" + "=" * 70)
    print("📊 Leyendo datos cada 1 segundo. Pulsa Ctrl+C para detener.")
    print("=" * 70 + "\n")

    contador = 0
    try:
        while True:
            contador += 1
            # Leer todos los sensores de una vez
            datos = manager.read_all()
            
            # Mostrar número de paquete y timestamp
            print(f"\n📦 PAQUETE #{contador} - [{datos['timestamp']}]")
            print("-" * 70)
            
            # ===== BME280 =====
            if 'temperature' in datos:
                print(f"\n🌡️  BME280 (Barométrico):")
                print(f"   Temperatura: {formatear_valor(datos.get('temperature'), '.1f')} °C")
                print(f"   Presión:     {formatear_valor(datos.get('pressure'), '.1f')} hPa")
                print(f"   Humedad:     {formatear_valor(datos.get('humidity'), '.1f')} %")
                print(f"   Altitud (bar): {formatear_valor(datos.get('altitude_barometric'), '.1f')} m")
            else:
                print(f"\n🌡️  BME280: No disponible")
            
            # ===== BNO055 CON CUATERNIONES =====
            if 'bno_accel_x' in datos:
                print(f"\n🧭 BNO055 (9-DOF):")
                
                # Aceleración
                print(f"   📊 Aceleración: X={formatear_valor(datos.get('bno_accel_x'), '.2f')}, "
                      f"Y={formatear_valor(datos.get('bno_accel_y'), '.2f')}, "
                      f"Z={formatear_valor(datos.get('bno_accel_z'), '.2f')} m/s²")
                
                # Giroscopio
                print(f"   🔄 Giroscopio:  X={formatear_valor(datos.get('bno_gyro_x'), '.2f')}, "
                      f"Y={formatear_valor(datos.get('bno_gyro_y'), '.2f')}, "
                      f"Z={formatear_valor(datos.get('bno_gyro_z'), '.2f')} rad/s")
                
                # Magnetómetro
                print(f"   🧲 Magnetómetro: X={formatear_valor(datos.get('bno_mag_x'), '.2f')}, "
                      f"Y={formatear_valor(datos.get('bno_mag_y'), '.2f')}, "
                      f"Z={formatear_valor(datos.get('bno_mag_z'), '.2f')} uT")
                
                # Ángulos de Euler
                print(f"   📐 Euler:        Heading={formatear_valor(datos.get('bno_euler_heading'), '.1f')}°, "
                      f"Roll={formatear_valor(datos.get('bno_euler_roll'), '.1f')}°, "
                      f"Pitch={formatear_valor(datos.get('bno_euler_pitch'), '.1f')}°")
                
                # ===== CUATERNIONES =====
                if all(k in datos for k in ['bno_quat_w', 'bno_quat_x', 'bno_quat_y', 'bno_quat_z']):
                    w = datos.get('bno_quat_w', 0)
                    x = datos.get('bno_quat_x', 0)
                    y = datos.get('bno_quat_y', 0)
                    z = datos.get('bno_quat_z', 0)
                    
                    # Calcular magnitud del cuaternión (debería ser ~1.0)
                    magnitud = (w*w + x*x + y*y + z*z)**0.5
                    
                    print(f"   🔮 CUATERNIONES:")
                    print(f"      w={formatear_valor(w, '.4f')}, x={formatear_valor(x, '.4f')}")
                    print(f"      y={formatear_valor(y, '.4f')}, z={formatear_valor(z, '.4f')}")
                    print(f"      |q| = {formatear_valor(magnitud, '.3f')} (debe ser ≈1.0)")
                    
                    # Opcional: mostrar ángulo de rotación total
                    angulo = 2 * math.acos(min(1.0, max(-1.0, w))) * 180 / math.pi
                    print(f"      Ángulo rotación: {formatear_valor(angulo, '.1f')}°")
                
                # Temperatura interna del BNO055
                print(f"   🌡️  Temp. interna: {formatear_valor(datos.get('bno_temperature'), '.1f')} °C")
                
                # Estado de calibración
                if all(k in datos for k in ['bno_calibration_sys', 'bno_calibration_gyro', 
                                           'bno_calibration_accel', 'bno_calibration_mag']):
                    cal_sys = datos['bno_calibration_sys']
                    cal_gyro = datos['bno_calibration_gyro']
                    cal_acc = datos['bno_calibration_accel']
                    cal_mag = datos['bno_calibration_mag']
                    
                    # Indicador visual de calibración
                    def cal_icon(val):
                        return "✅" if val == 3 else "🟡" if val > 0 else "❌"
                    
                    print(f"   ⚡ Calibración:")
                    print(f"      SISTEMA: {cal_sys}/3 {cal_icon(cal_sys)} | "
                          f"GIRO: {cal_gyro}/3 {cal_icon(cal_gyro)}")
                    print(f"      ACEL: {cal_acc}/3 {cal_icon(cal_acc)} | "
                          f"MAG: {cal_mag}/3 {cal_icon(cal_mag)}")
            else:
                print(f"\n🧭 BNO055: No disponible")
            
            # ===== GNSS =====
            print(f"\n🛰️  GNSS:")
            if datos.get('fix_valid', False):
                print(f"   📍 Posición:    {formatear_valor(datos.get('latitude'), '.6f')}, "
                      f"{formatear_valor(datos.get('longitude'), '.6f')}")
                print(f"   🏔️  Altitud GPS: {formatear_valor(datos.get('gps_altitude'), '.1f')} m")
                print(f"   ⚡ Velocidad:   {formatear_valor(datos.get('gps_speed'), '.2f')} m/s "
                      f"({formatear_valor(datos.get('gps_speed_kmh'), '.2f')} km/h)")
                print(f"   🧭 Rumbo:       {formatear_valor(datos.get('gps_course'), '.1f')}°")
                print(f"   📡 Satélites:   {datos.get('satellites', 0)}")
                print(f"   ⏰ Hora UTC:    {datos.get('gps_time', '00:00:00')}")
                print(f"   📅 Fecha:       {datos.get('gps_date', '0000-00-00')}")
            else:
                print(f"   🔍 Buscando fix... (satélites: {datos.get('satellites', 0)})")
                if datos.get('satellites', 0) > 0:
                    print(f"   ⏰ Hora UTC:    {datos.get('gps_time', '00:00:00')}")
            
            # ===== Sensores Analógicos =====
            print(f"\n⚡ Sensores Analógicos (ADS1115):")
            hay_analogicos = False
            for ch in [0, 1]:
                valor = datos.get(f'analog_ch{ch}_value', 0)
                voltaje = datos.get(f'analog_ch{ch}_voltage', 0.0)
                if valor != 0 or voltaje != 0.0:
                    hay_analogicos = True
                    print(f"   CH{ch}: valor={valor} | voltaje={formatear_valor(voltaje, '.3f')}V")
            if not hay_analogicos:
                print(f"   No disponibles")
            
            print("-" * 70)
            
            # Opcional: descomentar para ver todos los datos en JSON
            # print(json.dumps(datos, indent=2, default=str))
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("⏹️  Programa detenido por el usuario")
        print(f"📊 Total de paquetes: {contador}")
        print("=" * 70)
        manager.shutdown()

# Necesario para math.acos en el cálculo del ángulo
import math

if __name__ == "__main__":
    main()
