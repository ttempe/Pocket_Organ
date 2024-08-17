import displayio, busio
import adafruit_displayio_ssd1306
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

from supervisor import ticks_ms
import board_po as board
from version import version

#Screen structure (hard coded): 128*64
# Top 8 pixel: indicators bar
# Bottom 56: either 1 line of big font (40 pixels), or 1 + up to 2 lines of med font (18 pixels)
# TODO: redo the big font with the spacebar character

#Indicators:
# Pos Width Indicator
#   0     9 Memory Write
#   9    24 SW version
#  24    32 loop duration
#  60    48 Battery voltage (debug)
# 108    20 Battery

#Actuals:
# 24		latency
# 57		status

all_letters="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789.,!?"

#TODO: Move the icons to frozen storage.

class Display:
    def __init__(self):
        #framebuf_init()#Displayio apparently fails to initialize the display, lighting random pixels
        displayio.release_displays()
        disp_SPI = busio.SPI(clock=board.disp_CLK, MOSI=board.disp_MOSI, MISO=None)
        display_bus = displayio.FourWire(disp_SPI, command=board.disp_DC, chip_select=board.disp_CS, reset=board.disp_RST, baudrate=1000000)
        self.disp = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64, rotation=180, brightness=0)#,auto_refresh=True, brightness=1
        self.disp.root_group = displayio.Group()

        #add that one first, we will remove it later
        #bitmap = displayio.OnDiskBitmap("logo.bmp")
        #self.disp.root_group.append(displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader))

        # Only includes a few letters, as required for displaying chord names.
        # Prepared based on these instructions: https://learn.adafruit.com/custom-fonts-for-pyportal-circuitpython-display/conversion
        # then converted with this tool: https://adafruit.github.io/web-bdftopcf/
        font_big   = bitmap_font.load_font("fonts/bigfont.pcf")
        font_med   = bitmap_font.load_font("fonts/Involve-Regular-14.pcf")
        font_small = bitmap_font.load_font("fonts/Urbanist-Light-10.pcf")
                
        self.chord_name = label.Label(font_big, text="", y=44)#text area can be updated, but can't be made wider
        self.disp.root_group.append(self.chord_name)

        loading = label.Label(font_med, text="Loading...", x=32, y=32)
        self.disp.root_group.append(loading)
        
        #pre-load ; display is faster after that
        label.Label(font_big, text="ABCDEFG7augdims24#")
        label.Label(font_med, text=all_letters)
        label.Label(font_small, text=all_letters)
        loading.hidden = True
        
        self.latency = label.Label(font_small, text="00ms", x=24, y=5)
        self.disp.root_group.append(self.latency)

        self.status = label.Label(font_small, text="0.00V-", x=57, y=5)
        self.disp.root_group.append(self.status)

        self.tips_zone = label.Label(font_small, text="", x=0, y=45)
        self.tips_zone.anchor_point=(0,0)
        self.disp.root_group.append(self.tips_zone)
        
        self.slider_zone = displayio.Group(x=0, y=30)
        self.slider_zone.hidden = True
        self.disp.root_group.append(self.slider_zone)
        self.slider_zone.append(Rect(0,0,127,33, fill=0, outline=1))
        
        self.text_zones = []
        for i in range(3):
            z = label.Label(font_med, text="", x=0, y=16+i*14)
            z.anchor_point=(0,0)
            self.disp.root_group.append(z)
            self.text_zones.append(z)

        self.erase_time = ticks_ms() + 2000
        self.slider_last_val = 0
        self.slider_last_time = 0

    def _disp_image(self, img, x=0, y=0):
        #Wastes a lot of RAM. At least the bytearray duplicates the image into memory.
        #TODO: where is this used?
        print("Display._disp_image")

    def disp_image(self, img):
        #TODO: where is this used?
        print("Display.disp_image")

    def indicator(self, img, pos):
#        self._disp_image(img, pos, 0)
#        self.disp.show_top8() #Takes <1ms
        pass
    
#    def indicator_txt(self, txt, pos):
#        self.disp.framebuf.fill_rect(pos,0,len(txt)*8,8,0)
#        self.disp.text(txt, pos, 0)
#        self.disp.show_top8()
#        print("disp.indicator_text") #TODO: where is it called?
    
#    def indicator_erase(self, pos, length):
#        self.disp.framebuf.fill_rect(pos,0,length,8,0)
#        self.disp.show_top8()


    def disp_chord(self, degree, shape):
        #Displays text using the large font
        #TODO: display the "shape" with a smaller font if it's too long to fit the screen.
        self.clear()
        self.chord_name.text = degree+shape
        if board.verbose:
            print("Playing chord:", degree, shape)
    
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
        self.chord_name.text=""
        if tip:
            self.tips_zone.text = text
        else:
            self.text_zones[line].text = text
        self.erase_time = ticks_ms() + 2000

        if board.verbose and not tip:
            print(text)

    def disp_slider(self, val, text):
        self.text(text)
        self.slider_zone.pop()
        self.slider_zone.append(Rect(0,0,val,33, fill=1, outline=1))
        self.slider_zone.hidden=False
        #if abs(val - self.slider_last_val > 2) or ticks_ms()-self.slider_last_time > 100:
        print(text, val, "*"*(val//4)+"-"*((127-val)//4))
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

    def clear(self, all=True):
        self.chord_name.text = ""
        self.tips_zone.text = ""
        for z in self.text_zones:
            z.text=""
        self.slider_zone.hidden=True
        self.erase_time = None
        if all==True:
            self.latency.text = ""
            self.status.text = ""

    def loop(self, freeze_display=None):
        #TODO: instead of freezing the display, just don't call
        if not freeze_display:
            if self.erase_time != None and self.erase_time <= ticks_ms():
                self.clear()
#End
