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

class AT42QT1110:
    def __init__(self, spi, cs_pin):
        "chip is connected thourgh SPI; expecting a machine.SPI object (for the bus) and a machine.pin object (for the CS pin)"
        self.spi = spi
        self.cs = cs_pin
        self.cs(1)
        self.rate = 1500000
        self.buttons=0
        #IC Initialization
        for i in [
            b"\x90\xE0", #Auto trigger, 11-key, parallel acquisition, edge sync, free run
            b"\x92\x18", #Don't wait 3 cycles to report a detection. Faster, but noisier.
            b"\x97\x00", b"\x98\x00",  #Disable AKS. Allow multiple keys to be detected simultaneously
            b"\xAF\xF0", b"\xB0\xF0", b"\xB1\xF0", b"\xB2\xF0", b"\xB3\xF0", b"\xB4\xF0",
            b"\xB5\xF0", b"\xB6\xF0", b"\xB7\xF0", b"\xB8\xF0", b"\xB9\xF0" #Turn off negative drift compensation
            ]:
            self.send_command(i)


    def send_command2(self, cmd, read=0):
        "Send a single SPI command. Optionally write data specified in 'write'. Optionally read and return 'read' bytes."
        self.spi.init(baudrate=self.rate, polarity=1, phase=1)
        r = bytearray(read+len(cmd))
        b = bytearray(1)
        i = 0
        self.cs(0)
        for v in cmd:
            b[0]= v
            self.spi.write_readinto(b, b)
            r[i]=b[0]
            i+=1
            time.sleep_us(150)
        while read:
            r[i]=self.spi.read(1)[0]
            time.sleep_us(150)
            read-=1
            i+=1
        self.cs(1)
        return r

    def send_command(self, cmd, read=0):
        "Send a single SPI command. Optionally write data specified in 'write'. Optionally read and return 'read' bytes."
        self.spi.init(baudrate=self.rate, polarity=1, phase=1)
        r = []
        self.cs(0)
        for v in cmd:
            self.spi.write(bytearray([v]))
            time.sleep_us(150)
        for i in range(read):
            r.append(self.spi.read(1)[0])
            time.sleep_us(150)
        self.cs(1)
        return r

    def self_test(self):
        r = self.send_command(b"\xc9", read=1)
        if r[0] == 0x57:
            print(self, "Self-test OK")
        else:
            print(self, "self-test failed: returned", r) 

    def read_analog(self, key):
        r = self.send_command(bytes([0x20+(key&0x0F)]), read=2)
        return (r[0]<<8)+r[1]
        
    def read_threshold(self, key):
        r = self.send_command(bytes([0x40+(key&0x0F)]), read=2)
        return (r[0]<<8)+r[1]
        print(r)

    def loop(self):
        r = self.send_command(b"\xc1", read=2)
        self.buttons = (r[0]<<8)+r[1]
    
    def button(self, b):
        "Return the status of button n. b"
        return (self.buttons>>b)&1
        
    def recalibrate_all_keys(self):
        self.send_command(b"\x03")
        #time.sleep_ms(160)#after reset
        time.sleep_us(150)#after a full recalibration

#End
