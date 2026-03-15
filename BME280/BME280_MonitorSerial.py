# -*- coding: utf-8 -*

from __future__ import print_function
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from DFRobot_BME280 import *

sensor = DFRobot_BME280_I2C(i2c_addr = 0x77, bus = 1)

def setup():
  while not sensor.begin():
    print ('Please check that the device is properly connected')
    time.sleep(3)
  print("sensor begin successfully!!!")

  sensor.set_config_filter(BME280_IIR_FILTER_SETTINGS[0])
  sensor.set_config_T_standby(BME280_CONFIG_STANDBY_TIME_125)
  sensor.set_ctrl_meas_sampling_temp(BME280_TEMP_OSR_SETTINGS[3])
  sensor.set_ctrl_meas_sampling_press(BME280_PRESS_OSR_SETTINGS[3])
  sensor.set_ctrl_sampling_humi(BME280_HUMI_OSR_SETTINGS[3])
  sensor.set_ctrl_meas_mode(NORMAL_MODE)

  time.sleep(2)   # Wait for configuration to complete
 
  if( sensor.calibrated_absolute_difference(115.0) == True ):# Canvia l'altura del lloc en que estas.
    print("Absolute difference base value set successfully!")
  # Addicionem aquesta instrucció per saber qui és cada data de la trama.
  print("paquete, temperatura_C,Pressio_Pa,Humitat_%RH,Altitud_m,Nom_Equip") 

def loop():
  global flag
 # configurem les variables globals necessaries per a cada dada.
  global paquete,temp,pres,hum,alt
  if sensor.get_data_ready_status:
    # Guarda a les variables les lectures corresponents
    paquete = 0
    temp = sensor.get_temperature
    pres = sensor.get_pressure
    hum = sensor.get_humidity
    alt = sensor.get_altitude
    paquete +=1

    # cream la trama separada de comas. :.2f posa 2 decimals al valor
    print(f"{paquete},{temp:.2f},{pres:.2f},{hum:.2f},{alt:.2f},teamrocket")
    time.sleep(1)


if __name__ == "__main__":
  setup()
  while True:
    loop()
