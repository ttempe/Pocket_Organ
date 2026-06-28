import displayio, busio
import adafruit_displayio_ssd1306
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

from supervisor import ticks_ms
import board_po as board
from version import version

WHITE = 0xFFFFFF
BLACK = 0x000000

#Screen structure (hard coded): 128*64
# Top 8 pixel: indicators bar
# Bottom 56: either 1 line of big font (40 pixels), or 1 + up to 2 lines of med font (18 pixels)

# TODO:
# * redo the big font with the spacebar character
# * could I further prune the "all_letters" string? Run a script to check the existing text in the code.

#Indicators:
# Pos Width Indicator
#   0     9 Memory Write
#   9    24 SW version
#  24    32 loop duration
#  60    48 Battery voltage (debug)
# 108    20 Battery

#Actuals:
# 24		latency

# Battery icon at x=108: 16px body + 2px terminal nub in the 8px status bar
_BAT_X = 108
_BAT_BODY_W = 16
_BAT_BODY_H = 6
_BAT_FILL_MAX = 14  # inner width (body minus 1px padding each side)

class Display:
    def __init__(self):
        displayio.release_displays()
        disp_SPI = busio.SPI(clock=board.disp_CLK, MOSI=board.disp_MOSI, MISO=None)
        display_bus = displayio.FourWire(disp_SPI,
            command=board.disp_DC, chip_select=board.disp_CS, reset=board.disp_RST, baudrate=1000000)
        self.disp = adafruit_displayio_ssd1306.SSD1306(display_bus,
            width=128, height=64, rotation=180, brightness=0, auto_refresh=False)
        self.disp.root_group = displayio.Group()

        # Prepared based on these instructions: https://learn.adafruit.com/custom-fonts-for-pyportal-circuitpython-display/conversion
        # then converted with this tool: https://adafruit.github.io/web-bdftopcf/
        font_big   = bitmap_font.load_font("fonts/bigfont.pcf") # Only includes a few letters
        font_med   = bitmap_font.load_font("fonts/Involve-Regular-14.pcf")
        font_small = bitmap_font.load_font("fonts/Urbanist-Light-10.pcf")

        #pre-load to speed up display
        font_big.load_glyphs("ABCDEFG7augdims24#ro")
        font_med.load_glyphs(all_letters:="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789.,!?")
        font_small.load_glyphs(all_letters)

        self.chord_name = label.Label(font_big, text="", y=44) # text area can be updated, but can't be made wider
        self.latency = label.Label(font_small, text="", x=24, y=5)
        self.tips_zone = label.Label(font_small, text="", x=0, y=45)
        self.tips_zone.anchor_point=(0,0)

        self.bat_zone = displayio.Group(x=_BAT_X, y=0)
        self.bat_zone.append(Rect(0, 1, _BAT_BODY_W, _BAT_BODY_H, outline=WHITE, stroke=1))
        self.bat_zone.append(Rect(_BAT_BODY_W + 1, 2, 2, 4, fill=WHITE))
        self.bat_zone.append(Rect(1, 2, 0, 4, fill=WHITE))

        for i in [self.chord_name, self.latency, self.tips_zone, self.bat_zone]:
            self.disp.root_group.append(i)

        self.text_zones = []
        for i in range(3):
            z = label.Label(font_med, text="", x=0, y=16+i*14)
            z.anchor_point=(0,0)
            self.disp.root_group.append(z)
            self.text_zones.append(z)

        self.slider_zone = displayio.Group(x=0, y=30)
        self.slider_zone.hidden = True
        self.disp.root_group.append(self.slider_zone)
        self.slider_zone.append(Rect(0,0,127,33, fill=BLACK, outline=WHITE))
        self.slider_zone.append(Rect(0,0,127,33, fill=WHITE, outline=WHITE))

        self.erase_time = ticks_ms() + 2000
        self.disp.refresh()

    def _set_bat_fill(self, fill_w):
        self.bat_zone.pop()
        self.bat_zone.append(Rect(1, 2, fill_w, 4, fill=WHITE))

    def disp_bat(self, lvl):
        "lvl: 0-100 percent"
        fill_w = int(_BAT_FILL_MAX * max(0, min(100, lvl)) / 100 + 0.5)
        self._set_bat_fill(fill_w)
        self.disp.refresh()

    def disp_bat_charging(self, fill_w):
        self._set_bat_fill(min(fill_w, _BAT_FILL_MAX))
        self.disp.refresh()

    def disp_chord(self, degree, shape):
        #Displays text using the large font
        #TODO: display the "shape" with a smaller font if it's too long to fit the screen.
        self.clear()
        self.chord_name.text = degree+shape
        if board.verbose:
            print("Playing chord:", degree, shape)
        self.disp.refresh()

    def text(self, text, line=0, tip=False, err=False):
        self.chord_name.text=""
        if tip:
            self.tips_zone.text = text
        else:
            self.text_zones[line].text = text
        self.erase_time = ticks_ms() + 2000

        if board.verbose and not tip:
            print(text)
        self.disp.refresh()

    def disp_slider(self, val, text):
        "Slider bar (eg: for volume), range: 0-127"
        val = min(127, max(0, val))
        if self.slider_zone.hidden:
            self.text(text)
        self.slider_zone.hidden=False
        self.slider_zone.pop()
        self.slider_zone.append(Rect(0, 0, val, 33, fill=WHITE, outline=WHITE)) #Todo: update lib and try self.slider_zone[1].width=val
        self.disp.refresh()

        print(text, val, "*"*(val//4)+"-"*((127-val)//4))

    def show_error(self, lines):
        self.clear()
        self.chord_name.text = "Error"
        for i, line in enumerate(lines[:3]):
            self.text_zones[i].text = line
        self.erase_time = None
        self.disp.refresh()

    def clear(self, all=True):
        self.chord_name.text = ""
        self.tips_zone.text = ""
        for z in self.text_zones:
            z.text=""
        self.slider_zone.hidden=True
        self.erase_time = None
        if all==True:
            self.latency.text = ""
        self.disp.refresh()

    def loop(self):
        if self.erase_time != None and self.erase_time <= ticks_ms():
            self.clear(all=False)
            self.disp.refresh()

#End
