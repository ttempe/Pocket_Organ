#This file centralizes all the hardware-related configuration (incl. the pin allocation and calibration) in one location, and does pin initialization when needed
import board, digitalio, analogio, busio, neopixel, adafruit_midi, usb_midi
from version import version
#Hardware versions start at 24 for the CircuitPython codebase.

#TODO: If no version.py file, exit gracefully with an error message displayed on the OLED screen

verbose = True

#Helper functions
def pinOut(p, value=None):
    ret = digitalio.DigitalInOut(p)
    ret.direction = digitalio.Direction.OUTPUT
    if value != None: ret.value = value
    return ret

def pinIn(p, pull=None):
    ret = digitalio.DigitalInOut(p)
    if pull != None: ret.pull = pull
    return ret

#OLED Display on SPI bus
disp_CLK  = board.GP6
disp_MOSI = board.GP7
disp_DC   = board.GP5
disp_CS   = board.GP4 if version>=25 else board.GP3
disp_RST  = board.GP20 if 25==version else board.GP8
#MIDI out. Select between UART (on-board synth) and USB MIDI
midi = [ adafruit_midi.MIDI(midi_out=usb_midi.ports[1]),
         adafruit_midi.MIDI(midi_out=busio.UART(tx=board.GP16, baudrate=31250), debug=False)
         ]

#Backlight
backlight_map = [6, 5, 4, 7, 3, 2, 0, 1, 10, 9, 8, 11, 12, 13, 14, 15, 16, 17, 18]#All note keys in order, then all left-hand analog keys in reading order.
backlight = neopixel.NeoPixel(board.GP0 if version>=25 else board.GP8, len(backlight_map), brightness=.25)#, auto_write=False) #Actually V24 doesn't have backlight. Using a dummy port

#Buttons
power_off = pinOut(board.GP10)#, value=True)
key_power = digitalio.DigitalInOut(board.GP11)
key_vol   = pinIn(board.GP12, pull=digitalio.Pull.UP)
key_loop  = pinIn(board.GP13, pull=digitalio.Pull.UP)
key_instr = pinIn(board.GP14, pull=digitalio.Pull.UP)
key_capo  = pinIn(board.GP15, pull=digitalio.Pull.UP)
#vbat_ADC
#vusb_ADC

#Analog keys keyboard
keyb_muxA = pinOut(board.GP1 if version>=25 else board.GP0)
keyb_muxB = pinOut(board.GP2 if version>=25 else board.GP1)
keyb_muxC = pinOut(board.GP3 if version>=25 else board.GP2)
keyb_ADC = [analogio.AnalogIn(board.A0),
            analogio.AnalogIn(board.A1)]

keyb_map = [5, 9, 1, 13, 4, 8, 0, 12, 2, 15, 11, 6, 14, 10, 3, 7]
#Index      0, 1, 2,  3, 4, 5, 6,  7, 8,  9, 10,11, 12, 13,14,15

#Analog keys calibration, obtained with calibrate() in keyboard.py
if 24 == version:
    keyb_min= [22469, 23077, 23189, 1504, 26342, 24998, 23365, 51692, 24565, 24582, 21141, 23845, 22629, 21541, 22149, 22197] ;keyb_max= [5259, 4895, 4625, 53, 3613, 4354, 5393, 566, 4005, 4408, 5392, 4652, 5028, 6148, 5109, 4921]
elif 25 == version:
    keyb_min= [9442, 8177, 8177, 1072, 18580, 10930, 13059, 19028, 8930, 7761, 9314, 14739, 16291, 9298, 7841, 13507] ;keyb_max= [13121, 11957, 9451, 103, 6177, 12237, 9863, 456, 11721, 8714, 11676, 11190, 9009, 12310, 10143, 9022]
elif 26 == version:
   #keyb_min= [10274,#14787, 18196, 10322, 6273, 21861, 17492, 19220, 14419, 20388, 20068, 13107, 10802, 16404, 10050, 12899] ;keyb_max= [13018, 11853, 6973, 339, 16483, 5056, 6708, 442, 10188, 7150, 4600, 11898, 12960, 9907, 13327, 11028]
    keyb_min= [10274, 14787, 18196, 10322, 6273, 21861, 17492, 19220, 14419, 20388, 20068, 13107, 10802, 16404, 10050, 12899] ;keyb_max= [13018, 11853, 6600, 339, 16483, 5056, 6708, 442, 10188, 7150, 4600, 11898, 12960, 9907, 13327, 11028]
    
keyboard_strum_keys = bytearray([0])#for compatibility. TODO: remove.

#End
