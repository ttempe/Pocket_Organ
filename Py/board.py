#board.py

#This file centralizes the pin allocation configuration in one location, and does pin initialization when needed

from machine import Pin, SPI, ADC, UART

#This is the version number of the board.
#Starting with version 16, all version-specific software (eg: choice of driver) should refer to this variable
#to remain backward compatible.
#Older board versions are not assumed to be feature-complete, but should keep working with at least
#the same level of functionality.
version = 18
verbose = True #display debug info on top of the screen. Display events info on the console.

spi = SPI(1)
midi_UART = UART(3, 31250)

if 16 == version:
    backlight_oe_pin   = Pin("B3", Pin.OUT)
    backlight_data_pin = Pin("B9",  Pin.OUT)
    backlight_clk_pin  = Pin("C0", Pin.OUT)
    backlight_leds     = bytearray([1, 2, 0, 3, 4, 5, 6, 7])

    display_spi = spi
    display_dc =  Pin("C0", Pin.OUT)
    display_res = Pin("C9", Pin.OUT)
    display_cs =  Pin("A8", Pin.OUT)
    display_cs(1)

    #for W25Q128 flash
    flash_spi = spi
    flash_cs  = Pin("B12", Pin.OUT)
    flash_cs(1)

    #for AT42QT1110 version
    keyboard_spi =    spi
    keyboard_uc1_cs = Pin("B8", Pin.OUT)
    keyboard_uc2_cs = Pin("C5", Pin.OUT)
    keyboard_uc3_cs = Pin("C3", Pin.OUT)
    keyboard_trigger= Pin("B4", Pin.OUT)
    keyboard_uc1_cs(1)
    keyboard_uc2_cs(1)
    keyboard_uc3_cs(1)
    keyboard_melody_led = Pin("A0", Pin.OUT)
    keyboard_volume_pin = Pin("B0", Pin.IN, Pin.PULL_UP)
    keyboard_instr_pin  = Pin("C4", Pin.IN, Pin.PULL_UP)
    keyboard_looper_pin = Pin("A4", Pin.IN, Pin.PULL_UP)
    keyboard_drum_pin   = Pin("A3", Pin.IN, Pin.PULL_UP)
    keyboard_note_keys  = bytearray([7,6,8,1,0,9,4,3]) #Order of the note key pads from Do to Ut. All must be on the same UC.
    keyboard_sharp      = 6 #on UC1
    keyboard_uc2_seventh= 6 #on UC2
    keyboard_uc2_fifth  = 7 #on UC2
    keyboard_uc2_third  = 8 #on UC2
    keyboard_uc2_minor  = 0 #on UC2
    keyboard_uc2_shift  = 1 #on UC2
    keyboard_strum_mute = 5 #on UC3
    keyboard_strum_keys = bytearray([9, 8, 7, 6, 4, 3, 1, 2]) #on UC3
    keyboard_notes_thres= bytearray([9]*8) #above this value, assume the key is pressed
    keyboard_notes_max  = bytearray([40]*8)#highest possible analog value
    keyboard_slider_keys= [2,3,4,5] #on UC2
    keyboard_slider_cal = [24,23,8,24]
    keyboard_crosstalk  = None
    vbat = lambda : 4.2
    vusb = lambda : 5.0
    midi_rst = Pin("A15", Pin.OUT)

elif version >= 17:
    backlight_oe_pin   = Pin("C14", Pin.OUT)
    backlight_oe_pin(1)
    backlight_data_pin = Pin("C13",  Pin.OUT)
    backlight_clk_pin  = Pin("C15", Pin.OUT)
    if 17 == version: 
        backlight_leds     = bytearray([0, 1, 2, 4, 3, 6, 7, 5])#Order of the LEDs
    else:
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
    keyboard_volume_pin = Pin("A3", Pin.IN, Pin.PULL_UP)
    keyboard_instr_pin  = Pin("A4", Pin.IN, Pin.PULL_UP)
    keyboard_looper_pin = Pin("A1", Pin.IN, Pin.PULL_UP)
    keyboard_drum_pin   = Pin("A2", Pin.IN, Pin.PULL_UP)
    keyboard_sharp      = 4 #on UC1
    keyboard_uc2_seventh= 6 #on UC2
    if 17 == version:
        keyboard_note_keys  = bytearray([6, 7, 8, 0, 9, 3, 1, 2]) #Order of the note key pads from Do to Ut. All must be on the same UC.
        keyboard_uc2_fifth  = 7 #on UC2
        keyboard_uc2_third  = 8 #on UC2
    else:
        keyboard_note_keys  = bytearray([6, 7, 8, 0, 9, 2, 3, 1]) #Order of the note key pads from Do to Ut. All must be on the same UC.
        keyboard_uc2_fifth  = 8 #on UC2
        keyboard_uc2_third  = 7 #on UC2

    keyboard_uc2_minor  = 0 #on UC2
    keyboard_uc2_shift  = 1 #on UC2
    if 17 == version:
        keyboard_strum_keys = bytearray([5,4,3,2,1,0,10,9,8,7]) #on UC3
        keyboard_strum_mute = 6 #on UC3
    else:
        keyboard_strum_keys = bytearray([5,4,3,2,1,0,10,9,8,7, 6]) #on UC3
        keyboard_strum_mute = None #on UC3
    keyboard_notes_max  = bytearray([35,30,20,41,28,29,12,28]) #highest possible analog value (after substraction from the reference)
                                                               #To calibrate, apply the crosstalk matrix first (and press each key individually) 
    keyboard_slider_keys= [2,3,4,5] #on UC2
    keyboard_slider_cal = [33,35,11,20]
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
                            
    midi_rst = Pin("C10", Pin.OUT, value=0)
    
    vbat_ADC = ADC(Pin("B1"))
    vusb_ADC = ADC(Pin("B0"))
    vbat = lambda : vbat_ADC.read_u16()/65536*3.3*2
    vusb = lambda : vbat_ADC.read_u16()/65536*3.3*2

main_startup_pin = keyboard_volume_pin


#End