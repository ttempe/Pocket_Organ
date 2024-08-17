#     Hobbyist Steno Keyboard - MicroPython driver for a hobbyist steno machine (keyboard)
#     Copyright (C) 2023 Thomas TEMPE
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

#TODO:
# Send the console messages as strokes interpretable by Plover
# Add support for more protocols: Plover-HID, rollover keyboard
# Give calibration success/failure feedback to the user (through LED color codes?)
# Add a way of displaying the current protocol, and the current Bluetooth pairing partner
# Add 1st-hand-up support
# Add key repeat support
# Add a way to send parameters or commands from a Plover plug-in
# Measure power consumption. See if we can decrease it by toggling the Hall effect sensors on and off

import time, supervisor, array, os, json
import digitalio, analogio, board
import usb_cdc

#Keymap
#address  0  1  2  3  4  5  6  7  | 8  9  10  11  12  13  14  15 | 16  17  18  19  20  21  22  23 | 24 25 26 27 28 29 30 31
#Key      S- S- #  T- K- -  P- W- | A  H- R-  O   *   *   E   F- | -R  -U  -P  -B  -L  -G  -   -T | -S #  -D -Z

#index = address
__key_names = ["S1", "S2", "#", "T", "K", "-", "P", "W", "A", "H", "R", "O", "*1", "*2", "E", "F", "-R", "-U", "-P", "-B", "-L", "-G", "--", "-T", "-S", "#2", "-D", "-Z"]
__finger_spelling = {"a":["A", "#", "-P"]}
__gemini_codes = {"S":0x006000000000, "T":0x001000000000, "K":0x000800000000, "P":0x000400000000, "W":0x000200000000,
                  "H":0x000100000000, "R":0x000040000000, "A":0x000020000000, "O":0x000010000000, "#":0x3F000000007E,
                  "*":0x00000C300000, "E":0x000000080000, "U":0x000000040000,"-P":0x000000004000}

### Extract from Plover code:
# In the Gemini PR protocol, each packet consists of exactly six bytes
# and the most significant bit (MSB) of every byte is used exclusively
# to indicate whether that byte is the first byte of the packet
# (MSB=1) or one of the remaining five bytes of the packet (MSB=0). As
# such, there are really only seven bits of steno data in each packet
# byte. This is why the STENO_KEY_CHART below is visually presented as
# six rows of seven elements instead of six rows of eight elements.

#__protocol = [["N/A", "Num", "Num", | "Num", "Num", "Num", "Num"],
#              ["S-",  "S-",  "T-",  | "K-",  "P-",  "W-",  "H-" ],
#              ["R-",  "A",   "O-",  | "*",   "*",   "N/A", "N/A"],
#              ["N/A", "*",   "*",   | "E",   "U",   "-F",  "-R" ],
#              ["-P",  "-B",  "-L",  | "-G",  "-T",  "-S",  "-D" ],
#              ["Num", "Num", "Num", | "Num", "Num", "Num", "-Z" ]]


#Here is the same protocole, but with key addresses (see keymap above) instead
__protocol = [[ 28,  2,  2,  2,  2,  2,  2],
              [  0,  1,  3,  4,  6,  7,  9],
              [ 10,  8, 11, 12, 13, 28, 28],
              [ 28, 12, 13, 14, 17, 15, 16],
              [ 18, 19, 20, 21, 23, 24, 26],
              [  2,  2,  2,  2,  2,  2, 27]]

__hw_cal_file = "hardware_calibration.json"

def pinOut(p):
    ret = digitalio.DigitalInOut(p)
    ret.direction = digitalio.Direction.OUTPUT
    return ret

class Keys: 
    def __init__(self):
        #Pins
        self.muxA =   pinOut(board.GP0 )
        self.muxB =   pinOut(board.GP1)
        self.muxC =   pinOut(board.GP2)
        self.ADC = [analogio.AnalogIn(i) for i in [board.A0, board.A1]]
        #self.LED_act = pinOut(board.GP25)
        self.LED_cal = pinOut(board.GP24)
        self.SW_cal =  digitalio.DigitalInOut(board.GP19) #In
        self.SW_cal.pull = digitalio.Pull.UP
        
        #Buffers
        self.readings = array.array("I", (0 for i in range(32)))    #16-bit ADC reading
        self.output = array.array("B", (0 for i in range(32)))      # 8-bit normalized values
        self.prev_output = array.array("B", (0 for i in range(32))) # same
        self.serial = usb_cdc.data
        self.gemini_buffer = bytearray(6)

        #bitmap of currently pressed keys
        self.pressed = 0
        self.prev_pressed = 0
        self.stroke = 0
        
        #hardware calibration values (used for converting 16-bit readings to 8-bit values)
        try:
            fd = open(__hw_cal_file, "r")
            (self.zero, self.max) = json.load(fd)
            fd.close()
        except OSError:
            self.zero = [32913]*32 
            self.max =  [51227]*32
            
        #User calibration: thresholds for converting 8-bit values to pressed/release values (with hysteresis), between 0 (fully released) and 255 (fully pressed)
        self.thresh_h = [128]*32  
        self.thresh_l = [100]*32
        #bitmap of the addressable sensors that are actually used in the steno machine (1st mux, 1st sensor is 0b1)
        self.mask = 0b1101101111111111111111011111 
        self.l_mask = 0b111111111111                 #left hand
        self.r_mask = 0b1111111111111100000000000000 #right hand
        
    def set_address(self, mux):
            time.sleep(0.001) #TODO: does it work without?
            self.muxA.value = mux&1
            self.muxB.value = mux&2
            self.muxC.value = mux&4
            time.sleep(0.001) #TODO: reduce
            
    def read(self):
        "One loop of polling all the keys. Get the results in the object attributes. Returns whether there was a change in the 8-bit normalized readings"
        (self.prev_output, self.output) = (self.output, self.prev_output)
        changed = False
        self.prev_pressed = self.pressed
        #Read the 16-bit analog values and normalize them
        for i, mux in enumerate(range(8)):
            self.set_address(mux)
            for j, ADC in enumerate(self.ADC):
                addr=i+j*8
                if (self.mask >> addr) & 1:
                    #Read analog
                    self.readings[addr] = val = ADC.value
                    #Normalize
                    val = abs(val-self.zero[addr])*255//max(1, abs(self.max[addr]-self.zero[addr]))
                    self.output[addr] = val = min(255, max(0, val))
                    changed += (val != self.prev_output[addr])
                    #Threshold (with hysteresis)
                    if val > self.thresh_h[addr] and not((self.pressed>>addr)&1):
                        self.pressed |= 1<<addr
                    elif val < self.thresh_l[addr] and (self.pressed>>addr)&1:
                        self.pressed -= 1<<addr
        return self.pressed != self.prev_pressed


def monitor_readings2(list=None, divisor=1):
    "Real-time display of the 32 readings (raw sensor data), for display with Thonny's View->Plotter feature"
    while True:
        k.read()
        if list:
            print([k.readings[l]//divisor for l in list])
        else:                  
            print([v//divisor for v in k.readings])
        time.sleep(.02) 

def monitor_readings(list=None, divisor=1):
    "Real-time display of the 32 readings (raw sensor data), for display with Thonny's View->Plotter feature"
    while True:
        v = []
        for l in list:
            k.set_address(l)
            k.ADC[0].value
            time.sleep(0.001)
            v.append(k.ADC[0].value//divisor)
        print(v)
        time.sleep(.02) 

def monitor_readings_voltage(list=None, divisor=1):
    "Real-time display of the 32 readings (raw sensor data), for display with Thonny's View->Plotter feature"
    while True:
        v = []
        for l in list:
            k.set_address(l)
            k.ADC[0].value
            time.sleep(0.001)
            v.append(3.3*k.ADC[0].value/65535)
        print(v)
        time.sleep(.02) 


def monitor_switch(list, divisor=1):
    while True:
        for l in list:
            k.set_address(l)
            for i in range(10):
                print(k.ADC[0].value)
                time.sleep(0.1)
        time.sleep(0.5)

            

def monitor_readings_percents(list=None):
    "Real-time display of the 32 readings (raw sensor data), for display with Thonny's View->Plotter feature"
    while True:
        k.read()
        if list:
            print([int(k.readings[l]*100/65535) for l in list])
        else:                  
            print([int(v*100/65535) for v in k.readings])
        time.sleep(.1) 


#Calculate the average values, for use in histogram() 
def avg_values(sensors, divisor=1, duration=5):
    t0 = time.time()
    val = [0]*len(sensors)
    count = 0
    while time.time()-t0<duration:
        for i, v in enumerate(val):
            k.set_address(sensors[i])
            val[i] += k.ADC[0].value
        count+=1

    for i, v in enumerate(val):
        val[i] = v//count//divisor
    print(val)
        
#calculate the standard deviation on each sensor
def histogram(sensors, divisor, spread, avg_values=None, duration=2):
    t0 = time.time()
    hist = [[0]*spread for i in range(len(sensors))]
    if avg_values == None:
        avg_values = [0]*len(sensors)
    #Collect
    while time.time()-t0<duration:
        for i, sensor in enumerate(sensors):
            k.set_address(sensor)
            val = min(max(k.ADC[0].value//divisor-avg_values[i]+spread//2,0), spread//2-1)
            hist[i][val]+=1    
    #Print
    print("sensor, count, avg, stdev, underrun, overrun, spread, #values")
    print(sensors)
    for sensor in range(len(sensors)):
        avg = sum([i*v for i,v in enumerate(hist[sensor])])/sum(hist[sensor])
        stdev = sum([v*abs(i-avg) for i,v in enumerate(hist[sensor])])/sum(hist[sensor])
        vmin = spread
        vmax = 0
        for i, v in enumerate(hist[sensor]):
            if v!=0:
                vmin=min(vmin, i)
                vmax=max(vmax, i)
        print(sensor, ",", sum(hist[sensor]), ",", avg+avg_values[sensor]-spread//2, ",", stdev, ",", hist[sensor][0], ",", hist[sensor][-1], vmax-vmin)#, ",".join([str(i) for i in hist[sensor]]))
 

def minmax():
    """Loop read the keyboard, and display the 32 highest and lowest values identified so far.
    Use it to gauge the level of noise (don't move any keys), or for calibration (press down each key fully)
    """
    min_val = array.array("I", (65535 for i in range(32)))
    max_val = array.array("I", (0 for i in range(32)))
    last_time = 0
    while True:
        k.read()
        for i, v in enumerate(k.readings):
            max_val[i]=max(v, max_val[i])
            min_val[i]=min(v, min_val[i])
        if (supervisor.ticks_ms() - last_time > 1000):
            last_time = supervisor.ticks_ms()
            print("Min: ", min_val)
            print("Max: ", max_val)
            time.sleep(.05)
                    
def read_one(mux, input):
    "Gives the measured voltage for one sensor"
    k.set_address(input)
    print("S{}-{} : {:.3} V".format(mux, input, k.ADC[mux].value*3.3/65535)) 

def time_once():
    "How many microseconds to poll once?"
    t=supervisor.ticks_us()
    k.read()
    print("Polling once takes", supervisor.ticks_us()-t, "us")

def noise():
    "Generate PWM output to produce electrical noise on the board"
    import pwmio
    pwmio.PWMOut(board.GP3, frequency=5000, duty_cycle=32768)
    pwmio.PWMOut(board.GP25, frequency=5000, duty_cycle=32768)

def test_spike():
    k.set_address(4)
    counters = [0,0]
    while True:
        for i in range(10000):
            print(k.ADC[0].value//(2^10));time.sleep(0.1)
            counters[ (k.ADC[0].value//(2^20))>4750]+=1
        print(counters)
noise()

k = Keys()
#avg_values([0,1,2,3, 4, 5, 6, 7], 2^7)
#histogram([0,1,2,3, 4, 5, 6, 7], 2^7, 200, [6795, 7045, 6537, 6716, 6748, 6702, 6837, 6584], 2)
#monitor_readings([4,7], 2^10)
#monitor_switch([4,7], 2^10)
#test_spike()
monitor_readings_voltage([0, 1, 2, 3, 4, 5, 6, 7], 2^7)
#monitor_readings([0, 1, 2, 3, 4, 5, 6, 7], 2^7)
#monitor_readings([0, 1, 2, 3, 4, 6, 7], 2^10)
#monitor_readings([8, 9, 10, 11, 12, 13, 14, 15], 2^7)
#k.loop()
