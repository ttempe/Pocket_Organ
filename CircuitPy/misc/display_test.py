import adafruit_ssd1306, busio, board, digitalio
from adafruit_framebuf import FrameBuffer1

def pinOut(p, value=None):
    ret = digitalio.DigitalInOut(p)
    ret.direction = digitalio.Direction.OUTPUT
    if value!=None:
        ret.value =value
    return ret


spi = busio.SPI(clock=board.GP6, MOSI=board.GP7, MISO=None)

display = adafruit_ssd1306.SSD1306_SPI(width=128, height=32, spi=spi, dc=digitalio.DigitalInOut(board.GP5), cs=digitalio.DigitalInOut(board.GP4), reset=None)
display.rotation=2
display.fill(0)
display.line(0, 30, 127, 30,1)
display.text("Hello!", 0,0,1)
display.show()
