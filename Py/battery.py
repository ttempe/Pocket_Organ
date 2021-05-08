from board import vbat, vusb
from time import ticks_ms

bat_levels = [(4.2, "bat_100"),
              (3.7, "bat_70"),
              (3.6, "bat_20"),
              (0,   "bat_0")]

class Battery:
    def __init__(self, disp):
        self.last_val = 0
        self.last_time = 0
        self.d = disp
        self.last_icon = ""
        
    def classify(self, val):
        for lvl, icon in bat_levels:
            if val>lvl:
                return icon
        
    def loop(self):
        if ticks_ms()-self.last_time > 1000:
            if vusb()>4.5:
                icon = "bat_chrg"
            else:
                icon = self.classify(vbat())
            if icon != self.last_icon:
                self.d.indicator(icon, 108)
                self.last_icon = icon
            self.d.indicator_txt(str(vbat())[0:4]+"V", 68)
            self.last_time = ticks_ms()

#End
                