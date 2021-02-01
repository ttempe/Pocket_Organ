#board.py

#This file centralizes the pin allocation configuration in one location, and does pin initialization when needed

#TODO
# * Create and mount a filesystem 

from machine import Pin, SPI

#This is the version number of the board.
#Starting with version 16, all version-specific software (eg: choice of driver) should refer to this variable
#to remain backward compatible.
#Older board versions are not assumed to be feature-complete, but should keep working with at least
#the same level of functionality.
version = 16

spi = SPI(1)

backlight_oe_pin =   Pin("B3", Pin.OUT)
backlight_data_pin = Pin("B9",  Pin.OUT)
backlight_clk_pin =  Pin("C0", Pin.OUT)

display_spi = spi
display_dc =  Pin("C0", Pin.OUT)
display_res = Pin("C9", Pin.OUT)
display_cs =  Pin("A8", Pin.OUT)
display_cs(1)

#for W25Q128 flash
flash_spi = spi
flash_cs  = Pin("B12", Pin.OUT)
flash_cs(1)
flash_fs_size = 256 #Measured in blocks of 4kB. 256=1MB

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

main_startup_pin = keyboard_volume_pin

#Pin("B12", Pin.OUT).value(1)

#End