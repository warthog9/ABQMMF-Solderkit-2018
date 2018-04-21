all: mpy_bme280_esp8266/bme280.py bme280.mpy

mpy_bme280_esp8266/bme280.py:
	git init submodule

bme280.mpy:
	mpy-cross bme280.py
