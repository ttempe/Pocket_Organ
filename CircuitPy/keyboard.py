import time
from board_po import keyb_map, key_vol, key_loop, key_instr, key_capo, keyb_muxA, keyb_muxB, keyb_muxC, keyb_ADC, keyb_min, keyb_max
import micropython

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
        self.keymap = [keyb_map.index(i) for i in range(16)]#pre-compute the reverse map once for faster reading
        self.bitmap = 0 #binary map of button press states
        self.current_note_key = None
        self.current_note_level = None
        self.mode = chord
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
    def _read_addr(self, addr):
        "For calibration"
        keyb_muxA.value = addr&0x8
        keyb_muxB.value = addr&0x4
        keyb_muxC.value = addr&0x2
        #time.sleep(0.001)
        keyb_ADC[addr&0x1].value
        return keyb_ADC[addr&0x1].value

    def _read(self):
        "Read all values"
        self.bitmap=0
        for i in range(8):
            keyb_muxA.value = i&0x4
            keyb_muxB.value = i&0x2
            keyb_muxC.value = i&0x1
            for j in range(2):
                addr=self.keymap[(i<<1)+j]
                self.notes_val[addr] = r = max(0, min(127,127-(((keyb_ADC[j].value-keyb_min[(i<<1)+j])<<7)//keyb_max[(i<<1)+j])))
                self.bitmap |= (r>0)<<addr #Min value: 0

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
        

        self.volume = not(key_vol.value)
        self.looper = not(key_loop.value)
        self.instr  = not(key_instr.value)
        self.capo   = not(key_capo.value)

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


def calibrate(threshold = 10):
    "Press each key all the way down in turn, then copy-paste the output into board_po.py, variables keyb_min and keyb_max"
    "threshold = value (out of 127) below which the keypress is not registered"
    k = Keyboard()
    vmin = [66000]*16
    vmax = [1] * 16
    while True:
        for i in range(16):
            r = k._read_addr(i)
            vmax[i] = max(r, vmax[i])            
            vmin[i] = min(r, vmin[i])
        #print("keyb_min2=",[vmin[i]-threshold*127//(vmax[i]-vmin[i]+1) for i in range(16)], ";keyb_max=",[vmax[i]-vmin[i] for i in range(16)])
        print("keyb_min=",[vmin[i] for i in range(16)], ";keyb_max=",[int((vmax[i]-vmin[i])*(1-threshold/127)) for i in range(16)])
        time.sleep(0.2)

def monitor_readings(val = range(14), bits=16):
    "Print raw 16-bit values for all [listed] keys in order"
    k = Keyboard()
    while True:
        print([k._read_addr(keyb_map[i])>>(16-bits) for i in val])
        time.sleep(0.1)

def monitor_readings_no_keymap(addr, bits=16):
    "Print raw 16-bit values for both ADCs on the specified MUX address (0~7)"
    k = Keyboard()
    keyb_muxA.value = addr&0x4
    keyb_muxB.value = addr&0x2
    keyb_muxC.value = addr&0x1
    time.sleep(0.001)
    while True:
        print(keyb_ADC[0].value, keyb_ADC[1].value)
        time.sleep(0.1)


def monitor_values(val = range(14)):
    "Print the 7-bit reading after calibration for all keys"
    k = Keyboard()
    while True:
        k.loop()
        print([k.notes_val[i] for i in val], k.current_note_key)
        #print([v for i, v in bits(i)])
        time.sleep(.1)

def monitor_status():
    "Print the status (pressed/released) for each key"
    k = Keyboard()
    while True:
        k.loop()
        print([v for i, v in bits(k.bitmap, 14)])
        time.sleep(.1)

#end
