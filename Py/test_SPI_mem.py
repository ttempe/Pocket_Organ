from machine import SPI
from machine import Pin
import time

def f():
    cs_flash = Pin("B11", Pin.OUT) #V13: B11; V14: B12
    cs_flash.value(0)
    spi = SPI(1)
    buf = bytearray(8)
    #spi.send(b"\x9F")
    time.sleep_ms(10)
    #spi.write(b"\x9F")
    #spi.write(b"\x9F")
    spi.write(b"\x9F")
    #spi.write(b"\x05")

    #time.sleep_ms(10)
    spi.readinto(buf)
    cs_flash.value(1)
    print(buf)
    time.sleep_ms(200)

while 1:
    f()