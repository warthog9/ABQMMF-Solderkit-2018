import machine
from machine import Pin, Signal, Timer
import bme280
import ssd1306

import time
import math

#import sys

# btree seems to be broken
# as it seems to stomp all over the
# fat filesystem internally
# after being modified quickly
## import btree

#
# These are needed for switching the 
# VCC read pin to the internal 
# - it's complicated
# 

import esp
from flashbdev import bdev

# End imports for vcc read flipping

pin_scl=14
pin_sda=4

pin_led_board=0

pin_led_node=16
pin_led_esp12=2

button_pin_up=13
button_pin_right=10
button_pin_down=5
button_pin_left=9
button_pin_middle=12


_pin_led_board = Pin(pin_led_board, machine.Pin.OUT)
_pin_led_node  = Pin(pin_led_node, machine.Pin.OUT)
_pin_led_esp12 = Pin(pin_led_esp12, machine.Pin.OUT)

led_board = Signal(_pin_led_board, invert=True)
led_node  = Signal(_pin_led_node, invert=True)
led_esp12 = Signal(_pin_led_esp12, invert=True)

leds = [ led_board, led_node, led_esp12 ]

pin_button_up     = machine.Pin( button_pin_up,     machine.Pin.IN, machine.Pin.PULL_UP )
pin_button_right  = machine.Pin( button_pin_right,  machine.Pin.IN, machine.Pin.PULL_UP )
pin_button_down   = machine.Pin( button_pin_down,   machine.Pin.IN, machine.Pin.PULL_UP )
pin_button_left   = machine.Pin( button_pin_left,   machine.Pin.IN, machine.Pin.PULL_UP )
pin_button_middle = machine.Pin( button_pin_middle, machine.Pin.IN, machine.Pin.PULL_UP )

buttons = [ pin_button_up, pin_button_right, pin_button_down, pin_button_left, pin_button_middle ]

#####################
# Real Code goes after here
#####################

#####################
# VCC flipping information
#####################
ADC_MODE_VCC = 255
ADC_MODE_ADC = 0

SCREEN_BRIGHTNESS = 100

def set_adc_mode(mode):
    sector_size = bdev.SEC_SIZE
    flash_size = esp.flash_size() # device dependent
    init_sector = int(flash_size / sector_size - 4)
    data = bytearray(esp.flash_read(init_sector * sector_size, sector_size))
    if data[107] == mode:
        return  # flash is already correct; nothing to do
    else:
        print( "*** Going to adjust the ADC type in the flashed memory" );
        print( "*** You will need to hit the 'RST' button, near the USB port" );
        print( "*** when it's done" );
        data[107] = mode  # re-write flash
        esp.flash_erase(init_sector)
        esp.flash_write(init_sector * sector_size, data)
        print("*** ADC mode changed in flash; restart to use it!")
        return

set_adc_mode( ADC_MODE_VCC )

#####################
# End of VCC Flipping code
#####################

#####################
# Instantiate the rest of the things we'll need
#####################

# This sets up what pins on the system are going
# to be I2C.  MicroPython does a 'soft' I2C for
# any pins (I.E. it's bit banging the I2C via gpio)
# and we need to tell MicroPython which pins to do this on
print( "Initialize the I2C pins...", end="")
##try:
i2c = machine.I2C(scl=machine.Pin(pin_scl), sda=machine.Pin(pin_sda) )
##except:
##    print( " FAILED")
##    print( "This is a fatal error - something is very wonky")
##    sys.exit()
print( " Success")

# this sets up the temp/humidity/pressure sensor
print( "Initialize the BME280 using I2C...", end="")
##try:
bme = bme280.BME280(i2c=i2c)
##except:
##    print( " FAILED")
##    print( "This is a fatal error - something is very wonky")
##    sys.exit()
print( " Success")

# this sets up the oled screen
print( "Initialize the OLED screen using I2C...", end="")
##try:
oled = ssd1306.SSD1306_I2C( 128, 32, i2c)
##except:
##    print( " FAILED")
##    print( "This is a fatal error - something is very wonky")
##    sys.exit()
print( " Success")


# This setups the reading of the VCC state
# this boils down to the voltage on the system
# which can be equated to how much battery is
# left
print( "Initialize the ADC as VCC...", end="")
##try:
vcc_stat = machine.ADC(1)
##except:
##    print( " FAILED")
##    print( "This is a fatal error - something is very wonky")
##    sys.exit()
print( " Success")


#####################
# End instantiation
#####################

#####################
# Lets run through some basic diagnostics quick, clearing the screen, blinking some LEDs, etc
#####################

# First turn off the LEDs, and clear the screen
print( "Turning off all the LEDs...", end='')
for led in leds:
    print(".", end='')
    led.off()
print( "!" )

print( "Clearing the OLED screen...", end='')
oled.fill(0)
oled.show()
print( " Success")

# Ok lets put something on the LEDs, show some 'life'
for led in leds:
    print( "Toggling LED:")
    for x in range( 0, 3 ):
        if( not led.value() ):
            print( "        On")
            led.on()
        else:
            print( "        Off")
            led.off()
        time.sleep( 0.5 )
    print( "        Final - Off")
    led.off()


#####################
# End Startup testing code
#####################


#####################
# Lets just setup the LED that's on the board as a PWM, we may 'breath' it later
#####################
breath_i = 0

def breath( x ):
    global pwmLed
    global breath_i

    breath_i = breath_i + 1

    #newduty = int(math.sin(breath_i / 10 * math.pi) * 500 + 500)
    #newduty = int(math.sin(breath_i / 200 * math.pi) * 375 + 375)
    #newduty = int( (math.sin(breath_i * math.pi * 1.5) / 2) * 250 + 250 )
    newduty = 1024 - int( (math.exp(math.sin(breath_i/20.0 * math.pi)) - 0.36787944) * 108.0 );

    if( newduty >= 1010 ):
        return

    pwmLed.duty( newduty )
    ##print( "breath_i:", end='')
    ##print( str(breath_i) )
    ##print( "Duty:", end='')
    ##print( str(newduty) )

print( "Initialize the Board LED as a PWM...", end="")
##try:
pwmLed = machine.PWM(_pin_led_board)
pwmLed.freq(1000)
pwmLed.duty(1024)

breathTimer = Timer(-1)
breathTimer.init(period=100, mode=Timer.PERIODIC, callback=breath)
##except:
##    print( " FAILED")
##    print( "This is a fatal error - something is very wonky")
##    sys.exit()
print( " Success")

#####################
# Read in config data
#####################

##database_filename = "config.db"

### open the database:
##try:
##    f = open(database_filename, "r+b")
##except OSError:
##    f = open(database_filename, "w+b")
##
##db = btree.open(f)
##
###defaults
##if( not db.get("brightness") ):
##    db[b"brightness"]= b"100"
##    #db.flush()
##
##if( not db.get("temp_mode") ):
##    db[b"temp_mode"] = b"F"
##    #db.flush()

#
# Classes, mostly for ISR, go here
#

#
# Function definitions
#

def draw_battery():
    max_bat = 3300 #3.3V * 1000
    bat_dead = 1200 # about 1.2V
    # note we have 14 steps in this battery meter
    # 16 pixels wide, 2 pixels for the edges = 14
    bat_steps = 13
    
    bat_lost = max_bat - vcc_stat.read()

    bat_per_lost = round(bat_lost / ((max_bat - bat_dead) / bat_steps))

    oled.fill_rect(112,0,16,6,1)
    oled.fill_rect(110,2,3,2,1)
    oled.fill_rect(113,1,bat_per_lost,4,0)


def set_contrast( x ):
    global SCREEN_BRIGHTNESS

    oled.contrast( x )
    SCREEN_BRIGHTNESS = x


##    brightness = db[b"brightness"]
##    db[b"brightness"] = bytes(str(x), "ascii")
    
def cb_adjustBrightnessUp( pin ):
##    bright = int(db[b"brightness"])
    bright = SCREEN_BRIGHTNESS

    if(
        bright >= 255
    ):
        return

    bright = bright + 25

    if( bright >= 255 ):
        bright = 255

    set_contrast( bright )
    #print( "cb_adjustBrightnessUp "+ str( bright ) +"|"+ str( SCREEN_BRIGHTNESS ) )

def cb_adjustBrightnessDown( pin ):
##    bright = int(db[b"brightness"])
    bright = SCREEN_BRIGHTNESS

    if(
        bright <= 0
    ):
        return

    bright = bright - 25

    if( bright <= 0 ):
        bright = 0

    set_contrast( bright )

    #print( "cb_adjustBrightnessDown "+ str( bright ) +"|"+ str( SCREEN_BRIGHTNESS ) )

USE_F = 1

def cb_switchCF( pin ):
    global USE_F

    USE_F = not USE_F

    #if( USE_F ):
    #    USE_F = 0
    #else:
    #    USE_F = 1

USE_TXT = 0

def cb_switchText( pin ):
    global USE_TXT

    USE_TXT = not USE_TXT

    #if( USE_TXT ):
    #    USE_TXT = 0
    #else:
    #    USE_TXT = 1

def cb_LEDTOG( pin ):
    ##print( "LED TOG: "+ str(led_esp12.value()) +" | "+ str(led_esp12.value()) )
    if( not led_esp12.value() and not led_node.value() ):
        led_esp12.on()
        return

    if( led_esp12.value() and not led_node.value() ):
        led_node.on()
        return

    if( led_esp12.value() and led_node.value()):
        led_esp12.off()
        return

    if( not led_esp12.value() and led_node.value()):
        led_node.off()
        return


pin_button_up.irq( trigger=machine.Pin.IRQ_FALLING, handler=cb_adjustBrightnessUp)
pin_button_down.irq( trigger=machine.Pin.IRQ_FALLING, handler=cb_adjustBrightnessDown)
pin_button_middle.irq( trigger=machine.Pin.IRQ_FALLING, handler=cb_switchCF)
pin_button_left.irq( trigger=machine.Pin.IRQ_FALLING, handler=cb_switchText)
pin_button_right.irq( trigger=machine.Pin.IRQ_FALLING, handler=cb_LEDTOG)

while( True ):
    bme_data = bme.read_compensated_data()
    tTemp = bme_data[0]
    del bme_data

    tPress = bme.values[1]
    tHum = bme.values[2]

    if vcc_stat.read() == 65535:
        # So vcc_stat.read() will read wonky data till
        # the system is rebooted and the ADC line is
        # switched to the 'right' way to read the battery
        #
        # where 'right' is defined as what we want
        # it to do, and without external resistors 
##        oled.text( "Please Press the", 0, 0, 100)
##        oled.text( "'RST' button", 0, 10, 100)
##        oled.text( "below usb", 0, 20, 100) 
##        oled.show()
        # break out of the loop entirely, this
        # will drop the board to a REPL prompt
        break

    fTemp = "{}F".format( 9.0/5.0 * (tTemp // 100) + 32)
    #cTemp = "{}C".format(tTemp / 100) 

    if( USE_F ):
        tTemp = fTemp
    else:
        #tTemp = cTemp
        tTemp = bme.values[0]

    if( USE_TXT ):
        exTemp = "emp"
        exPress = "ress"
        exHum = "um"
    else:
        exTemp = ""
        exPress = ""
        exHum = ""

    oled.fill(0)
    oled.text( 'T'+ exTemp +':'+ tTemp, 0, 0, 100)
    oled.text( 'P'+ exPress +':'+ str(tPress), 0, 10, 100)
    oled.text( 'H'+ exHum +':'+ str(tHum), 0, 20, 100)

    ##oled.text( "{0:.2f}".format(vcc_stat.read() / 1000) , 90, 20, 100)
    draw_battery()

    oled.show()

    ##db.flush()

    #print( "breath_i: ", end='')
    #print( str(breath_i) )
    #print( "PWM Duty:"+ str(pwmLed.duty()) ) 

    print( "To break hit <ctrl>+c then enter: breathTimer.deinit()" )
    time.sleep(1)
