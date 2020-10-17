import ssd1306
import time
import framebuf
import board

#Notes:
# * disp.fill(0) takes  ~500 us
# * disp.show()  takes ~2200 us

def load_image(name):
    "takes a filename, returns a framebuffer"
    try:
        f = open(name, 'rb')
    except:
        raise ImportError("Error opening file: "+name)
    if b'P4\n' != f.readline():                         # Magic number
        raise ImportError("Invalid file: "+name)
    f.readline()                                       # Creator comment
    width, height = list(int(j) for j in f.readline()[:-1].decode().split(" ")) # Dimensions
    data = bytearray(f.read())
    f = framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)
    return f, width, height

class Display:
    def __init__(self):
        self.disp = ssd1306.SSD1306_SPI(128, 64, board.display_spi,
                           dc =  board.display_dc,
                           res = board.display_res,
                           cs =  board.display_cs,
                           external_vcc=False, mirror_v=True, mirror_h=True)

        self.disp.contrast(50)
        self.disp_image("img/logo.pbm")
        self.disp.show()
        self.erase_time = 0


    def disp_image(self, img):
        self.disp.framebuf.blit(load_image(img)[0], 0, 0)
        self.disp.show()

    def disp_chord(self, text):
        """Displays text using the large font"""
        self.disp.fill(0)
        x = 0
        for c in text:
            try:
                img, width, height = load_image("img/"+c+".pbm") 
                self.disp.framebuf.blit(img, x, 16)
                x += width
            except ImportError:
                print("Error loading file for", c)
        self.disp.show()
    
    def text(self, text, line=0, duration=None):
        if not line:
            self.disp.fill(0)
        self.disp.text(text, 0,line*8,1)
        self.disp.show()
        if duration:
            self.erase_time = time.ticks_ms() + duration
        print(text)

    def disp_volume(self, volume, text = "Volume"):
        self.disp.fill(0)
        self.disp.text(text, 0, 0, 1)
        self.disp.framebuf.rect(0, 20, 127, 40, 1)
        self.disp.framebuf.fill_rect(0, 21, volume, 38, 1)
        if volume<64:
            self.disp.text("{}%".format(volume*100//128), 64, 26, 1)
        else:
            self.disp.text("{}%".format(volume*100//128), 40, 26, 0)

        self.disp.show()
        self.erase_time = time.ticks_ms() + 2000 #auto-erase after 2 seconds

    def clear(self):
        self.disp.fill(0)
        self.disp.show()
        self.erase_time = None

    def loop(self):
        if self.erase_time != None and self.erase_time <= time.ticks_ms():
            self.clear() #takes no time at all.
        
#end
