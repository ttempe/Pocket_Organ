from machine import Pin, I2C
import time

muxA = Pin(5, Pin.OUT)
muxB = Pin(6, Pin.OUT)

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000) #Pocket Organ 
#i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=100000) #Breadboard

class FDC2214:
    def __init__(self, i2c, addr=0x2A):
        self.i2c = i2c
        self.addr = addr
#        i2c.writeto_mem(self.addr, 0x1A, bytes(0b001111000000001))
        self.buf = memoryview(bytearray(4))
        #Read and check the Manufacturer ID and Device ID of the FDC2214
        if (int.from_bytes(i2c.readfrom_mem(42, 0x7E, 2), "big") != 0x5449) or\
           (int.from_bytes(i2c.readfrom_mem(42, 0x7F, 2), "big") != 0x3055):
            raise Exception("FDC2214 not found.")
        i2c.writeto_mem(self.addr, 0x1B, b'\xc2\x0f')#b1100001000001111))#1001000001101)) #multiplexed mode
        i2c.writeto_mem(self.addr, 0x1A, b'\x18\x81')#bytes(0b0001010000000001)) #get out of sleep mode
            
    def _read28(self, addr):
        a0 = int.from_bytes(self.i2c.readfrom_mem(42, addr,   2), "big")
        a1 = int.from_bytes(self.i2c.readfrom_mem(42, addr+1, 2), "big")
        return ((a0&0xFFF)<<16)+a1

c=FDC2214(i2c)

amax = c._read28(0)
bmax = c._read28(2)
cmax = c._read28(4)
dmax = c._read28(6)

muxA(1) #lsb
muxB(1) #msb

while True:
#    a2 = int.from_bytes(i2c.readfrom_mem(42, 0x02, 2), "big")
#    a3 = int.from_bytes(i2c.readfrom_mem(42, 0x03, 2), "big")
    aa = c._read28(0)-amax
    bb = c._read28(2)-bmax
    cc = c._read28(4)-cmax
    dd = c._read28(6)-dmax
    print(aa, bb)
    time.sleep_ms(20)
