import display
import backlight
import os
import re
from board import vbat, vusb, vbat_ADC, vusb_ADC
from time import ticks_ms, sleep_ms

d=display.Display()
b=backlight.Backlight()

b.display(0x1, 0xF0) #Calibrate to get around 11mA


def logfile_name():
    "Returns the first unused logfile name in the format bat<num>.txt"
    index = 0
    for f, *t in os.ilistdir():
        m = re.match("bat([0-9]+)\\.txt", f)
        if m:
            index = max(index, int(m.group(1)))
    return "bat{}.txt".format(index+1)


def loop():
    fn = logfile_name()
    fd=open(fn, "w")
    fd.write("timestamp,time,vbat,vusb,vbat_read16,vusb_read16,vref\n")
    fd.close()
    while(True):
        t = ticks_ms()//1000
        h = "{:02}h{:02}m{:02}s".format(t//3600, t%3600//60, t%60)
        d.clear()
        d.text(h,0)
        d.text("Vbat: {:1.3} V".format(vbat()),1)
        d.text("Vusb: {:1.3} V".format(vusb()),2)
        fd=open(fn, "a")
        fd.write(",".join([str(t),h,str(vbat()),str(vusb()),str(vbat_ADC.read_u16()),str(vusb_ADC.read_u16()),str(vbat_ADC.VREF)])+"\n")
        fd.close()
        sleep_ms(10000)

loop()
#End