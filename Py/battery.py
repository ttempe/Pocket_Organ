from board import vbat, vusb, verbose
from time import ticks_ms

bat_levels = [(4.15, "bat_100"),
              (3.7, "bat_70"),
              (3.6, "bat_20"),
              (0,   "bat_0")]

class Battery:
    def __init__(self, disp):
        self.last_val = 0
        self.last_time = 0
        self.d = disp
        self.last_icon = ""
        self.disp_update = 0
        self.last_lvl = 0
        
    def classify(self, val):
        for lvl, icon in bat_levels:
            if val>lvl:
                return icon

    def disp_bat(self, lvl):
        self.d.disp.framebuf.rect(108, 0, 20, 0, 0)
        self.d.disp.framebuf.rect(127, 2, 1, 4, 1)
        self.d.disp.framebuf.rect(108, 0, 19, 8, 1)
        self.d.disp.framebuf.fill_rect(110, 2, lvl, 4, 1)
        self.d.disp.show_top8()


    def loop(self):
        #TODO: Test again on V19
        #TODO: Re-draw the "charging" icon. (Maybe without a battery, only a plug or USB logo?)
        if ticks_ms()-self.last_time > 500:
            if vusb()>4.5 and self.last_lvl != None:
                self.d.indicator("bat_chrg", 108)
                last_lvl = None
            else:
                lvl = min(int(14*(vbat()-3.3)/1.0),14)
                if lvl != self.last_lvl:
                    self.disp_bat(lvl)
                    self.last_lvl = lvl
            if verbose:
                self.d.indicator_txt("-\|/"[self.disp_update%4] + str(vbat())[0:4]+"V", 58)
                self.disp_update += 1
            self.last_time = ticks_ms()

#End
                