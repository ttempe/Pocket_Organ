import time
import board
import display
import backlight
import pyb
import AT42QT1110

t0=time.ticks_ms()
d=display.Display()
ba=backlight.Backlight()
adcAll=pyb.ADCAll(12, 0x70000)
uc1 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc1_cs)
uc2 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc2_cs)
uc3 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc3_cs)



ba.display(0, 0) #to create battery load
step = 20 #nb of seconds per pixel; 60s-> ~2h per screen width

def vbat():
    return board.vbat()

def pix(v):
    return int(64-((v-2.5)*20))

def disp_log(log):
    #Display scale
#    d.disp.framebuf.line(0,pix(3),127,pix(3),1)
#    d.disp.framebuf.line(0,pix(4),127,pix(4),1)
    for i in range(0, 42):
        d.disp.pixel(i*3, pix(3), 1)
        d.disp.pixel(i*3, pix(4), 1)
    for i in range(0, 31):
        d.disp.pixel(i*4, pix(3.5), 1)
        d.disp.pixel(i*4, pix(2.5), 1)
    d.disp.framebuf.text("3V", 0, pix(3)-8,1)
    d.disp.framebuf.text("4V", 0, pix(4)-8,1)
    
    #Display graph
    for x, y in enumerate(log):
        d.disp.pixel(x, int(64-((y-2.5)*20)), 1)
    d.disp.show()

def discharge():
    "Run a battery discharge test, display and record the results, incl. the value of each analog key, over time."
    t = t0
    log = []
    fd = open("plot_bat.txt", "a")
    fd.write("time,time_human, Vbat,sensor1,...")
    fd.close()
    while(True):
        t += 1000*step
        while(time.ticks_ms()<t):
            time.sleep_ms(1000)
            v = vbat()
            t1 = (time.ticks_ms()-t0)/1000
            d.text("{}:{:02}:{:02} {:.3}V".format(int(t1/3600), int(t1/60)%60, int(t1)%60, v))
            disp_log(log)
        fd = open("plot_bat.txt", "a")
        fd.write("{},{:.3},{:.4},{:.4},".format((t-t0)/1000, v, board.vbat(), adcAll.read_core_vref()))
        for uc in [uc1, uc2, uc3]:
            for i in range(11):
                fd.write("{},".format(uc.read_analog(i)))
        fd.write("\n")
        fd.close()
        log.append(v)
        if len(log)>127:
            a.pop(0)

def discharge_with_backlight():
    """Run a battery discharge test, display and record the results.
    Turn max backlight on for a second every so often, in order to be in the worst-case scenario for brown-out detection"""
    t = t0
    v2 = 0
    log = []
    ba.display(0, 0)
    fd = open("plot_bat.txt", "a")
    fd.write("time, voltage (low load), voltage (high load)\n")
    while(True):
        t += 1000*step
        while(time.ticks_ms()<t):
            time.sleep_ms(1000)
            v = vbat()
            t1 = (time.ticks_ms()-t0)/1000
            d.text("{}:{:02}:{:02} {:.2}-{:.2}V".format(int(t1/3600), int(t1/60)%60, int(t1)%60, v2, v))
            disp_log(log)
        ba.display(255, 255)
        time.sleep(1)
        v2 = vbat()
        ba.display(0, 0)        
        fd = open("plot_bat.txt", "a")
        fd.write("{},{:.4},{:.4},".format((t-t0)/1000, v, v2))
        fd.write("\n")
        fd.close()
        log.append(v)
        if len(log)>127:
            a.pop(0)

def test_voltage_drop():
    "Blink the backlights, and display impact on voltage"
    def dl(delta=None):
        v=0
        for i in range(1,11):
            time.sleep_ms(200)
            v+=vbat()
            if delta:
                d.text("{:.2}V delta: {:.2}V".format(v/i, delta-v/i))
            else:
                d.text("{:.2}V".format(v/i))
        return v/i
    
    while(True):
        ba.display(0, 0)
        v1=dl()
        ba.display(255, 255)
        dl(v1)
        

discharge()
#discharge_with_backlight()
#test_voltage_drop()
