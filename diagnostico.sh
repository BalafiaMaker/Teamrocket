#!/bin/bash
# diagnostico.sh - Script de diagnóstico para CanSat
# Ejecutar con: bash diagnostico.sh

echo "🔍 DIAGNÓSTICO CANSAT"
echo "====================="
echo ""

# 1. Verificar BNO055
echo -n "1. BNO055 (0x28/0x29): "
if i2cdetect -y 1 | grep -q "28\|29"; then
    echo "✅ DETECTADO"
    # Intentar leer el chip ID
    CHIP_ID=$(sudo i2cget -y 1 0x28 0x00 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   Chip ID: 0x$CHIP_ID (debe ser 0xA0)"
    else
        echo "   ⚠️ No responde a lectura"
    fi
else
    echo "❌ NO DETECTADO"
fi

# 2. Verificar BME280
echo -n "2. BME280 (0x76/0x77): "
if i2cdetect -y 1 | grep -q "76\|77"; then
    echo "✅ DETECTADO"
else
    echo "❌ NO DETECTADO"
fi

# 3. Verificar GNSS
echo -n "3. GNSS (0x66): "
if i2cdetect -y 1 | grep -q "66"; then
    echo "✅ DETECTADO"
else
    echo "❌ NO DETECTADO"
fi

# 4. Verificar ADS1115
echo -n "4. ADS1115 (0x48): "
if i2cdetect -y 1 | grep -q "48"; then
    echo "✅ DETECTADO"
else
    echo "❌ NO DETECTADO"
fi

# 5. Listar TODOS los dispositivos I2C
echo ""
echo "5. TODOS los dispositivos I2C detectados:"
sudo i2cdetect -y 1
echo ""

# 6. Verificar SPI para OLED
echo "6. Verificando SPI:"
if [ -e /dev/spidev0.0 ]; then
    echo "   ✅ SPI disponible"
    # Probar permisos
    if [ -r /dev/spidev0.0 ]; then
        echo "   ✅ Permisos SPI OK"
    else
        echo "   ⚠️ Permisos SPI: ejecutar 'sudo usermod -a -G spi teamrocket'"
    fi
else
    echo "   ❌ SPI no disponible"
    echo "   Ejecutar: sudo raspi-config -> Interface Options -> SPI -> Enable"
fi

# 7. Verificar UART
echo ""
echo "7. Verificando UART:"
if [ -e /dev/serial0 ]; then
    echo "   ✅ UART disponible"
    ls -l /dev/serial0
else
    echo "   ❌ UART no disponible"
    echo "   Añadir a /boot/config.txt: enable_uart=1"
fi

# 8. Verificar pines OLED
echo ""
echo "8. Pines GPIO para OLED:"
for pin in 6 13 19; do
    if [ -e /sys/class/gpio/gpio$pin ]; then
        echo "   GPIO$pin: Exportado"
    else
        echo "   GPIO$pin: No exportado (se exportará en el programa)"
    fi
done

echo ""
echo "✅ DIAGNÓSTICO COMPLETADO"