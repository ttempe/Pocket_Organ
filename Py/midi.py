from machine import Pin, UART
#from pyb import UART
import time

  
class Midi:
    def __init__(self, looper):
        self.l = looper
        self.uart = UART(3, 31250)
        self.buf3 = bytearray(3)
        self.rst = Pin("A15", Pin.OUT)
        self.rst(0)
        time.sleep_ms(200)
        self.rst(1)
        time.sleep_ms(200)
        

#     def note_on(self, channel, note, vel=64):
#          self.buf3[0] = 0x90 | (channel & 0x0F)
#          self.buf3[1] = note & 0x7F
#          self.buf3[2] = vel & 0x7F
#          self.uart.write(self.buf3)

    def note_on(self, channel, note, vel=64):
        n = bytearray([0x90| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        self.uart.write(n)
        self.l.append(n)

        
    def note_off(self, channel, note, vel=64):
        n = bytearray([0x80| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        self.uart.write(n)
        self.l.append(n)
 
    def all_off(self, channel):
        n = bytearray([0xB0| (channel & 0x0F),
                       123,
                       0])
        self.uart.write(n)
        self.l.append(n)

    def set_instr(self, channel, instr):
        n = bytearray([0xC0| (channel & 0x0F),
                       0,
                       instr & 0x7F])
        self.uart.write(n)
        self.l.append(n)
    
    def set_controller(self, channel, controller, value):
        n = bytearray([0xB0| (channel & 0x0F),
                       controller & 0x7F,
                       value & 0x7F])
        self.uart.write(n)
        self.l.append(n)        
    
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

#End
