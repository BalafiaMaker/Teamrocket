from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont
import time

# Configuración SPI según tu esquema
serial = spi(device=0, port=0, gpio_DC=13, gpio_RST=6)

# Crear dispositivo OLED
device = sh1106(serial)

# Fuente
font = ImageFont.load_default()

# Mostrar mensaje
with canvas(device) as draw:
    draw.text((5, 20), "Funcionando", font=font, fill=255)
    draw.text((5, 35), "CanSat", font=font, fill=255)
    draw.text((5, 50), "Team Rocket", font=font, fill=255)

time.sleep(10)