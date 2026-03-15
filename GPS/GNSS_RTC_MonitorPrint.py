#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programa principal para lectura GPS usando librería GNSSAndRTC
Muestra el mismo formato que el programa original
"""

import time
from datetime import datetime, timedelta
from GNSSAndRTC import GNSSAndRTC, hora_local_desde_utc

def main():
    """
    Función principal del programa
    """
    
    # ===== INICIALIZACIÓN =====
    print("Inicializando módulo GNSS...")
    
    # Crear instancia del GNSS
    gps = GNSSAndRTC()
    
    # Verificar comunicación
    if not gps.detectar():
        print("ERROR: No se encuentra el módulo GNSS")
        print("Verifica las conexiones I2C (GPIO2 SDA, GPIO3 SCL)")
        return
    
    print("Módulo GNSS detectado correctamente")
    
    # ===== VARIABLES =====
    paquete = 0
    tiempo_inicial = None
    primera_lectura = False
    
    # ===== ESPERAR PRIMER FIX =====
    print("Esperando señal GPS...")
    
    while not primera_lectura:
        if gps.has_fix():
            # Leer fecha y hora
            año, mes, dia = gps.get_fecha()
            h_utc, m_utc, s_utc = gps.get_hora_utc()
            
            if año > 2020:
                primera_lectura = True
                
                # Convertir a hora local (Ibiza, UTC+2)
                h_local, m_local, s_local = hora_local_desde_utc(h_utc, m_utc, s_utc, 1)
                
                # Crear objeto datetime para formatear
                fecha_local = datetime(año, mes, dia, h_local, m_local, s_local)
                
                # Guardar tiempo inicial
                tiempo_inicial = time.time()
                
                # Mostrar información inicial (SOLO UNA VEZ)
                print("\n" + "="*50)
                print("FECHA CAPTURA DATOS: {} del {} de {} de {}".format(
                    fecha_local.strftime("%A"),
                    fecha_local.day,
                    fecha_local.strftime("%B"),
                    fecha_local.year))
                print("HORA GPS (local Ibiza): {}".format(
                    fecha_local.strftime("%H:%M:%S")))
                print("="*50 + "\n")
                
                # Cabecera CSV (SOLO UNA VEZ)
                print("# paquete, tiempo (segundos), latitud (grados), longitud (grados), altitud_GPS (m), n_sat")
                print("# La fecha de inicio de la toma de datos fue: {}".format(
                    fecha_local.strftime("%d/%m/%Y a las %H:%M:%S")))
        else:
            print("No encuentra GPS", end="\r")
            time.sleep(1)
    
    # ===== BUCLE PRINCIPAL =====
    try:
        while True:
            if gps.has_fix():
                # Leer datos individuales (como en el programa original)
                latitud = gps.get_latitud()
                longitud = gps.get_longitud()
                altitud = gps.get_altitud()
                num_sat = gps.get_satelites()
                
                # Calcular tiempo relativo
                t = round(time.time() - tiempo_inicial, 2)
                
                # Mostrar en formato CSV
                print(f"{paquete},{t:.2f},{latitud:.6f},{longitud:.6f},{altitud:.1f},{num_sat}")
                
                paquete += 1
            else:
                print("No encuentra GPS")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nPrograma terminado por el usuario")
        print(f"Total de paquetes enviados: {paquete}")
        if tiempo_inicial:
            duracion = round(time.time() - tiempo_inicial, 1)
            print(f"Duración total: {duracion} segundos")

if __name__ == "__main__":
    main()