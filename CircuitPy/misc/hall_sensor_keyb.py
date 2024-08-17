#This module drives the 14 analog keys with Hall effect sensors.
#The keys are multiplexed (address is set through mux_A, _B, and _C)
#and readings are collected through two ADCs.
#
# Key order is:
# 0~7: the note keys (C, D, E.. CC)
# 8~13: the left-hand keys (left to right, top to bottom)
#
# The magnets must be installed in the right direction (pressing down the key lowers the reading)

from board_po import keyb_muxA, keyb_muxB, keyb_muxC, keyb_ADC, keyb_min, keyb_max, keyb_map
import time, supervisor

class Keyb:
    def __init__(self):
        self.values = bytearray(16) #analog values
        self.map = [keyb_map.index(i) for i in range(16)]#compute reverse map once for faster reading in loop()
        self.bitmap = 0#of button press states
    
    def _read_addr(self, addr):
        keyb_muxA.value = addr&0x8
        keyb_muxB.value = addr&0x4
        keyb_muxC.value = addr&0x2
        #time.sleep(0.001)
        keyb_ADC[addr&0x1].value
        return keyb_ADC[addr&0x1].value
    
    def read_val(self, key):
        "Return an 8-bit reading"
        addr = keyb_map[key]
        return max(0, min(255,255-(((self._read_addr(addr)-keyb_min[addr])<<8)//keyb_max[addr])))

    def loop0(self):
        "Read all values -- naïve"
        self.bitmap = 0
        for i in range(16):
            self.values[i] = self.read_val(i)
            self.bitmap |= (self.values[i]>64)<<i

    def loop(self):
        "Read all values -- optimized"
        self.bitmap=0
        for i in range(8):
            keyb_muxA.value = i&0x4
            keyb_muxB.value = i&0x2
            keyb_muxC.value = i&0x1
            for j in range(2):
                addr=self.map[(i<<1)+j]
                self.values[addr] = max(0, min(255,255-(((keyb_ADC[j].value-keyb_min[addr])<<8)//keyb_max[addr])))
                self.bitmap |= (self.values[i]>64)<<i
            

def monitor_readings(val = range(14)):
    "Print raw 16-bit values for all [listed] keys in order"
    k = Keyb()
    while True:
        print([k._read_addr(keyb_map[i]) for i in val])
        time.sleep(0.1)

def monitor_values(val = range(14)):
    "Print the 8-bit values from all [listed] keys, after calibration and in order"
    k = Keyb()
    while True:
        print([k.read_val(i) for i in val])
        time.sleep(0.1)

def calibrate():
    "Press each key all the way down in turn, then copy-paste the output into board_po.py, variables keyb_min and keyb_max"
    k = Keyb()
    vmin = [66000]*16
    vmax = [0] * 16
    while True:
        for i in range(16):
            r = k._read_addr(i)
            vmin[i] = min(r, vmin[i])
            vmax[i] = max(r, vmax[i])
        print("keyb_min=",vmin, ";keyb_max=",[vmax[i]-vmin[i] for i in range(16)])
        time.sleep(0.1)

def test_loop():
    k = Keyb()
    while True:
        t0=supervisor.ticks_ms()
        k.loop0()
        #print([k.values[i] for i in range(14)])
        #print("{0:b}".format(k.bitmap))
        #Timing measurement
        k.loop0();k.loop0();k.loop0();k.loop0();k.loop0();k.loop0();k.loop0();k.loop0();k.loop0();print("{}ms/run".format((supervisor.ticks_ms()-t0)/10))
        time.sleep(0.1)
