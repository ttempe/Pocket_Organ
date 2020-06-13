from machine import Pin, UART
#from pyb import UART
import time

  
class Midi:
    def __init__(self, synth=True):
        self.synth=synth
        self.uart = UART(3, 31250)
        self.buf3 = bytearray(3)
        self.rst = Pin("A15", Pin.OUT)
        self.rst(0)
        time.sleep_ms(200)
        self.rst(1)
        time.sleep_ms(200)
        

    def note_on(self, channel, note, vel=64):
         self.buf3[0] = 0x90 | (channel & 0x0F)
         self.buf3[1] = note & 0x7F
         self.buf3[2] = vel & 0x7F
         self.uart.write(self.buf3)
        
    def note_off(self, channel, note, vel=64):
        self.buf3[0] = 0x80 | (channel & 0x0F)
        self.buf3[1] = note & 0x7F
        self.buf3[2] = vel & 0x7F
        self.uart.write(self.buf3)

    def all_off(self, channel):
        self.buf3[0] = 0xB0 | (channel & 0x0F)
        self.buf3[1] = 123
        self.buf3[2] = 0
        self.uart.write(self.buf3)

    def set_instr(self, channel, instr):
        self.buf3[0] = 0xC0 | (channel & 0x0F)
        self.buf3[1] = 0
        self.buf3[2] = instr & 0x7F
        self.uart.write(self.buf3)
    
    def set_controller(self, channel, controller, value):
        self.buf3[0] = 0xB0 | (channel & 0x0F)
        self.buf3[1] = (controller & 0x7F)
        self.buf3[2] = (value & 0x7F)
        self.uart.write(self.buf3)
        
    
    def test2(self):
        while 1 :
            self.note_on(0, 60)
            time.sleep_ms(200)
            self.note_on(0, 64)
            time.sleep_ms(200)
            self.note_on(0, 67)
            time.sleep_ms(1600)
            self.note_off(0,60)
            self.note_off(0,64)
            self.note_off(0,67)
            time.sleep(1)
            
    def test1(self):
        while 1:
            self.uart.write(b"\x90\x40\x60")
            time.sleep(1)
            self.uart.write(b"\x80\x40\x60")

