# Micropython driver for the AT42QT110 touch sensor IC from Atmel
# Copyright 2020, Thomas TEMPE
# DWTFYL license.

#Supports SPI clock of up to 1.5 MHz
#Clock idle high (Clock polarity=1, clock phase=1)
#Need to wait min 150us, max 100ms between two byte exchanges
#MOSI: reading data on the falling edge of each clock pulse
#MISO: writing data on the rising edge

import errno
import time

class AT42QT110:
    def __init__(self, spi, cs_pin):
        "chip is connected thourgh SPI; expecting a machine.SPI object (for the bus) and a machine.pin object (for the CS pin)"
        self.spi = spi
        self.cs = cs_pin
        self.cs(1)
        self.rate = 1500000
        self.buf = bytearray(3)
        self.buttons=0
        #IC Initialization
        self.send_command(b"\x90\xF0")#Auto trigger, 11-key, parallel acquisition, edge sync, free run
        
    def send_command(self, cmd, read=0):
        "Send a single SPI command. Optionally write data specified in 'write'. Optionally read and return 'read' bytes."
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        r = None
        self.cs(0)
        if read:
            r = self.spi.read(read)
        self.cs(1)
        return r
    
    def self_test(self):
        r = self.send_command(b"\xc9", read=1)
        if r[1] == 0x57:
            print(self, "Self-test OK")
        else:
            print(self, "self-test failed: returned", self.buf) 

    def read_analog(self, key):
        r = self.send_command(bytes([0x20+key&0x0F]), read=2)
        print(r)
        
    def read_threshold(self, key):
        r = self.send_command(bytes([0x40+(key&0x0F)]), read=2)
        print(r)

    def read(self):
        r = self.send_command("\xc1", read=2)
        self.buttons = (r[0]<<8)+r[1]
        print(self.buttons)
    
    def button(self, b):
        "Return the status of button n. b"
        return (self.buttons>>b)&1
        
    def recalibrate_all_keys(self):
        self.send_command(b"\x03")
        #time.sleep_ms(160)#after reset
        time.sleep_us(150)#after a full recalibration

#Debug. TODO: Remove
from machine import SPI, Pin
a = AT42QT110(SPI(1), Pin("B8", Pin.OUT))
#End