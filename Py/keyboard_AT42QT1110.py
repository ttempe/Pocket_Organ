import AT42QT1110
import time
import board

#TODO:
# * force a recalibration when switching between USB and battery power (instead of when pressing the Volume key)
# * clean up slider code
# * check the analog measurements for slight drift of all the values while none of the keys are being pressed
# * Synchronize the main loop with the uc1 acquisition cycle
# * Decrease the sensitivity of the key below when the key above is detected? (finger shadow)

class Slider:
    "Driver for a capacitive slider made of multiple electrodes. The 1st electrode is connected to the last."
    
    def __init__(self, uc, electrodes, sensitivity, repeat=False):
        """
        'electrodes' is a list of the electrode numbers from touch sensor 'uc' to be used by this slider
        'sensitivity' is the maximum expected deviation in the value of each corresponding electrode, when naturally sliding a finger over it.
        'repeat' indicates whether the last electrode is repeated at the end of the slider (in a 1/2/3/1 manner).
        """
        self.uc = uc
        self.electrodes = electrodes
        self.repeat = bool(repeat)
        self.sens   = sensitivity                #List of expected max deviation for each electrode
        self.count  = len(electrodes)+bool(self.repeat)
        self.thres  = [0]*len(electrodes)        #Reference value, after calibration
        if self.repeat:
            self.sens.append(self.sens[0])
        self.calibrate()

    def sensitivity_detect(self):
        """
        to be called manually during hardware development. Evenly swipe a finger over the slider, and it will
        display the corresponding "sensitivity" values.
        Values need to be updated every time a new hardware iteration modifies the routing around the touch IC
        or electrodes.
        """
        vmin = [2048]*len(self.electrodes)
        vmax = [0]*len(self.electrodes)
        while True:
            for i, e in enumerate(self.electrodes):
                v = self.uc.read_analog(e)
                vmin[i]=min(vmin[i],v)
                vmax[i]=max(vmax[i],v)
                print(vmax[i]-vmin[i], end=",")
            print("")
            time.sleep_ms(200)        

    def calibrate(self):
        for i, e in enumerate(self.electrodes):
            self.thres[i] = self.uc.read_threshold(e)
        if self.repeat:
            self.thres[-1]=self.thres[0]        

    def read(self):
        values = [0]*self.count     #For storing intermediary results
                                    #Fully pressed: ~127; fully released: ~0
        touch = 0
        #Get a relative reading for each electrode, between 0 and 127
        for i, e in enumerate(self.electrodes):
            if self.uc.button(e):
                touch+=1
        if touch:
            for i, e in enumerate(self.electrodes):
                #if self.uc.button(e):
                r = self.uc.read_analog(e)
                values[i] = min(((self.thres[i] - r)*127)//(self.sens[i]),127)
                #print("r", r, "; thres", self.thres[i], "; min", (self.thres[i] - r)*127, "; sens", self.sens[i], "; //", ((self.thres[i] - r)*127)//(self.sens[i]),"; value", values[i])
            if self.repeat:
                values[-1]=values[0]
            v_sum = []
            for e in range(self.count-1):
                v_sum.append(values[e]+values[e+1])
            #Find the value with the highest reading
            highest_val, highest = max( (v, i) for i, v in enumerate(v_sum) )
            #print("Highest point is between electrodes", highest, "and", highest+1, "value", highest)
            if highest_val<60:
                #none of the key is pressed hard enough. Reading will be very fragile. Ignore
                return None
            else:
                slice = 127//(self.count-1)
                res = highest*slice
                res += int(slice*(values[highest+1]/(values[highest]+values[highest+1])))#interpolate
                #print(0, 127, slice, highest*slice, res, highest_val)
                return min(res, 127)
        else:
            return None

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

        self.vol_slider = Slider( self.uc2, [2, 3, 4, 5], [24,23,8,24], True)

        self.volume_pin = board.keyboard_volume_pin
        self.instr_pin = board.keyboard_instr_pin
        self.looper_pin = board.keyboard_looper_pin
        self.drum_pin = board.keyboard_drum_pin

        self.notes = bytearray(8) #binary output
        self.notes_old = bytearray(8)
        self.notes_val = bytearray(8) #analog value
        self.notes_val_old = bytearray(8) #analog value
        self.notes_ref = [0]*8 #reference value from unpressed key (from calibration)
        self.notes_thres = 9 #above this value, assume the key is pressed
        self.notes_max = 40  #highest possible analog value
        self.volume = False
        self.volume_old = False
        self.volume_val =  64 #value from 0 to 100
        self.sharp = False
        self.current_note_key = None
        time.sleep_ms(20)
        self.calibrate()
        self.loop()
        self.melody_led(0)
        self.strum_mute = False
        self.strum_keys = 0 #Bytearray
        self.nb_strum_keys = 8
                
    def calibrate(self):
        self.uc1.recalibrate_all_keys()
        self.uc2.recalibrate_all_keys()
        self.uc3.recalibrate_all_keys()
        for note, button in enumerate(board.keyboard_note_keys):
            self.notes_ref[note] = self.uc1.read_analog(button)
    
    def loop(self):
        
        self.notes_old = self.notes[:]
        self.notes_val_old = self.notes_val[:]
        self.sharp_old = self.sharp

        self.uc1.loop()
        self.uc2.loop()
        self.uc3.loop()        
        
        self.volume = not(self.volume_pin.value())
        self.instr = not(self.instr_pin.value())
        self.looper = not(self.looper_pin.value())
        self.drum = not(self.drum_pin.value())
        
        self.seventh = self.uc2.button(6)
        self.fifth = self.uc2.button(7)
        self.third = self.uc2.button(8)
        self.minor = self.uc2.button(0)
        self.shift = self.uc2.button(1)
        self.sharp = self.uc1.button(2)

        for note, button in enumerate(board.keyboard_note_keys):
            a = self.notes_ref[note] - self.uc1.read_analog(button)
            #self.notes[note] = self.uc1.button(button)
            self.notes[note] = (a>= self.notes_thres)
            self.notes_val[note] = max(min(a - self.notes_thres, self.notes_max), 0)
        
        #Re-calibrate the touch keys on "Volume" press
        if self.volume and not self.volume_old:
            self.calibrate()
        self.volume_old = self.volume
        
        #Volume slider
        if self.volume:
            v=self.vol_slider.read()
            self.volume_val = v

        #is there a key being pressed right now?
        if self.current_note_key!=None:
            if not self.notes[self.current_note_key]:
                self.current_note_key = None
        if None == self.current_note_key:
            for i, n in enumerate(self.notes):
                if n:
                    self.current_note_key = i
                    break

        #Update the strum keys status
        b = self.uc3.button
        self.strum_mute = b(5)
        self.strum_keys = b(9)+(b(8)<<1)+(b(7)<<2)+(b(6)<<3)+(b(4)<<4)+(b(3)<<5)+(b(1)<<6)+(b(2)<<7)

        #TODO: implement melody lock
        self.melody_led(self.shift)
        
            
#end
            