from cansat_sensors import create_default_sensor_manager
import time

manager=create_default_sensor_manager()

manager.init_all()

packet=1

while True:

    data=manager.read_all()

    data["packet"]=packet

    manager.save_csv("cansat_data.csv",data)

    print(data)

    packet+=1

    time.sleep(1)