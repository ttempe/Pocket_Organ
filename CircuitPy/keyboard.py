import time, array
import board_po as board
import mux
import micropython

#TODO:
# * Measure in low/high temperature environment, determine need to re-calibrate

chord  = micropython.const(0)
melody = micropython.const(1)
drum   = micropython.const(2)
drum   = micropython.const(2)
expr_bend_up   = micropython.const(13)

keys_sharp = [1, 2, None, 4, 5, 6, None, None]
keys_flat  = [None, 0, 1, None, 3, 4, 5, None]
key_levels = [0, 2, 4, 5, 7, 9, 11, 12]
key_expr_up   = [3, 3, 3, 7, 7, 7, 7, 0]
key_expr_down = [7, 7, 7, 0, 0, 0, 0, 3]

def bits(n, nb=8): 
    "8-bit bit map iterator"
    for i in range(nb):
        yield i, (n>>i)&1
            
class Keyboard:
    """
    This is the abstraction layer responsible for collecting all user input,
    including key mapping.
    """
    def __init__(self):
        self.notes_val = bytearray(16) #analog values
        self.notes_val_old = bytearray(16) #analog value
#        self.notes = bytearray(8) #binary output #Replaced by self.pressed()
        #NOTE: Some of the state variables are created on the 1st execution of self.loop() and not mentioned here
        self.keymap = [board.keyb_map.index(i) for i in range(16)]#pre-compute the reverse map once for faster reading
        self.bitmap = 0 #binary map of button press states
        self.current_note_key = None
        self.current_note_level = None
        self.mode = chord
        self._v = array.array('l', (0 for _ in range(16))) #pre-allocation, for storing intermediary sensor readings
        #self._re_calibrate()
        self.loop()

    def pressed(self, key):
        "Returns whether the corresponding key index has been pressed"
        #Replaces self.notes[]
        return None if None == key else (self.bitmap>>key) & 1

#     def current_note_key_level(self):
#         """Returns a number from 0 to 12 (nb of semi-tones from C)
#         depending on note keys pressed. (C=0; C#=1; D=2...)
#         Returns None if no key pressed
#         2nd parameter indicates whether the level is a combination of 2 keys
#         """
#         #TODO: is this how we want to do sharps?
#         if self.current_note_key != None:
#             d = 0
#             if self.current_note_key>0 and self.pressed(self.current_note_key-1):
#                 d=-1
#             elif self.current_note_key<7 and self.pressed(self.current_note_key+1):
#                 d=1
#             return (key_levels[self.current_note_key]+d)%12, bool(d)
#         return None, None

    def _read(self):
        "Read all values"
        self.bitmap=0
        mux.power_on()

        #Read all the sensor values.
        for i in range(8):
            # Set address
            mux.set_addr(i*2)
            time.sleep(0.00001)#let it settle, 10us
            # Read both ADCs
            for adc_num in range(2):
                adc = board.keyb_ADC[adc_num]
                val = abs(((adc.value+adc.value+adc.value+adc.value)>>2)-32768)
                self._v[i*2 + adc_num] = ((val-board.keyb_min[i*2 + adc_num])*127)//board.keyb_range[i*2 + adc_num] 

        #and finalize calculation
        for i in range(16):
            addr=self.keymap[i]
            self.notes_val[addr] = r = max(0, min(127,self._v[i]))
            self.bitmap |= (r>(0 if (self.bitmap&addr) else 5))<<addr #incl. hysteresis

        mux.power_off()

    def _re_calibrate(self, count = 30):
        """Poll each key multiple times, to check their current range in a rested state, and fine-tune the calibration imported from board_po accordingly.
        Assumes all analog keys are released.
        Each iteration takes ~1ms. Only suitable for initial fine-tuning of the calibration when powered on."""
        return #TODO: update
        vmin = [66000]*16
        for c in range(count):
            for i in range(16):
                r = mux.read_addr(i)
                vmin[i] = min(r, vmin[i])
        for i in range(16):
            ##TODO：if one key is off, ignore it.
            keyb_max[i] = vmin[i]-200 ##TODO: This is grossly arbitrary

    def loop(self):
        self.notes_val, self.notes_val_old = self.notes_val_old, self.notes_val
        self.bitmap_old = self.bitmap

        self._read()

        self.sharp   = self.pressed(12)
        self.seventh = self.pressed(10)
        self.fifth   = self.pressed( 9)
        self.third   = self.pressed( 8)
        self.minor   = self.pressed(13)
        self.shift   = self.pressed(11)
        self.up 	 = self.minor
        self.down 	 = self.sharp
        

        self.volume = not(board.key_vol.value)
        self.looper = not(board.key_loop.value)
        self.instr  = not(board.key_instr.value)
        self.capo   = not(board.key_capo.value)

        #Change mode?
        if self.shift and (self.third ^ self.fifth ^ self.seventh):
            if self.third and (self.mode != chord):
                self.mode=chord
            elif self.fifth and (self.mode != melody):
                self.mode = melody
            elif self.seventh and (self.mode != drum):
                self.mode = drum

        #is there a key being pressed right now?
        if self.current_note_key!=None:
            if not self.pressed(self.current_note_key):
                self.current_note_key = None
        if None == self.current_note_key:
            for i, n in bits(self.bitmap):
                if n:
                    self.current_note_key = i
#                    self.current_key_level = key_levels[self.current_note_key] + 1 * self.shift #Todo: re-enable below code
                    break
                        
        #is there a combination of 2 keys being pressed right now? (Sharp/flat)
        #(honors the precedence of "1st key pressed")
        if self.current_note_key != None:
            self.current_key_level = key_levels[self.current_note_key]
            if self.sharp:
                self.current_key_level+=1
            elif (keys_sharp[self.current_note_key] != None):
                self.current_key_level += self.pressed(keys_sharp[self.current_note_key])
            if keys_flat[self.current_note_key] != None:
                self.current_key_level -= self.pressed(keys_flat[self.current_note_key])
            self.key_expr_up   = self.notes_val[key_expr_up[  self.current_note_key]]
            self.key_expr_down = self.notes_val[key_expr_down[self.current_note_key]]
        else:
           self.current_key_level = None

#         #Update the strum keys status
#         b = self.uc3.button
#         self.strum_keys=0
#         for n, k in enumerate(board.keyboard_strum_keys):
#             self.strum_keys += self.uc3.button(k)<<n
            
#         #Strumming comb as an analog slider
#         n, t = 0, 0
#         for i in range(len(board.keyboard_strum_keys)):
#             n += (self.strum_keys >> i)&1
#             t += ((self.strum_keys >> i)&1) * i
#             self.slider_val = int( t / n * 127 / len(board.keyboard_strum_keys) ) if n else None
        
#     def disp(self):#for calibration
#         notes_thres = 0
#         while(True):
#             for note, button in enumerate(board.keyboard_note_keys):
#                 a = self.notes_ref[note] - self.uc1.read_analog(button)
#                 print(a, ",", end="")
#             print("")
#             time.sleep(0.200)


def calibrate(threshold=5):
    """
    Press each key all the way down in turn, then copy-paste the output into board_po.py, variables keyb_min, keyb_range
    Suited for manual calibration of each instrument.
    threshold = value (out of 127) below which the keypress is not registered.
    """

    k = Keyboard()
    vmin    = [0] * 16  # highest value of unpressed keys
    vmax    = [0] * 16

    print("Starting calibration.\nPlease don't press the keys, reading the background noise level.")
    #We have quite a bit of jitter in the readings. Compensate for that by first sampling some unpressed values, and using the lower bound as a threshold.
    for n in range(20):
        print(".", end="")
        for nn in range(200):
            for i in range(16):
                #Measure the maximum value 
                vi = abs(mux.read_addr(i)-32768)
                vmin[i] = max(vi, vmin[i]) #see how high it goes at rest. We'll add a bit of buffer later.

        
    print("\nThank you.\nNow press each key all the way down. Press hard, and hold for a short moment.")
    while True:
        for n in range(500):
            for i in range(16):
                vi = abs(mux.read_addr(i)-32768)
                vmax[i] = max(vi, vmax[i]) #if the key is pressed deeper than previous readings
        
        # Output calibration data in one line
        vmin_t = [vmin[i]+(vmax[i]-vmin[i])*threshold//127 for i in range(16)] #Add threshold
        keyb_range = [max(1,int(vmax[i] - vmin_t[i])) for i in range(16)] #don't let it be zero
        print(f"keyb_range={keyb_range}; keyb_min={vmin_t}")
        time.sleep(0.1)


def monitor_readings(val = range(14), bits=16):
    "Print raw 16-bit values for all [listed] keys in order"
    k = Keyboard()
    while True:
        print([abs(mux.read_addr(k.keymap[i])-32768)>>(16-bits) for i in val])
        time.sleep(0.1)

def monitor_readings_no_keymap(addr, bits=16):
    "Print raw 16-bit values for both ADCs on the specified MUX address (0~7)"
    k = Keyboard()
    time.sleep(0.001)
    while True:
        print(abs(mux.read_addr(addr)-32768))
        time.sleep(0.1)


def monitor_values(val = range(14)):
    "Print the 7-bit reading after calibration for all keys"
    k = Keyboard()
    while True:
        k.loop()
        print([k.notes_val[i] for i in val])
        #print([v for i, v in bits(i)])
        time.sleep(.1)

def monitor_status():
    "Print the status (pressed/released) for each key"
    k = Keyboard()
    while True:
        k.loop()
        print([v for i, v in bits(k.bitmap, 14)])
        time.sleep(.1)

def monitor_status_with_names():
    "Print the status (pressed/released) for each key with names"
    k = Keyboard()
    while True:
        k.loop()
        print([board.key_names[i] for i in range(14) if bits(k.bitmap, i)])
        time.sleep(.5)

def test_power_settle():
    """Measure how long the ADC signal takes to stabilize after hall power-on.
    2026-06-28 test on V31: settling time is less that the time to read the 1st sample"""

    readings = [0]*100
    mux.power_off()
    time.sleep(0.2)
    r0, r1, r2, r3 = 0, 0, 0, 0 # Unroll the loop to go faster
    mux.power_on()
    adc = board.keyb_ADC[0]    
    start = time.monotonic_ns()
    mux.set_addr(0)
    r0= adc.value 
    r1= adc.value 
    r2= adc.value 
    r3= adc.value 
    for i in range(100):
        readings[i] = adc.value
    
    print("Total sampling time: ", time.monotonic_ns() - start)
    print(r0, "\n", r1, "\n", r2, "\n", r3)
    for i in readings:
        print(i)

#end
