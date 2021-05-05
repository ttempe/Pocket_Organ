import ssd1306
import time
import framebuf
import board
import writer, font_med, font_big, font_small

#Instructions for creating files:
#in Gimp, image->mode->indexed, "use black-and-white (1-bit) palette"
#then export as PBM, and choose "Raw" data formatting.

#Notes:
# * disp.fill(0) takes  ~500 us
# * disp.show()  takes ~2200 us

#Screen structure (hard coded): 128*64
# Top 8 pixel: indicators bar
# Bottom 56: either 1 line of big font (40 pixels), or 1 + up to 2 lines of med font (18 pixels)

#Indicators:
# Pos Width Indicator
#   0     8 Memory Write
# 108    20 Battery

#TODO: Move the icons to frozen storage.

def load_image(name):
    "takes a filename, returns a framebuffer"
    filename = "img/"+name+".pbm"
    try:
        f = open(filename, 'rb')
    except:
        raise ImportError("Error opening file: " + filename)
    if b'P4\n' != f.readline():                         # Magic number
        pass
        raise ImportError("Invalid file: " + filename)
    f.readline()                                       # Creator comment
    width, height = list(int(j) for j in f.readline()[:-1].decode().split(" ")) # Dimensions
    data = bytearray(f.read())
    f = framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)
    return f, width, height

class Display:
    def __init__(self):
        #Display connected through SPI bus
        self.disp = ssd1306.SSD1306_SPI(128, 64, board.display_spi,
                            dc =  board.display_dc,
                            res = board.display_res,
                            cs =  board.display_cs,
                            external_vcc=False, mirror_v=True, mirror_h=True)
#        #variant: display connected through I2C bus
#        from machine import Pin, I2C
#        self.disp = ssd1306.SSD1306_I2C(128, 64, I2C(1))
        self.disp.contrast(100)
        self.disp_image("logo")
        self.erase_time = 0
        self.font_big = writer.Writer(self.disp.framebuf, font_big)
        self.font_big.set_clip(False, True, False)
        self.font_med = writer.Writer(self.disp.framebuf, font_med)
        self.font_med.set_clip(False, True, True)
        self.font_small = writer.Writer(self.disp.framebuf, font_small)
        self.font_small.set_clip(False, True, True)

    def _locate(self, x, y):
        writer.Writer.set_textpos(self.disp.framebuf, y, x)
    
    def disp_image(self, img):
        self.disp.framebuf.blit(load_image(img)[0], 0, 0)
        self.disp.show()

    def disp_indicator(self, img, pos):
        self.disp.framebuf.blit(load_image(img)[0], pos, 0)
        self.disp.show_top8() #Takes <1ms

    def disp_chord(self, text):
        #Displays text using the large font
        self.disp.framebuf.fill_rect(0,8,127,63,0)
        self._locate(0, 10)
        if self.font_big.stringlen(text)>128:
            self.font_big.printstring(text[:2])
            self.font_med.printstring(text[2:])
        else:
            self.font_big.printstring(text)
        self.disp.show()
    
    def text(self, text, line=0, tip=False, duration=None):
        if line:
            self.disp.framebuf.fill_rect(0,8+self.font_med.height,127,63,0)
        else:
            self.disp.framebuf.fill_rect(0,8,127,63,0)
        self._locate(0, 8+line*self.font_med.height)
        if tip:
            self.font_small.printstring(" ! ", True)
            self.font_small.printstring(text, False)
        else:
            self.font_med.printstring(text)
        self.disp.show()
        if duration:
            self.erase_time = time.ticks_ms() + duration
        print(text)

    def disp_slider(self, val, text):
        self.text(text)
        h = 8+self.font_med.height + 2 #where to draw the slider box
        ht = (h+63)//2-self.font_med.height//2 + 2 #where to draw the text inside
        self.disp.framebuf.rect(0, h, 127, 64-h, 1)
        self.disp.framebuf.fill_rect(0, h+1, val, 63-h, 1)
        s = "{0}%".format(val*100//127) #% value
        sl = self.font_med.stringlen(s) #length of that string in pixels
        if sl + 8 > val:
            self._locate(124-sl, ht)
            self.font_med.printstring(s)
        else:
            self._locate(val-sl-4,ht)
            self.font_med.printstring(s, True)

        self.disp.show()
        self.erase_time = time.ticks_ms() + 2000 #auto-erase after 2 seconds

    def clear(self):
        self.disp.framebuf.fill_rect(0,8,127,63,0)
        self.disp.show()
        self.erase_time = None

    def loop(self, freeze_display=None):
        if not freeze_display:
            if self.erase_time != None and self.erase_time <= time.ticks_ms():
                self.clear()      
#end
