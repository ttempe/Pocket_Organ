import AT42QT1110
import time
import board

#TODO:
# * force a recalibration when switching between USB and battery power (instead of when pressing the Volume key)
# * clean up and debug slider code. Make sure it doesn't fly around while lifting the finger.
# * Synchronize the main loop with the uc1 acquisition cycle
# * Cleanup: use board.py variables directly rather than copying them into class Keyboard.

##For calibration when the USB cable is unplugged:
#import display;d=display.Display();

keys_sharp = [1, 2, None, 4, 5, 6, None, None]
keys_flat  = [None, 0, 1, None, 3, 4, 5, None]
key_levels = [0, 2, 4, 5, 7, 9, 11, 12]
key_expr_up   = [3, 3, 3, 7, 7, 7, 7, 0]
key_expr_down = [7, 7, 7, 0, 0, 0, 0, 3]


class Keyboard:
    """
    This is the abstraction layer responsible for collecting all user input,
    including key mapping.
    """
    def __init__(self):
        self.melody_led = board.keyboard_melody_led
        self.melody_led(1)

        #Reminder: on V17, Touch_trigger is not connected on uc2 and uc3
        self.uc1 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc1_cs)
        self.uc2 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc2_cs)
        self.uc3 = AT42QT1110.AT42QT1110(board.keyboard_spi, board.keyboard_uc3_cs)
        
        self.instr_pin = board.keyboard_instr_pin
        self.looper_pin = board.keyboard_looper_pin
        self.drum_pin = board.keyboard_drum_pin
        self.melody_lock = False
        self.drum = False
        self.notes = bytearray(8) #binary output
        self.notes_old = bytearray(8)
        self.notes_val = bytearray(8) #analog value
        self.notes_val_old = bytearray(8) #analog value
        self.notes_ref = [0]*8 #reference value from unpressed key (from calibration)
        self.volume = False
        self.volume_old = False
        self.slider_val =  127 #value from 0 to 127
        self.current_note_key = None
        self.current_note_level = None
        time.sleep_ms(100)
        self.calibrate()
        self.loop()
        self.melody_led(0)
        self.strum_keys = 0 #Bytearray
                
    def calibrate(self):
        if board.verbose:
            print("Recalibrating keyboard")
        self.uc1.recalibrate_all_keys()
        self.uc2.recalibrate_all_keys()
        self.uc3.recalibrate_all_keys()
        for note, button in enumerate(board.keyboard_note_keys):
            self.notes_ref[note] = self.uc1.read_analog(button)

    #TODO: Clean up from pocket_organ. Redundant with self.current_key_level
    def current_note_key_level(self):
        """Returns a number from 0 to 12 (nb of semi-tones from C)
        depending on note keys pressed. (C=0; C#=1; D=2...)
        Returns None if no key pressed
        2nd parameter indicates whether the level is a combination of 2 keys
        """
        if self.current_note_key != None:
            d = 0
            if self.current_note_key>0 and self.notes[self.current_note_key-1]:
                d=-1
            elif self.current_note_key<7 and self.notes[self.current_note_key+1]:
                d=1
            return (key_levels[self.current_note_key]+d)%12, bool(d)
        return None, None

    def read_analog_keys(self):
        """
        1. read analog value
        2. substract it from the reference (the highest possible reading, obtained during auto-calibration when the key is at rest and updated automatically below)
        3. substract values from the crosstalk matrix (eg: key n. 3 is significantly affected by key n. 2's reading) (cross talk matrix is specific to each board revision)
        4. determine the binary (pressed/depressed) value by comparing with that key's threshold (=max * a coefficient) and adding a little histeresis from the previous reading.
        5. if pressed, calculate an analog key value between 0 and 127 based on each key's maximum theoretical reading
        """
        analog = []
        all_keys_min = 0
        for note, button in enumerate(board.keyboard_note_keys):
            v = self.notes_ref[note]-self.uc1.read_analog(button)
            if v<0: #adjust calibration
                if board.verbose:
                    print("keyboard calibration: adjusting {} by {}".format(note, v))
                self.notes_ref[note] -= v
                v=0
            analog.append(v)
            
        #Correct crosstalk between keys
        ####For calibration of keyboard_crosstalk (apply first) and keyboard_notes_max (do next) in board.py
        #time.sleep_ms(100);print("\n\nBefore: ", analog,"\nMax: ", list(board.keyboard_notes_max),"\nAfter: ", end="")
        ####For calibration when the USB cable is unplugged:
        #d.disp.show();d.disp.fill(0);time.sleep_ms(200);i=0        
        for note1 in range(len(self.notes)):
            v = analog[note1]
            if board.keyboard_crosstalk:
                for note2 in range(len(self.notes)):
                    v -= analog[note1]*board.keyboard_crosstalk[note2][note1]
            ####For calibration
            #print(int(v), ", ", end="")
            ####For calibration when the USB cable is unplugged:
            #d.disp.text(str(v),0,8*i);i+=1
            
            self.notes[note1] = ( v >= board.keyboard_notes_max[note]/10 + (0 if self.notes[note] else 2) ) #add a little hysteresis            
            self.notes_val[note1] = int(max(0, min(v - board.keyboard_notes_max[note]*.15, board.keyboard_notes_max[note]))/board.keyboard_notes_max[note]*127) if self.notes[note1] else 0
            all_keys_min = min( all_keys_min, v)

        if all_keys_min > 1:
            #all keys have drifted up. Let's adjust the calibration
            for note in range(len(self.notes)):
                self.notes_ref[note] -= all_keys_min
            if board.verbose:
                print("keyboard calibration: adjusted all keys by {}. New values: {}".format(all_keys_ref, self.notes_ref))

    def loop(self):
        
        self.notes_old = self.notes[:]
        self.notes_val_old = self.notes_val[:]
        self.drum_old  = self.drum

        self.uc1.loop()
        self.uc2.loop()
        self.uc3.loop()        
        
        self.seventh = self.uc2.button(board.keyboard_uc2_seventh)
        self.fifth   = self.uc2.button(board.keyboard_uc2_fifth)
        self.third   = self.uc2.button(board.keyboard_uc2_third)
        self.minor   = self.uc2.button(board.keyboard_uc2_minor)
        self.shift   = self.uc2.button(board.keyboard_uc2_shift)

        self.volume = sum([ self.uc2.button(i) for i in board.keyboard_slider_keys])
        self.volume_old = self.volume
        self.instr  = not(self.instr_pin())
        self.looper = not(self.looper_pin())
        self.capo   = not(board.keyboard_capo_pin())
        
        #Play mode: Melody, chords, drum
        #TODO: replace with a condition that the Drum key is defined in board.py
        if 20 == board.version:
            if self.shift:
                if self.seventh: #Pressed the "Drum" button
                    self.drum = True
                    self.melody_lock = False
                elif self.fifth: #Pressed the "Melody" button
                    self.drum = False
                    self.melody_lock = True
                elif self.third:      #Pressed the "Chords" button
                    self.drum = False
                    self.melody_lock = False                    
        else:
            self.drum = not(self.drum_pin())        
            if self.drum_old and not self.drum and self.shift:
                self.melody_lock=True
            elif self.drum and self.melody_lock:
                self.melody_lock=False
            self.melody_led(self.shift)

        self.read_analog_keys()

        #Re-calibrate the touch keys on "Volume" press
        #if self.volume and not self.volume_old:
        #    self.calibrate()
            

        #is there a key being pressed right now?
        if self.current_note_key!=None:
            if not self.notes[self.current_note_key]:
                self.current_note_key = None
        if None == self.current_note_key:
            for i, n in enumerate(self.notes):
                if n:
                    self.current_note_key = i
                    break
                
        self.strum_mute = (None == self.current_note_key) 
        
        #is there a combination of 2 keys being pressed right now? (Sharp/flat)
        #(honors the precedence of "1st key pressed")
        if self.current_note_key != None:
            self.current_key_level = key_levels[self.current_note_key]
            if keys_sharp[self.current_note_key] != None:
                self.current_key_level += self.notes[keys_sharp[self.current_note_key]]
            if keys_flat[self.current_note_key] != None:
                self.current_key_level -= self.notes[keys_flat[self.current_note_key]]
            self.key_expr_up   = self.notes_val[key_expr_up[  self.current_note_key]]
            self.key_expr_down = self.notes_val[key_expr_down[self.current_note_key]]
        else:
            self.current_key_level = None

        #Update the strum keys status
        b = self.uc3.button
        self.strum_keys=0
        for n, k in enumerate(board.keyboard_strum_keys):
            self.strum_keys += self.uc3.button(k)<<n
            
        #Strumming comb as an analog slider
        n, t = 0, 0
        for i in range(len(board.keyboard_strum_keys)):
            n += (self.strum_keys >> i)&1
            t += ((self.strum_keys >> i)&1) * i
            self.slider_val = int( t / n * 127 / len(board.keyboard_strum_keys) ) if n else None
        
    def disp(self):#for calibration
        notes_thres = 0
        while(True):
            for note, button in enumerate(board.keyboard_note_keys):
                a = self.notes_ref[note] - self.uc1.read_analog(button)
                print(a, ",", end="")
            print("")
            time.sleep_ms(200)


#end
