import adafruit_ssd1306, busio, board, digitalio
from adafruit_framebuf import FrameBuffer1
from supervisor import ticks_ms
import board_po as board
from version import version
#import writer, font_med, font_big, font_small
#import images

#Instructions for creating files:
#in Gimp, image->mode->indexed, "use black-and-white (1-bit) palette"
#then export as PBM, and choose "Raw" data formatting.

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
        self.disp = adafruit_ssd1306.SSD1306_SPI(width=128, height=64, spi=board.disp_SPI, dc=board.disp_DC, cs=board.disp_CS, reset=None)
        self.disp.rotation=2
        self.disp.fill(0)
        self.disp.text("PocketOrgan V{}!".format(version), 0,0,1)
        self.disp.show()

        #self.disp.contrast(100) #0~255 TODO: Test ouside in bright sunlight
#         self.disp_image(images.logo)
#         self.erase_time = ticks_ms() + 2000
#         self.font_big = writer.Writer(self.disp.framebuf, font_big)
#         self.font_big.set_clip(False, True, False)
#         self.font_med = writer.Writer(self.disp.framebuf, font_med)
#         self.font_med.set_clip(False, True, True)
#         self.font_small = writer.Writer(self.disp.framebuf, font_small)
#         self.font_small.set_clip(False, True, True)
#         self.slider_last_val = 0
#         self.slider_last_time = 0

    def _locate(self, x, y):
#         writer.Writer.set_textpos(self.disp.framebuf, y, x)
        pass

    def _disp_image(self, img, x=0, y=0):
        #Wastes a lot of RAM. At least the bytearray duplicates the image into memory.
        #TODO: write a function to blit the image directly into the framebuffer, without creating a bytearray in memory, based on writer.py
#         self.disp.framebuf.blit(framebuf.FrameBuffer(bytearray(img[0]), img[1], img[2], framebuf.MONO_HLSB), x, y)
        pass

    def disp_image(self, img):
#        self._disp_image(img)
#        self.disp.show()
        pass

    def indicator(self, img, pos):
#        self._disp_image(img, pos, 0)
#        self.disp.show_top8() #Takes <1ms
        pass
    
    def indicator_txt(self, txt, pos):
#        self.disp.framebuf.fill_rect(pos,0,len(txt)*8,8,0)
#        self.disp.text(txt, pos, 0)
#        self.disp.show_top8()
        pass
    
    def indicator_erase(self, pos, length):
#        self.disp.framebuf.fill_rect(pos,0,length,8,0)
#        self.disp.show_top8()
        pass

    def disp_chord(self, degree, shape):
        #Displays text using the large font
#         self.disp.framebuf.fill_rect(0,8,127,63,0)
#         self._locate(0, 10)
#         self.font_big.printstring(degree)
#         if self.font_big.stringlen(degree+shape)>128:
#             self.font_med.printstring(shape)
#         else:
#             self.font_big.printstring(shape)
#         self.disp.show()
#         if board.verbose:
#             print("Playing chord:", degree, shape)
        pass
    
    def text(self, text, line=0, tip=False, err=False):
#         self.disp.framebuf.fill_rect(0,8+self.font_med.height*line,127,63,0)
#         self._locate(0, 8+line*self.font_med.height)
#         if tip:
#             self.font_small.printstring(text, True)
#         elif err:
#             self.font_small.set_clip(False, False, False)
#             self.font_small.printstring(text, False)
#         else:
#             self.font_med.printstring(text)
#         self.disp.show()
#         self.erase_time = ticks_ms() + 2000
#         if board.verbose and not tip:
#             print(text)
        pass

    def disp_slider(self, val, text):
#         if abs(val - self.slider_last_val > 2) or ticks_ms()-self.slider_last_time > 100:
#             self.text(text)
#             h = 8+self.font_med.height + 2 #where to draw the slider box
#             ht = (h+63)//2-self.font_med.height//2 + 2 #where to draw the text inside
#             self.disp.framebuf.rect(0, h, 127, 64-h, 1)
#             self.disp.framebuf.fill_rect(0, h+1, val, 63-h, 1)
#             s = "{0}%".format(val*100//127) #% value
#             sl = self.font_med.stringlen(s) #length of that string in pixels
#             if sl + 8 > val:
#                 self._locate(124-sl, ht)
#                 self.font_med.printstring(s)
#             else:
#                 self._locate(val-sl-4,ht)
#                 self.font_med.printstring(s, True)
#             self.disp.show()
#             self.slider_last_time = ticks_ms()
#             self.slider_last_val = val
        pass

    def clear(self):
#         self.disp.framebuf.fill_rect(0,8,128,56,0)
#         self.disp.show()
#         self.erase_time = None
        pass

    def loop(self, freeze_display=None):
#         if not freeze_display:
#             if self.erase_time != None and self.erase_time <= ticks_ms():
#                 self.clear()
        pass
#end
