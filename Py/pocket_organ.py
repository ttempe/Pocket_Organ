import keyboard
import polyphony
import midi
import time


#Todo:
# * read the keyboard interrupt; then set the threshold one step lower and measure the time to get an
# interrupt again. Are the readings consistant enough to estimate key velocity?


class PocketOrgan:
    def __init__(self):
        self.k = keyboard.Keyboard()
        self.p = polyphony.Polyphony(self.k)
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
            self.k.loop()

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
            
            if self.k.current_note_key != None: #1st key pressed
                print("Selected family: {}".format(midi.instrument_families[self.k.current_note_key]))
                k1 = self.k.current_note_key
                k1_shift = self.k.shift
                instr = (self.k.current_note_key + (self.k.shift<<4))<<3
                while self.k.current_note_key != None and not(self.k.instr_pin()):
                    self.k.loop()

                #1st key released
                while self.k.current_note_key == None and not(self.k.instr_pin()):
                    #wait for 2nd key press, or Instr key release
                    self.k.loop()
                if self.k.current_note_key != None:
                    #2nd note key pressed
                    instr += self.k.current_note_key
                print("Selected instrument: {}".format(midi.instrument_names[instr]))
                
                #Wait for release of the note key
                while self.k.current_note_key != None:
                    self.k.loop()


            self.k.loop()

    def loop_chord(self):
        root = self.k.current_note_key
        self.p.start_chord()
        while self.k.notes[root]:
            self.k.loop()
            self.p.loop()
            #TODO: if you press the "Melody" key, enter the melody loop without breaking the chord
        #root note key released. Stop chord and return
        self.p.stop_chord()

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while 1:
            self.k.loop()
            
            #Melody mode.
            if self.k.shift:
                self.loop_shift()

            #Note keys: play chords
            elif self.k.current_note_key != None:
                print("On: {} chord".format(self.k.current_note_key));time.sleep_us(50)
                self.loop_chord() #returns when the chord is released
                print("Chord off");time.sleep_us(50)

            #MIDI instrument selection loop
            elif not(self.k.instr_pin()): 
                self.loop_instr()
    
    def loop_shift(self):
        while self.k.shift:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    #start playing i
                    self.midi.note_on(0, self.scale[i])
                    #print("On: {}".format(i));time.sleep_us(200)#
                elif self.k.notes_old[i] and not self.k.notes[i]: