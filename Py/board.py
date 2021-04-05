#board.py

#This file centralizes the pin allocation configuration in one location, and does pin initialization when needed

from machine import Pin, SPI

#This is the version number of the board.
#Starting with version 16, all version-specific software (eg: choice of driver) should refer to this variable
#to remain backward compatible.
#Older board versions are not assumed to be feature-complete, but should keep working with at least
#the same level of functionality.
version = 17

spi = SPI(1)

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
    flash_fs_size = 0 #Measured in blocks of 4kB. 256=1MB

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

elif 17 == version:
    backlight_oe_pin   = Pin("C14", Pin.OUT)
    backlight_oe_pin(1)
    backlight_data_pin = Pin("C13",  Pin.OUT)
    backlight_clk_pin  = Pin("C15", Pin.OUT)
    backlight_leds     = bytearray([0, 1, 2, 4, 3, 6, 7, 5])#Order of the LEDs

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
    keyboard_note_keys  = bytearray([6, 7, 8, 0, 9, 3, 1, 2]) #Order of the note key pads from Do to Ut. All must be on the same UC.
    keyboard_sharp      = 4 #on UC1
    keyboard_uc2_seventh= 6 #on UC2
    keyboard_uc2_fifth  = 7 #on UC2
    keyboard_uc2_third  = 8 #on UC2
    keyboard_uc2_minor  = 0 #on UC2
    keyboard_uc2_shift  = 1 #on UC2
    keyboard_strum_mute = 6 #on UC3
    keyboard_strum_keys = bytearray([5,4,3,2,1,0,10,9,8,7]) #on UC3
    keyboard_notes_thres= bytearray([10,10,12,4,7,7,4,9]) #above this value, assume the key is pressed
    keyboard_notes_max  = bytearray([60,40,50,48,43,40,55,48])#highest possible analog value, minus the threshold

main_startup_pin = keyboard_volume_pin


#End