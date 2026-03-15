#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Librería para módulo GNSS+RTC DFRobot DFR1103
Comunicación I2C - Versión optimizada para CanSat
"""

from smbus2 import SMBus
import time
from datetime import datetime, timedelta

# Constantes del módulo
I2C_ADDR = 0x66
BUS = 1

# Registros del módulo (mapeo completo)
class REG:
    # Fecha y hora (0x00 - 0x06)
    YEAR_H = 0x00      # Año high byte
    YEAR_L = 0x01      # Año low byte
    MONTH = 0x02       # Mes
    DAY = 0x03         # Día
    HOUR = 0x04        # Hora UTC
    MINUTE = 0x05      # Minuto
    SECOND = 0x06      # Segundo
    
    # Latitud (0x07 - 0x0C)
    LAT_1 = 0x07       # Grados
    LAT_2 = 0x08       # Minutos (parte entera)
    LAT_3 = 0x09       # Minutos fracción (byte alto)
    LAT_4 = 0x0A       # Minutos fracción (byte medio)
    LAT_5 = 0x0B       # Minutos fracción (byte bajo)
    LAT_6 = 0x0C       # N/S (0=Norte, 1=Sur)
    
    # Longitud (0x0D - 0x12)
    LON_1 = 0x0D       # Grados
    LON_2 = 0x0E       # Minutos (parte entera)
    LON_3 = 0x0F       # Minutos fracción (byte alto)
    LON_4 = 0x10       # Minutos fracción (byte medio)
    LON_5 = 0x11       # Minutos fracción (byte bajo)
    LON_6 = 0x12       # E/O (0=Este, 1=Oeste)
    
    # Otros datos
    USE_STAR = 0x13    # Satélites usados
    ALT_H = 0x14       # Altitud high byte
    ALT_M = 0x15       # Altitud medium byte
    ALT_L = 0x16       # Altitud low byte
    SPEED = 0x17       # Velocidad
    COURSE = 0x18      # Rumbo


class GNSSAndRTC:
    """
    Clase principal para comunicación con módulo GNSS+RTC DFR1103
    Versión ligera y optimizada para CanSat
    """
    
    def __init__(self, bus=1, addr=0x66):
        """
        Inicializa comunicación I2C
        bus: número del bus I2C (1 para Raspberry Pi)
        addr: dirección I2C del módulo (0x66 por defecto)
        """
        self.bus = SMBus(bus)
        self.addr = addr
        self._ultima_lectura = 0
        self._cache = {}
        
    def __del__(self):
        """Limpieza al destruir el objeto"""
        try:
            self.bus.close()
        except:
            pass
    
    # ===== MÉTODOS PRIVADOS =====
    
    def _read_bytes(self, reg, n_bytes):
        """
        Lee n_bytes desde el registro reg
        Args:
            reg: registro inicial
            n_bytes: número de bytes a leer
        Returns:
            list: lista de bytes leídos
        """
        try:
            return self.bus.read_i2c_block_data(self.addr, reg, n_bytes)
        except Exception as e:
            print(f"Error I2C: {e}")
            return [0] * n_bytes
    
    def _read_byte(self, reg):
        """Lee un solo byte"""
        try:
            return self.bus.read_byte_data(self.addr, reg)
        except:
            return 0
    
    # ===== MÉTODOS PÚBLICOS =====
    
    def detectar(self):
        """
        Detecta si el módulo está presente
        Returns:
            bool: True si el módulo responde
        """
        try:
            self.bus.read_byte(self.addr)
            return True
        except:
            return False
    
    def get_fecha(self):
        """
        Obtiene fecha del GPS
        Returns:
            tuple: (año, mes, día) o (0,0,0) si error
        """
        data = self._read_bytes(REG.YEAR_H, 4)
        if len(data) >= 4:
            año = (data[0] << 8) | data[1]
            mes = data[2]
            dia = data[3]
            return año, mes, dia
        return 0, 0, 0
    
    def get_hora_utc(self):
        """
        Obtiene hora UTC del GPS
        Returns:
            tuple: (hora, minuto, segundo) o (0,0,0) si error
        """
        data = self._read_bytes(REG.HOUR, 3)
        if len(data) >= 3:
            return data[0], data[1], data[2]
        return 0, 0, 0
    
    def get_hora_local(self, utc_offset=2):
        """
        Obtiene hora local (UTC + offset)
        Args:
            utc_offset: diferencia horaria respecto UTC (2 para Ibiza verano)
        Returns:
            tuple: (hora, minuto, segundo) en hora local
        """
        h, m, s = self.get_hora_utc()
        if h == 0 and m == 0 and s == 0:
            return 0, 0, 0
        
        # Crear objeto datetime y sumar offset
        try:
            fecha_actual = datetime.now().date()
            hora_utc_dt = datetime.combine(fecha_actual, 
                                          datetime.min.time().replace(hour=h, minute=m, second=s))
            hora_local_dt = hora_utc_dt + timedelta(hours=utc_offset)
            return hora_local_dt.hour, hora_local_dt.minute, hora_local_dt.second
        except:
            return h, m, s
    
    def get_latitud(self):
        """
        Calcula latitud en grados decimales
        Returns:
            float: latitud en grados (0.0 si error)
        """
        data = self._read_bytes(REG.LAT_1, 6)
        if len(data) < 6:
            return 0.0
        
        grados = data[0]
        minutos_enteros = data[1]
        minutos_frac = (data[2] << 16) | (data[3] << 8) | data[4]
        norte_sur = data[5]  # 0=Norte, 1=Sur
        
        # Convertir a grados decimales
        lat = grados + minutos_enteros/60.0 + (minutos_frac/100000.0)/60.0
        
        # Si es sur, negativo
        if norte_sur == 1:
            lat = -lat
            
        return lat
    
    def get_longitud(self):
        """
        Calcula longitud en grados decimales
        Returns:
            float: longitud en grados (0.0 si error)
        """
        data = self._read_bytes(REG.LON_1, 6)
        if len(data) < 6:
            return 0.0
        
        grados = data[0]
        minutos_enteros = data[1]
        minutos_frac = (data[2] << 16) | (data[3] << 8) | data[4]
        este_oeste = data[5]  # 0=Este, 1=Oeste
        
        # Convertir a grados decimales
        lon = grados + minutos_enteros/60.0 + (minutos_frac/100000.0)/60.0
        
        # Si es oeste, negativo
        if este_oeste == 1:
            lon = -lon
            
        return lon
    
    def get_altitud(self):
        """
        Obtiene altitud en metros
        Returns:
            float: altitud en metros
        """
        data = self._read_bytes(REG.ALT_H, 3)
        if len(data) < 3:
            return 0.0
        
        # Decodificar altitud
        alt = ((data[0] & 0x7F) << 8 | data[1]) + data[2] / 100.0
        return alt
    
    def get_satelites(self):
        """
        Obtiene número de satélites usados
        Returns:
            int: número de satélites
        """
        return self._read_byte(REG.USE_STAR)
    
    def has_fix(self):
        """
        Verifica si hay señal GPS válida
        Returns:
            bool: True si hay señal y datos válidos
        """
        año, _, _ = self.get_fecha()
        sat = self.get_satelites()
        lat = self.get_latitud()
        lon = self.get_longitud()
        
        # Criterios para considerar señal válida
        return (año > 2020 and sat >= 3 and lat != 0 and lon != 0)
    
    def get_all_data(self):
        """
        Lee todos los datos GPS de una vez (optimizado)
        Returns:
            dict: diccionario con todos los datos
        """
        # Leer todos los registros de una vez (0x00 a 0x16 = 23 bytes)
        data = self._read_bytes(0x00, 23)
        
        if len(data) < 23:
            return self._datos_por_defecto()
        
        # Decodificar fecha
        año = (data[REG.YEAR_H] << 8) | data[REG.YEAR_L]
        mes = data[REG.MONTH]
        dia = data[REG.DAY]
        
        # Decodificar hora
        hora = data[REG.HOUR]
        minuto = data[REG.MINUTE]
        segundo = data[REG.SECOND]
        
        # Decodificar latitud
        lat_grados = data[REG.LAT_1]
        lat_min_ent = data[REG.LAT_2]
        lat_min_frac = (data[REG.LAT_3] << 16) | (data[REG.LAT_4] << 8) | data[REG.LAT_5]
        lat_ns = data[REG.LAT_6]
        
        lat = lat_grados + lat_min_ent/60.0 + (lat_min_frac/100000.0)/60.0
        if lat_ns == 1:
            lat = -lat
        
        # Decodificar longitud
        lon_grados = data[REG.LON_1]
        lon_min_ent = data[REG.LON_2]
        lon_min_frac = (data[REG.LON_3] << 16) | (data[REG.LON_4] << 8) | data[REG.LON_5]
        lon_eo = data[REG.LON_6]
        
        lon = lon_grados + lon_min_ent/60.0 + (lon_min_frac/100000.0)/60.0
        if lon_eo == 1:
            lon = -lon
        
        # Decodificar altitud
        alt = ((data[REG.ALT_H] & 0x7F) << 8 | data[REG.ALT_M]) + data[REG.ALT_L] / 100.0
        
        # Satélites
        sat = data[REG.USE_STAR]
        
        return {
            'año': año,
            'mes': mes,
            'dia': dia,
            'hora': hora,
            'minuto': minuto,
            'segundo': segundo,
            'latitud': lat,
            'longitud': lon,
            'altitud': alt,
            'satelites': sat,
            'fix_valido': (año > 2020 and sat >= 3 and lat != 0 and lon != 0)
        }
    
    def _datos_por_defecto(self):
        """Retorna diccionario con valores por defecto"""
        return {
            'año': 0, 'mes': 0, 'dia': 0,
            'hora': 0, 'minuto': 0, 'segundo': 0,
            'latitud': 0.0, 'longitud': 0.0,
            'altitud': 0.0, 'satelites': 0,
            'fix_valido': False
        }


# ===== FUNCIÓN DE AYUDA =====

def hora_local_desde_utc(hora_utc, min_utc, seg_utc, offset_horas=2):
    """
    Convierte hora UTC a hora local
    Args:
        hora_utc, min_utc, seg_utc: hora UTC
        offset_horas: diferencia horaria (2 para Ibiza verano)
    Returns:
        tuple: (hora_local, min_local, seg_local)
    """
    try:
        # Usar fecha actual para la conversión
        ahora = datetime.now()
        fecha_base = datetime(ahora.year, ahora.month, ahora.day, 
                             hora_utc, min_utc, seg_utc)
        fecha_local = fecha_base + timedelta(hours=offset_horas)
        return fecha_local.hour, fecha_local.minute, fecha_local.second
    except:
        return hora_utc, min_utc, seg_utc