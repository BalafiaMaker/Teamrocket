#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cansat_main.py
Programa principal para telemetría del CanSat Team Rocket.
Lee todos los sensores cada 1 segundo y genera salida CSV en consola y archivo.
VERSIÓN DEFINITIVA - Preparada para Raspberry Pi Zero
"""

import time
import signal
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Importar nuestra librería de sensores
from cansat_sensors import create_default_sensor_manager, SensorManager, scan_i2c_devices

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
INTERVALO_LECTURA = 1.0  # segundos
ARCHIVO_DATOS = "telemetria_cansat.csv"
EQUIPO = "TeamRocket"  # Nombre del equipo

# -----------------------------------------------------------------------------
# Clase principal del programa
# -----------------------------------------------------------------------------
class CanSatTelemetria:
    """
    Clase principal que gestiona la telemetría del CanSat.
    """
    def __init__(self, archivo: str = ARCHIVO_DATOS):
        """
        Inicializa el sistema de telemetría.
        
        Args:
            archivo: Nombre del archivo donde guardar los datos
        """
        self.archivo = archivo
        self.sensor_manager: Optional[SensorManager] = None
        self.contador_paquete = 0
        self.tiempo_inicio: Optional[float] = None
        self.archivo_handle = None
        self.ejecutando = False
        
        # Manejador de señal para cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Manejador de señales para cierre controlado."""
        print(f"\nSeñal {signum} recibida. Cerrando programa...")
        self.ejecutando = False
        
    def inicializar_sensores(self) -> bool:
        """
        Inicializa todos los sensores.
        
        Returns:
            bool: True si al menos un sensor se inicializó correctamente
        """
        print("\n" + "="*60)
        print("CAN SAT TEAM ROCKET - SISTEMA DE TELEMETRÍA")
        print("="*60 + "\n")
        
        # Escanear bus I2C para diagnóstico
        print("Escaneando bus I2C...")
        dispositivos = scan_i2c_devices()
        if dispositivos:
            print(f"Dispositivos encontrados: {[hex(d) for d in dispositivos]}")
        else:
            print("No se encontraron dispositivos I2C")
        print()
        
        # Crear gestor de sensores con configuración por defecto
        self.sensor_manager = create_default_sensor_manager(sea_level_pressure=1013.25)
        
        # Inicializar todos los sensores
        print("Inicializando sensores...")
        exito = self.sensor_manager.init_all()
        
        if exito:
            print(f"\n✅ Sensores activos: {self.sensor_manager.get_sensor_names()}")
        else:
            print("\n❌ No se pudo inicializar ningún sensor")
            
        return exito
    
    def generar_cabecera(self) -> str:
        """
        Genera la línea de cabecera con nombres y unidades.
        
        Returns:
            str: Cabecera CSV
        """
        cabecera = [
            "paquete",              # Número de paquete
            "time_s",                # Tiempo desde inicio (segundos)
            "temperature_C",         # Temperatura en grados Celsius
            "pressure_hPa",          # Presión en hPa
            "humidity_pct",          # Humedad relativa %
            "lat_deg",               # Latitud en grados
            "lon_deg",               # Longitud en grados
            "alt_m_GPS",             # Altitud GPS en metros
            "alt_m_Patm",            # Altitud barométrica en metros
            "accel_x_g",             # Aceleración X en g (1g = 9.8 m/s²)
            "accel_y_g",             # Aceleración Y en g
            "accel_z_g",             # Aceleración Z en g
            "quat_w",                # Cuaternión w
            "quat_x",                # Cuaternión x
            "quat_y",                # Cuaternión y
            "quat_z",                # Cuaternión z
            "gyro_x_dps",            # Giroscopio X grados/segundo
            "gyro_y_dps",            # Giroscopio Y grados/segundo
            "gyro_z_dps",            # Giroscopio Z grados/segundo
            "mag_x_uT",              # Magnetómetro X microTeslas
            "mag_y_uT",              # Magnetómetro Y microTeslas
            "mag_z_uT",              # Magnetómetro Z microTeslas
            "euler_heading_deg",     # Ángulo de orientación (heading)
            "euler_roll_deg",        # Ángulo de alabeo (roll)
            "euler_pitch_deg",       # Ángulo de cabeceo (pitch)
            "velocidad_kmh",         # Velocidad en km/h (desde GPS)
            "satelites",             # Número de satélites
            "analog_ch0_voltage",    # Sensor analógico canal 0 (ej. humedad suelo)
            "analog_ch1_voltage",    # Sensor analógico canal 1 (ej. detector agua)
            "equipo"                 # Nombre del equipo
        ]
        
        return ",".join(cabecera)
    
    def convertir_a_g(self, accel_ms2: float) -> float:
        """
        Convierte aceleración de m/s² a g's.
        
        Args:
            accel_ms2: Aceleración en m/s²
            
        Returns:
            float: Aceleración en g's
        """
        if accel_ms2 == 0.0 or math.isnan(accel_ms2):
            return float('nan')
        return accel_ms2 / 9.80665
    
    def generar_linea_telemetria(self, datos: Dict[str, Any]) -> str:
        """
        Genera una línea CSV con los datos de telemetría.
        Si un valor no está disponible, escribe "nan".
        
        Args:
            datos: Diccionario con todos los datos de sensores
            
        Returns:
            str: Línea CSV completa
        """
        # Tiempo actual desde inicio
        tiempo_actual = time.time() - self.tiempo_inicio if self.tiempo_inicio else 0
        
        # Extraer valores con nan por defecto
        valores = []
        
        # Paquete y tiempo
        valores.append(str(self.contador_paquete))
        valores.append(f"{tiempo_actual:.3f}")
        
        # BME280
        valores.append(str(datos.get("temperature", "nan")))
        valores.append(str(datos.get("pressure", "nan")))
        valores.append(str(datos.get("humidity", "nan")))
        
        # GNSS
        valores.append(str(datos.get("latitude", "nan")))
        valores.append(str(datos.get("longitude", "nan")))
        valores.append(str(datos.get("gps_altitude", "nan")))
        
        # Altitud barométrica
        valores.append(str(datos.get("altitude_barometric", "nan")))
        
        # Aceleraciones (convertir a g's)
        accel_x = datos.get("bno_accel_x", 0.0)
        accel_y = datos.get("bno_accel_y", 0.0)
        accel_z = datos.get("bno_accel_z", 0.0)
        
        valores.append(f"{self.convertir_a_g(accel_x):.4f}" if accel_x != 0.0 else "nan")
        valores.append(f"{self.convertir_a_g(accel_y):.4f}" if accel_y != 0.0 else "nan")
        valores.append(f"{self.convertir_a_g(accel_z):.4f}" if accel_z != 0.0 else "nan")
        
        # Cuaterniones
        valores.append(str(datos.get("bno_quat_w", "nan")))
        valores.append(str(datos.get("bno_quat_x", "nan")))
        valores.append(str(datos.get("bno_quat_y", "nan")))
        valores.append(str(datos.get("bno_quat_z", "nan")))
        
        # Giroscopio
        valores.append(str(datos.get("bno_gyro_x", "nan")))
        valores.append(str(datos.get("bno_gyro_y", "nan")))
        valores.append(str(datos.get("bno_gyro_z", "nan")))
        
        # Magnetómetro
        valores.append(str(datos.get("bno_mag_x", "nan")))
        valores.append(str(datos.get("bno_mag_y", "nan")))
        valores.append(str(datos.get("bno_mag_z", "nan")))
        
        # Euler
        valores.append(str(datos.get("bno_euler_heading", "nan")))
        valores.append(str(datos.get("bno_euler_roll", "nan")))
        valores.append(str(datos.get("bno_euler_pitch", "nan")))
        
        # Velocidad en km/h
        velocidad_ms = datos.get("gps_speed", 0.0)
        if velocidad_ms and velocidad_ms != 0.0:
            valores.append(f"{velocidad_ms * 3.6:.2f}")
        else:
            valores.append("nan")
        
        # Satélites
        valores.append(str(datos.get("satellites", "nan")))
        
        # Sensores analógicos
        valores.append(str(datos.get("analog_ch0_voltage", "nan")))
        valores.append(str(datos.get("analog_ch1_voltage", "nan")))
        
        # Equipo
        valores.append(EQUIPO)
        
        return ",".join(valores)
    
    def iniciar_archivo(self):
        """Abre el archivo de datos y escribe la cabecera."""
        try:
            # Verificar si el archivo ya existe para no duplicar cabecera
            archivo_existe = os.path.isfile(self.archivo)
            
            self.archivo_handle = open(self.archivo, 'a')
            
            if not archivo_existe or os.path.getsize(self.archivo) == 0:
                cabecera = self.generar_cabecera()
                self.archivo_handle.write(cabecera + "\n")
                self.archivo_handle.flush()
                print(f"📁 Archivo creado: {self.archivo}")
                print(f"📋 Cabecera: {cabecera}\n")
            else:
                print(f"📁 Archivo existente: {self.archivo} (añadiendo datos)\n")
                
        except Exception as e:
            print(f"❌ Error al abrir archivo: {e}")
            sys.exit(1)
    
    def ejecutar(self):
        """Bucle principal de telemetría."""
        
        # Inicializar sensores
        if not self.inicializar_sensores():
            print("⚠️ Continuando con los sensores disponibles...")
        
        # Iniciar archivo
        self.iniciar_archivo()
        
        # Mostrar cabecera en consola
        print("📡 INICIANDO TELEMETRÍA - CTRL+C para detener\n")
        print(self.generar_cabecera())
        
        # Variables de control
        self.ejecutando = True
        self.tiempo_inicio = time.time()
        errores_consecutivos = 0
        max_errores = 10
        
        try:
            while self.ejecutando:
                ciclo_inicio = time.time()
                
                try:
                    # Leer todos los sensores
                    datos = self.sensor_manager.read_all()
                    
                    # Generar línea de telemetría
                    linea = self.generar_linea_telemetria(datos)
                    
                    # Mostrar en consola
                    print(linea)
                    sys.stdout.flush()  # Forzar salida inmediata
                    
                    # Guardar en archivo
                    if self.archivo_handle:
                        self.archivo_handle.write(linea + "\n")
                        self.archivo_handle.flush()  # Asegurar escritura en disco
                    
                    # Incrementar contador de paquetes
                    self.contador_paquete += 1
                    errores_consecutivos = 0
                    
                except Exception as e:
                    errores_consecutivos += 1
                    print(f"❌ Error en ciclo de lectura: {e}")
                    
                    if errores_consecutivos >= max_errores:
                        print(f"⚠️ Demasiados errores consecutivos ({max_errores}). Deteniendo...")
                        break
                
                # Calcular tiempo de espera para mantener intervalo constante
                tiempo_ciclo = time.time() - ciclo_inicio
                tiempo_espera = max(0, INTERVALO_LECTURA - tiempo_ciclo)
                
                # Pequeña pausa para no saturar la CPU
                if tiempo_espera > 0:
                    time.sleep(tiempo_espera)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Programa detenido por el usuario")
        finally:
            self.cerrar()
    
    def cerrar(self):
        """Cierra todos los recursos de forma ordenada."""
        print("\n" + "="*60)
        print("CERRANDO SISTEMA DE TELEMETRÍA")
        print("="*60)
        
        # Estadísticas finales
        if self.contador_paquete > 0 and self.tiempo_inicio:
            duracion = time.time() - self.tiempo_inicio
            print(f"📊 Paquetes enviados: {self.contador_paquete}")
            print(f"⏱️  Duración total: {duracion:.1f} segundos")
            print(f"📈 Tasa media: {self.contador_paquete/duracion:.2f} paquetes/segundo")
        
        # Cerrar archivo
        if self.archivo_handle:
            self.archivo_handle.close()
            print(f"💾 Datos guardados en: {self.archivo}")
        
        # Apagar sensores
        if self.sensor_manager:
            self.sensor_manager.shutdown()
        
        print("\n✅ Programa finalizado correctamente")

# -----------------------------------------------------------------------------
# Punto de entrada principal
# -----------------------------------------------------------------------------
def main():
    """
    Función principal del programa.
    """
    # Crear y ejecutar el sistema de telemetría
    telemetria = CanSatTelemetria(archivo=ARCHIVO_DATOS)
    telemetria.ejecutar()


if __name__ == "__main__":
    # Importar math aquí para la conversión a g's
    import math
    main()