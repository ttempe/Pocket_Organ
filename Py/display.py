import ssd1306
from machine import SPI, Pin
import time
import framebuf

def load_image(name):
    "takes a filename, returns a framebuffer"
    f = open(name, 'rb')
    if b'P4\n' != f.readline():                         # Magic number
        raise ImportError("Invalid file")
    f.readline()                                       # Creator comment
    width, height = list(int(j) for j in f.readline()[:-1].decode().split(" ")) # Dimensions
    data = bytearray(f.read())
    f = framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)
    return f, width, height

class Display:
    def __init__(self):
        self.disp = ssd1306.SSD1306_SPI(128, 64, SPI(1),
                           dc=Pin("B1", Pin.OUT),
                           res=Pin("C9", Pin.OUT),
                           cs=Pin("A8", Pin.OUT),
                           external_vcc=False)

        self.disp.contrast(50)
        #self.disp.rotate180()
        self.disp.write_cmd(0xc8)
        self.disp.write_cmd(0xb0)
        self.disp.framebuf.blit(load_image("img/logo.pbm")[0],0,0)
        self.disp.show()


    def disp_image(self, img):
        self.disp.framebuf.blit(load_image(img), 0, 0)
        self.disp.show()

    def disp_chord(self, text):
        """Displays text using the large font"""
        x = 0
        self.disp.fill(0)
        for c in text:
            img, width, height = load_image("img/"+c+".pbm") 
            self.disp.framebuf.blit(img, x, 0)
            x += width
        self.disp.show()
            
#end
