#!/bin/bash

esptool.py --port /dev/ttyUSB0 --baud 460800 erase_flash
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 ~/Downloads/esp8266-20171101-v1.9.3.bin

sleep 5

echo "Uploading BME280 code"
ampy --port /dev/ttyUSB0 put bme280.mpy
echo "Uploading boot.py"
ampy --port /dev/ttyUSB0 put boot.py
echo "Uploading main.py"
ampy --port /dev/ttyUSB0 put main.py
echo "Resetting again..."
ampy --port /dev/ttyUSB0 reset
