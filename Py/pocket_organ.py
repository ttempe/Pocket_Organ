import display
import backlight
import keyboard
import looper
import polyphony
import instr_names

import time

class PocketOrgan:
    def __init__(self):
        self.d = display.Display()
        self.b = backlight.Backlight()
        self.k = keyboard.Keyboard()
        self.l = looper.Looper(self.b)
        self.p = polyphony.Polyphony(self.k, self.d, self.l)
#        for i, v in enumerate([6, 6, 6, 12, 12, 12, 8, 8, 8]):
#            self.k.c1.set_threshold(i, v)
        self.volume = 63
    
    def loop_volume(self):
        #TODO: set the master and channel volumes separately
        self.d.disp_volume(self.volume)
        while self.k.volume:
            if self.volume != self.k.slider_vol_val//2:
                self.volume = self.k.slider_vol_val//2
                self.d.disp_volume(self.volume)
                self.p.set_volume(self.volume)
            #don't call d.loop()->freezez the display
            self.p.loop()
            self.k.loop()

    def loop_key(self):
        #TODO
        pass

    def loop_instr(self):
        """Let the user select an instrument from the MIDI bank for the current channel.
        Either one press on a note key (choose the 1st instrument of the family)
        or 2 successive presses (choose an instrument within this family).
        """
        instr = None #output
        k1 = k1_shift = k2 = 0 #these are the successive keys pressed for instrument
        self.d.text("Choose instrument", duration=1)
        while self.k.instr:
            #TODO: display whether the shift key is being pressed
            
            if self.k.current_note_key != None: #1st key pressed
                self.d.text(instr_names.instrument_families[self.k.current_note_key], duration=2000)
                instr = (self.k.current_note_key + (self.k.shift<<4))<<3
                while self.k.current_note_key != None and self.k.instr:
                    self.k.loop()
                    #Not updating the display
                #1st key released
                while self.k.current_note_key == None and self.k.instr:
                    #wait for 2nd key press, or Instr key release
                    self.k.loop()
                    #Not updating the display
                if self.k.current_note_key != None:
                    #2nd note key pressed
                    #print("press2");time.sleep_ms(100)
                    instr += self.k.current_note_key
                self.d.text(instr_names.instrument_names[instr], 1, 2000)
                self.p.set_instr(instr)
                
                #Wait for release of the note key
                while self.k.current_note_key != None:
                    self.k.loop()
                    #Not updating the display
            self.k.loop()

    def loop_chord(self):
        root = self.k.current_note_key
        self.p.start_chord()
        self.b.light_one(root)
        while self.k.notes[root]:
            self.k.loop()
            self.p.loop()
            self.d.loop()
            if self.k.shift:
                self.loop_shift()
            #TODO: if you press the "Melody" key, enter the melody loop without breaking the chord
        #root note key released. Stop chord and return
        self.p.stop_chord()
        self.b.off()

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while 1:
            self.k.loop()
            self.d.loop()
            if self.k.shift:
                #Melody mode.
                self.loop_shift()
            elif self.k.current_note_key != None:
                #Note keys: play chords
                print("On: {} chord".format(self.k.current_note_key));time.sleep_us(50)
                self.loop_chord() #returns when the chord is released
                print("Chord off");time.sleep_us(50)
            elif self.k.instr:
                #MIDI instrument selection loop
                self.loop_instr()
            elif self.k.volume:
                self.loop_volume()
    
    def loop_shift(self): #TODO
        self.d.text("Melody mode")
        while self.k.shift or self.k.current_note_key != None:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    #start playing i
                    self.p.start_note(i)
                elif self.k.notes_old[i] and not self.k.notes[i]:
                    #stop playing i
                    self.p.stop_note(i)
            self.k.loop()
            self.d.loop()
            self.p.loop()
        self.p.stop_all_notes()
        self.d.clear()

o = PocketOrgan()
o.loop_waiting()

#end