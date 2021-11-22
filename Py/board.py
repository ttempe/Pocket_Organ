#board.py

#This file centralizes the pin allocation configuration in one location, and does pin initialization when needed

from machine import Pin, SPI, ADC, UART
import version as ver

#This is the version number of the board.
#Starting with version 18, all version-specific software (eg: choice of driver) should refer to this variable
#to remain backward compatible.
#Older board versions are not assumed to be feature-complete, but should keep working with at least
#the same level of functionality.

#TODO: If no version.py file, exit gracefully with an error message displayed on the OLED screen

version = ver.version
verbose = True #display debug info on top of the screen. Display events info on the console.

spi = SPI(1)
midi_UART = UART(3, 31250)

backlight_oe_pin   = Pin("C14", Pin.OUT)
backlight_oe_pin(1)
backlight_data_pin = Pin("C13",  Pin.OUT)
backlight_clk_pin  = Pin("C15", Pin.OUT)
backlight_leds     = bytearray([0, 1, 2, 4, 3, 7, 5, 6])#Order of the LEDs

display_spi = spi
display_dc =  Pin("B13", Pin.OUT)
display_res = Pin("B14", Pin.OUT)
display_cs =  Pin("B15", Pin.OUT)
display_cs(1)

#for W25Q128 flash
flash_spi = spi
flash_cs  = Pin("C4", Pin.OUT)
flash_cs(1)
flash_fs_size = 0 #Measured in blocks of 4kB. 256=1MB

#for AT42QT1110 version
keyboard_spi =    spi
keyboard_uc1_cs = Pin("B8", Pin.OUT)
keyboard_uc2_cs = Pin("A0", Pin.OUT)
keyboard_uc3_cs = Pin("B9", Pin.OUT)
keyboard_trigger= Pin("B5", Pin.OUT)
keyboard_uc1_cs(1)
keyboard_uc2_cs(1)
keyboard_uc3_cs(1)
keyboard_melody_led = Pin("C3", Pin.OUT)
keyboard_instr_pin  = Pin("A4", Pin.IN, Pin.PULL_UP)
keyboard_looper_pin = Pin("A1", Pin.IN, Pin.PULL_UP)
keyboard_drum_pin   = Pin("A2", Pin.IN, Pin.PULL_UP)
keyboard_uc2_seventh= 6 #on UC2
keyboard_note_keys  = bytearray([6, 7, 8, 0, 9, 2, 3, 1]) #Order of the note key pads from Do to Ut. All must be on the same UC.
keyboard_uc2_fifth  = 8 #on UC2
keyboard_uc2_third  = 7 #on UC2

keyboard_uc2_minor  = 0 #on UC2
keyboard_uc2_shift  = 1 #on UC2
keyboard_slider_keys= [2,3,4,5] #on UC2
keyboard_strum_keys = bytearray([5,4,3,2,1,0,10,9,8,7, 6]) #on UC3
keyboard_slider_cal = [22,30,11,25]
if 18 == version:
    keyboard_notes_max  = bytearray([35,30,20,41,28,29,12,28]) #highest possible analog value (after substraction from the reference)
else:
    keyboard_notes_max  = bytearray([40,27,32,42,25,29,27,33]) #highest possible analog value (after substraction from the reference)
                                                           #To calibrate, apply the crosstalk matrix first (and press each key individually) 
if 19 >= version:
    keyboard_crosstalk = [ #when I put my finger on key n. <line>, this is the % of parasitic response I can read on each of the keys.
                           #To calibrate, uncomment the print() line in keyboard_AT42T1110.py, in keyboard.read_analog_keys()
                            [0,.05,.05,.05,  0,  0,  0,  0], #Do
                            [0,  0, .3,  0, .1,  0,  0,  0], #Re
                            [0,.05,  0,  0,  0, .1,.05,  0], #Mi
                            [0,  0,  0,  0,  0,  0,  0,.15], #Fa
                            [0,  0,  0,  0,  0, .1,  0,.25], #Sol
                            [0,  0,  0,  0,  0,  0, .4,  0],#La
                            [0,  0,  0,  0,  0, .2,  0,  0],#Si
                            [0,  0,  0,.05,  0,  0,  0,  0] #Ut
                            ]
elif 18==version:
    keyboard_crosstalk = [ #when I put my finger on key n. <line>, this is the % of parasitic response I can read on each of the keys.
                           #To calibrate, uncomment the print() line in keyboard_AT42T1110.py, in keyboard.read_analog_keys()
                            [0,.2,.05,.1,.05, 0, 0, 0], #Do
                            [0.05,0,.5, 0,.1, 0, 0, 0], #Re
                            [0]*8,                   #Mi
                            [0, 0, 0, 0, 0, 0, 0,.1],#Fa
                            [0, 0, 0, 0, 0,.1, 0,.1],#Sol
                            [0, 0, 0, 0, 0, 0,.5, 0],#La
                            [0, 0, 0, 0, 0,.2, 0, 0],#Si
                            [0, 0, 0, 0, 0,.3,.3, 0] #Ut
                            ]
else:
    keyboard_crosstalk = None
                        
midi_rst = Pin("C10", Pin.OUT, value=0)

vbat_ADC = ADC(Pin("B1"))
vusb_ADC = ADC(Pin("B0"))
vbat = lambda : vbat_ADC.read_u16()/65536*3.3*2
vusb = lambda : vusb_ADC.read_u16()/65536*3.3*2

main_startup_pin = keyboard_instr_pin

#End