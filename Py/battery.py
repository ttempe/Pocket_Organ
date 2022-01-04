from board import vbat, vusb, verbose, version
from time import ticks_ms

if verbose:
    import os

bat_levels = [(4.15, "bat_100"),
              (3.7, "bat_70"),
              (3.6, "bat_20"),
              (0,   "bat_0")]

class Battery:
    def __init__(self, disp):
        self.last_time = 0
        self.d = disp
        self.disp_update = 0
        self.last_lvl = 0

    def disp_bat(self, lvl):
        self.d.disp.framebuf.rect(108, 0, 20, 0, 0)
        self.d.disp.framebuf.rect(127, 2, 1, 4, 1)
        self.d.disp.framebuf.rect(108, 0, 19, 8, 1)
        self.d.disp.framebuf.fill_rect(110, 2, lvl, 4, 1)
        self.d.disp.show_top8()

    def loop(self):
        if ticks_ms()-self.last_time > 500: #Update every 1/2s
            if vusb()>4.5: #Charging
                if self.last_lvl != None:
                    if verbose:
                        print("battery level changing to 'charging'")
                    self.d.indicator("bat_chrg", 108)
                    self.last_lvl = None
            else:
                lvl = min(int(14*(vbat()-3.3)/1.0),14)
                if lvl != self.last_lvl:
                    if verbose:
                        print("battery level changing to", lvl)
                    self.disp_bat(lvl)
                    self.last_lvl = lvl
            if verbose:
                if self.disp_update//4 == 0:
                    self.d.indicator_txt("-\|/"[self.disp_update%4] + str(vbat())[0:4]+"V", 57)
                elif self.disp_update//4 == 1:
                    self.d.indicator_txt("-\|/"[self.disp_update%4] + "v"+str(version) + "  ", 57)
                elif self.disp_update//4 == 2:
                    self.d.indicator_txt("-\|/"[self.disp_update%4] + os.uname()[3][-7:-6]+os.uname()[3][-5:-3]+os.uname()[3][-2:], 57)
                else:
                    self.disp_update = -1
                self.disp_update += 1
            self.last_time = ticks_ms()

#End
                