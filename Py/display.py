import ssd1306
import time
import framebuf
import board
import writer, font_med, font_big, font_small
import images

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
#   0     9 Memory Write
#   9    24 SW version
#  24    32 loop duration
#  60    48 Battery voltage (debug)
# 108    20 Battery
    
#TODO: Move the icons to frozen storage.

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
        self.disp.contrast(100) #0~255 TODO: Test ouside in bright sunlight
        self.disp_image(images.logo)
        self.erase_time = time.ticks_ms() + 2000
        self.font_big = writer.Writer(self.disp.framebuf, font_big)
        self.font_big.set_clip(False, True, False)
        self.font_med = writer.Writer(self.disp.framebuf, font_med)
        self.font_med.set_clip(False, True, True)
        self.font_small = writer.Writer(self.disp.framebuf, font_small)
        self.font_small.set_clip(False, True, True)
        self.slider_last_val = 0
        self.slider_last_time = 0

    def _locate(self, x, y):
        writer.Writer.set_textpos(self.disp.framebuf, y, x)

    def _disp_image(self, img, x=0, y=0):
        #Wastes a lot of RAM. At least the bytearray duplicates the image into memory.
        #TODO: write a function to blit the image directly into the framebuffer, without creating a bytearray in memory, based on writer.py
        self.disp.framebuf.blit(framebuf.FrameBuffer(bytearray(img[0]), img[1], img[2], framebuf.MONO_HLSB), x, y)

    def disp_image(self, img):
        self._disp_image(img)
        self.disp.show()

    def indicator(self, img, pos):
        self._disp_image(img, pos, 0)
        self.disp.show_top8() #Takes <1ms
    
    def indicator_txt(self, txt, pos):
        self.disp.framebuf.fill_rect(pos,0,len(txt)*8,8,0)
        self.disp.text(txt, pos, 0)
        self.disp.show_top8()
    
    def indicator_erase(self, pos, length):
        self.disp.framebuf.fill_rect(pos,0,length,8,0)
        self.disp.show_top8()

    def disp_chord(self, degree, shape):
        #Displays text using the large font
        self.disp.framebuf.fill_rect(0,8,127,63,0)
        self._locate(0, 10)
        self.font_big.printstring(degree)
        if self.font_big.stringlen(degree+shape)>128:
            self.font_med.printstring(shape)
        else:
            self.font_big.printstring(shape)
        self.disp.show()
        if board.verbose:
            print("Playing chord:", degree, shape)
    
    def text(self, text, line=0, tip=False, err=False):
        self.disp.framebuf.fill_rect(0,8+self.font_med.height*line,127,63,0)
        self._locate(0, 8+line*self.font_med.height)
        if tip:
#            self.font_small.printstring(" i ", True)
            self.font_small.printstring(text, True)
        elif err:
            self.font_small.set_clip(False, False, False)
            self.font_small.printstring(text, False)
        else:
            self.font_med.printstring(text)
        self.disp.show()
        self.erase_time = time.ticks_ms() + 2000
        if board.verbose and not tip:
            print(text)

    def disp_slider(self, val, text):
        if abs(val - self.slider_last_val > 2) or time.ticks_ms()-self.slider_last_time > 100:
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
            self.slider_last_time = time.ticks_ms()
            self.slider_last_val = val

    def clear(self):
        self.disp.framebuf.fill_rect(0,8,128,56,0)
        self.disp.show()
        self.erase_time = None

    def loop(self, freeze_display=None):
        if not freeze_display:
            if self.erase_time != None and self.erase_time <= time.ticks_ms():
                self.clear()      
#end
