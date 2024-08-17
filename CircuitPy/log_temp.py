import keyboard, analogio
from time import sleep
from board_po import keyb_map
import microcontroller
import display

k = keyboard.Keyboard()
d = display.Display()

def log():
    "Save the values every minute in a log file"
    while True:
        v = [k._read_addr(keyb_map[i]) for i in range(14)]
        temp = microcontroller.cpu.temperature
        fd = open("cal_log.csv", "a")
        fd.write("{},".format(temp))
        for i in v:
            fd.write("{},".format(i))
        fd.write("\n")
        fd.close()

        sleep(60)

def disp():
    "Display all 14 raw values on the OLED screen"
    while True:
        v = [k._read_addr(keyb_map[i]) for i in range(14)]
        d.disp.fill(0)
        for i in range(8):
            d.disp.text("{}:{}".format(i, v[i]/100), 0,i*8,1)
        for i in range(8, 14):
            d.disp.text("{}:{}".format(i, v[i]/100), 64,(i-8)*8,1)
        d.disp.show()
        sleep(0.5)        

def collect():
    return [k._read_addr(keyb_map[i]) for i in range(14)]

disp()