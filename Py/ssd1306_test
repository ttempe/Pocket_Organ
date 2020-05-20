import ssd1306
from machine import SPI, Pin
import time

spi = SPI(1)
disp = ssd1306.SSD1306_SPI(128, 64, spi,
                           dc=Pin("B1", Pin.OUT),
                           res=Pin("C9", Pin.OUT),
                           cs=Pin("A8", Pin.OUT),
                           external_vcc=False)


time.sleep(1)
disp.contrast(50)
while 1:
    disp.fill(0)
    disp.show()
    time.sleep(1)
    disp.fill(1)
    disp.show()
    time.sleep(1)
    
test()