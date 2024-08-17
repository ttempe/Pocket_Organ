from board_po import verbose, version
from supervisor import ticks_ms
#import images

if verbose:
    import os

#TODO: disable battery level update when any key backlight is on?

#TODO
def vbat():
    return 0
def vusb():
    return 0

class Battery:
    def __init__(self, disp):
        self.last_time = 0
        self.d = disp
        self.disp_update = 0
        self.last_lvl = 0
        self.vbat = vbat()*20

    def disp_bat(self, lvl):
        #Todo
#         self.d.disp.framebuf.fill_rect(108, 0, 20, 8, 0)
#         self.d.disp.framebuf.rect(127, 2, 1, 4, 1)
#         self.d.disp.framebuf.rect(108, 0, 19, 8, 1)
#         self.d.disp.framebuf.fill_rect(110, 2, lvl, 4, 1)
#         self.d.disp.show_top8()
        pass

    def loop(self):
        if ticks_ms()-self.last_time > 500: #Update every 1/2s
            if vusb()>4500: #Charging
                if self.last_lvl != None:
                    if verbose:
                        print("battery level changing to 'charging'")
#                     self.d.indicator(images.bat_chrg, 108) #TODO
                    self.last_lvl = None
            else:
                if self.last_lvl == None:
                    self.vbat = vbat()*20
                else:
                    self.vbat = int(self.vbat*.95)+vbat() #average the recent readings
                lvl = min(int(14*max(self.vbat-3720,0)/0.24),14)//1000
                if lvl != self.last_lvl:
                    if verbose:
                        print("battery level changing to", lvl)
                    self.disp_bat(lvl)
                    self.last_lvl = lvl
            if verbose:
                if (self.disp_update & 0x8) == 0:
                    #self.d.indicator_txt("-\|/"[self.disp_update%4] + str(vbat())[0:4]+"V", 57)
                    self.d.status.text = "{}V {}".format(vbat(), "-\|/"[self.disp_update%4])
                else:
                    #self.d.indicator_txt("-\|/"[self.disp_update%4] + "v"+str(version) + "  ", 57)
                    self.d.status.text = "v{} {}".format(version, "-\|/"[self.disp_update%4])
                self.disp_update += 1
            self.last_time = ticks_ms()

#End
