import keyboard
import midi
import time


#Todo:
# * read the keyboard interrupt; then set the threshold one step lower and measure the time to get an
# interrupt again. Are the readings consistant enough to estimate key velocity?


class PocketOrgan:
    def __init__(self):
        self.k = keyboard.Keyboard()
        self.midi = midi.Midi()
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]
#        for i in range(0, 9):
#            self.k.c1.set_threshold(i, 10)
        for i, v in enumerate([6, 6, 6, 12, 12, 12, 8, 8, 8]):
            self.k.c1.set_threshold(i, v)
    
    def loop_volume(self):
        while self.k.volume_command():
            #TODO
            #
            #
            self.k.read()

    def loop_key(self):
        #TODO
        pass

    def loop_instr(self):
        """Let the user select an instrument from the MIDI bank for the current channel.
        Either one press on a note key (choose the 1st instrument of the family)
        or 2 successive presses (choose an instrument within this family).
        """
        instr = 0 #output
        k1 = k1_shift = k2 = 0 #these are the successive keys pressed for instrument
        while not(self.k.instr_pin()):
            #TODO display "instrument setting"
            #print("instr");time.sleep_ms(200);
            #TODO: display whether the shift key is being pressed
            p, k1 = self.k.note_key()
            if p: #1st key pressed
                #TODO:display
                print("Selected family: {}".format(midi.instrument_families[k1]))
                k1_shift = self.k.shift
                while p and not(self.k.instr_pin()):
                    self.k.read()
                    p, k0 = self.k.note_key()
                #1st key released
                instr = (k1 + (k1_shift<<4))<<3
                if self.k.instr_pin(): #instr key released
                    break
                while not p and not(self.k.instr_pin()):
                    #wait for 2nd key press
                    self.k.read()
                    p, k2 = self.k.note_key()
                if p:
                    instr += k2
                print("Selected instrument: {}".format(midi.instrument_names[instr]))

            self.k.read()

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while 1:
            self.k.read()

            if self.k.shift:
                #Enter the melody mode. If a chord was playing, it keeps going in the background
                #TODO: dispatch melody mode to a separate channel
                self.loop_shift()
                #TODO: stop the running chord as you leave melody mode

            #Note keys
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    #start playing i
                    self.midi.note_on(0, self.scale[i])
                    #print("On: {}".format(i));time.sleep_us(200)#
                elif self.k.notes_old[i] and not self.k.notes[i]:
                    #stop playing i
                    self.midi.note_off(0, self.scale[i])
                    #print("Off: {}".format(i));time.sleep_us(200)#

            #MIDI instrument selection loop
            if not(self.k.instr_pin()): 
                self.loop_instr()
    
    def loop_shift(self):
        while self.k.shift:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    #start playing i
                    self.midi.note_on(0, self.scale[i])
                    #print("On: {}".format(i));time.sleep_us(200)#
                elif self.k.notes_old[i] and not self.k.notes[i]:
                    #stop playing i
                    self.midi.note_off(0, self.scale[i])
                    #print("Off: {}".format(i));time.sleep_us(200)#
            self.k.read()

o = PocketOrgan() 
#o.play_notes()
o.loop_waiting()