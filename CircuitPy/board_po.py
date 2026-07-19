#This file centralizes all the hardware-related configuration (incl. the pin allocation and calibration) in one location, and does pin initialization when needed
import board, digitalio, analogio, busio, neopixel, adafruit_midi, usb_midi
from version import version
#Hardware versions start at 31

#TODO:
# * If no version.py file, exit gracefully with an error message displayed on the OLED screen
# * address bits A and C are swapped. Correct them, and correct the keyb_map as well to make all the keys work the same

verbose = False

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
disp_CLK  = board.GP10 if version>=31 else board.GP6
disp_MOSI = board.GP11 if version>=31 else board.GP7
disp_DC   = board.GP9  if version>=31 else board.GP5
disp_CS   = board.GP8  if version>=31 else board.GP4 if version>=25 else board.GP3
disp_RST  = board.GP12 if version>=31 else board.GP20 if 25==version else board.GP8
#MIDI out. Select between UART (on-board synth) and USB MIDI
midi = [ adafruit_midi.MIDI(midi_out=usb_midi.ports[1]),
         adafruit_midi.MIDI(midi_out=busio.UART(tx=board.GP16, baudrate=31250), debug=False)
         ]

# Backlight
# pixel sequence: [6, 7, 5, 4, 2, 1, 0, 3, 10, 9, 8, 11, 12, 13]
# index            0  1  2  3  4  5  6  7   8  9 10  11  12  13
backlight_map = [6, 5, 4, 7, 3, 2, 0, 1, 10, 9, 8, 11, 12, 13] 
backlight = neopixel.NeoPixel(board.GP0, len(backlight_map), brightness=.25, auto_write=False)

# Key indices (keyboard bitmap) and backlight hint masks
KEY_THIRD = 8
KEY_FIFTH = 9
KEY_SEVENTH = 10
KEY_SHIFT = 11
KEY_SHARP = 12
KEY_MINOR = 13
KEY_NOTE_MASK = 0xFF
LOOP_SLOTS = 0x3F  # note keys 0-5 used for looper

#Buttons
power_off = pinOut(board.GP13, value=False) #Set to high to turn off
force_on  = pinOut(board.GP14, value=False) #Set to high to keep the user from turning off the instrument
key_vol   = pinIn(board.GP18, pull=digitalio.Pull.UP)
key_loop  = pinIn(board.GP19, pull=digitalio.Pull.UP)
key_instr = pinIn(board.GP20, pull=digitalio.Pull.UP)
key_capo  = pinIn(board.GP21, pull=digitalio.Pull.UP)

# Strum comb — Holtek BS8112A-3 (V32+: SCL=GP7, SDA=GP6). Older boards: no I2C.
if version >= 32:
    strum_i2c = busio.I2C(scl=board.GP7, sda=board.GP6)
else:
    strum_i2c = None
STRUM_I2C_ADDR = 0x50  # Holtek default (0xA0/0xA1 with R/W)
STRUM_N_KEYS = 12
# Musical low->high pad order as BS8112A Key numbers (1..12). Slot 0 = lowest note = Key10.
STRUM_KEY_MAP = (10, 9, 8, 7, 6, 5, 4, 3, 11, 12, 1, 2)

#Analog keys keyboard (also provides battery and USB voltage readings)
keyb_muxA = pinOut(board.GP1)
keyb_muxB = pinOut(board.GP2)
keyb_muxC = pinOut(board.GP3)
keyb_ADC = [analogio.AnalogIn(board.A0),
            analogio.AnalogIn(board.A1)]
# Hall sensor supply: GP4 high = off, low = on (V31+ only; GP4 is display CS on older boards)
keyb_vbus = pinOut(board.GP4, value=True) #Power supply for the hall sensors
vbat_addr = 9
vusb_addr = 13

#Anolog key addresses
#keyb_map = [ 5,  9,  1, 13,  4,  8,  0,  12,   2,    15,  11,      6,  14,  10,   3,  7]
keyb_map = [ 5,  3,  1,  7,  4,  2,  0,   6,   8,    15,  11,     12,  14, 10,   9,      13] # address of each key
key_names =["C","D","E","F","G","A","B","CC","SUS","Aug","7th","Shift","#","m","vBat", "vUSB"]
#Index       0,  1,  2,  3,  4,  5,  6,   7,   8,    9,   10,     11,  12, 13,  14,      15 
key_up   = 10
key_down = 13

#Analog keys calibration, obtained with calibrate() in keyboard.py
keyb_range=[10701, 6865, 7111, 8464, 11984, 8133, 8056, 9194, 11700, 1, 6288, 6473, 8403, 147, 9041, 11070]; keyb_min=[11985, 10388, 11574, 11325, 13791, 9424, 10333, 9747, 15483, 6314, 9892, 9892, 12139, 909, 11596, 11424] #V32-A
#keyb_range=[8533, 11101, 6973, 10148, 8379, 7749, 9178, 9209, 13845, 1, 6650, 6496, 9801, 16, 8079, 11016]; keyb_min=[10743, 11616, 10599, 11937, 10209, 9583, 10570, 10315, 16538, 6786, 10458, 9972, 10507, 288, 10725, 12413] #V31-1
#keyb_range=[10291, 10674, 14523, 24, 8730, 7090, 17060, 32, 7786, 8434, 7754, 9563, 8034, 7658, 8818, 8858]; keyb_min=[10946, 9290, 12459, 6890, 9618, 10290, 13835, 488, 9346, 8626, 8866, 11026, 9394, 9602, 10234, 9282] #V31-2

#End
