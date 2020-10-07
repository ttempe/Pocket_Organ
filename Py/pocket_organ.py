import display
import backlight
import keyboard
import looper
import polyphony
import instr_names

import time
import gc #Garbage collector

#TODO:
# * Read the accelerometer
# * Choose a better selection of percussion for the Drum mode
# * Should the volume be global or channel-specifi? What should happen if I change it while recording a loop?
# * setup a mechanism for sending a message to the display, together with a function for checking whether this message is still active
# * find a way of voiding the warranty before exposing the filesystem throught USB?
# * add a reinit() call to each of the SPI chip drivers, to setup the bus for itself. Takes ~150 us.

class PocketOrgan:
    def __init__(self):
        
        #For V15 only: pull high the CS for all devices on the SPI bus
        from machine import Pin
        Pin("B8",  Pin.OUT).value(1)
        #Pin("B12", Pin.OUT).value(1)#Already pulled up electrically
        Pin("A8", Pin.OUT).value(1)
        Pin("C3", Pin.OUT).value(1)
        Pin("C5", Pin.OUT).value(1)
        
        self.d = display.Display()
        self.b = backlight.Backlight()
        self.k = keyboard.Keyboard()
        self.l = looper.Looper(self.b, self.d)
        self.p = polyphony.Polyphony(self.k, self.d, self.l)

    def loop(self, freeze_display=False):
        self.l.loop()
        self.p.loop()
        if not freeze_display:
            self.d.loop()
        gc.collect()
        self.k.loop()
    
    def loop_volume(self):
        #TODO: set the master and channel volumes separately
        self.d.disp_volume(self.p.volume)
        while self.k.volume:
            if self.p.volume != self.k.slider_vol_val//2:
                self.p.volume = self.k.slider_vol_val//2
                self.d.disp_volume(self.p.volume)
                self.p.set_volume(self.p.volume)
            self.loop(freeze_display=True)

    def loop_looper(self):
        #TODO: Allow to delete a track even while it's playing.
        last_tap_timestamp = 0
        if not self.l.stop_recording():
            self.d.text("Looper", 0)
            self.d.text("{} BPM".format(self.p.metronome.bpm), 2)
            self.d.text('Tap "minor" to\nset rythm', 3)
        self.l.display()
        while self.k.looper:
            key = self.k.current_note_key
            if key != None:
                #keypress
                if self.l.loop_exists(key):
                    self.l.toggle_play(key)
                    #Capture the UI until the key is released
                    t = time.ticks_ms()
                    while self.k.notes[key]:
                        #While key is not released:
                        if (time.ticks_ms()-t)>1000 and not(self.l.playing & (1<<key)):
                            #Long press
                            self.l.delete_track(key)
                            while self.k.notes[key]:
                                #Delete once, then capture the UI
                                self.loop(freeze_display=True)
                        else:
                            self.loop(freeze_display=True)
                elif self.l.recording == None:
                    #Not in recording mode yet
                    self.l.start_recording(key)                    
                    #Capture the UI until the key and the "loop" button are both released
                    #No further action is possible
                    while self.k.notes[key] or self.k.looper:
                        self.loop(freeze_display=True)
                        
            elif self.k.minor:
                #Set the beat by tapping it on the "minor" key
                now = time.ticks_ms()
                duration = now-last_tap_timestamp
                if last_tap_timestamp and duration < 2000 and duration >300:
                    #it's the 2nd tap
                    self.p.metronome.set_bpm(60000//duration)
                    self.d.text("{} BPM".format(self.p.metronome.bpm), 2)
                last_tap_timestamp=now
                while self.k.minor:
                    #wait for "minor" key release
                    self.loop(freeze_display=True)
                    
            elif (self.k.seventh and self.p.metronome.bpm<200)or (self.k.third and self.p.metronome.bpm>30):
                #manually adjust the BPM (+/-)
                self.p.metronome.set_bpm( (self.p.metronome.bpm//5)*5+5*self.k.seventh - 5*self.k.third)
                self.d.text("{} BPM".format(self.p.metronome.bpm), 2)
                while self.k.seventh or self.k.third:
                    #wait for both keys release
                    self.loop(freeze_display=True)
            
            elif self.k.fifth:
                #Toggle metronome tick
                self.p.metronome.toggle()
                print("Toggle")
                while self.k.fifth:
                    #Wait for "fifth" key release
                    self.loop(freeze_display=True)
                
            self.loop()
            

        self.l.apply_ui()

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
                family = self.k.current_note_key + (self.k.minor<<3)
                self.d.text(instr_names.instrument_families[family], duration=2000)
                instr = family <<3
                while self.k.current_note_key != None and self.k.instr:
                    self.loop(freeze_display=True)
                #1st key released
                while self.k.current_note_key == None and self.k.instr:
                    #wait for 2nd key press, or Instr key release
                    self.loop(freeze_display=True)
                if self.k.current_note_key != None:
                    #2nd note key pressed
                    instr += self.k.current_note_key
                self.d.text(instr_names.instrument_names[instr], 1, 2000)
                self.p.set_instr(instr)
                
                #Wait for release of the note key
                while self.k.current_note_key != None:
                    self.loop(freeze_display=True)
            self.loop(freeze_display=True)

    def loop_chord(self):
        root = self.k.current_note_key
        self.p.start_chord()
        self.b.light_one(root)
        while self.k.notes[root]:
            self.loop()
            if self.k.shift:
                self.loop_shift()
            #TODO: if you press the "Melody" key, enter the melody loop without breaking the chord
        #root note key released. Stop chord and return
        self.p.stop_chord()
        self.b.off()

    def loop_drum(self):
        while self.k.drum:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    name = self.p.play_drum(i)
                    self.d.text(name, duration=1000)
            self.loop()

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while 1:
            self.loop()
            if self.k.shift:
                #Melody mode.
                self.loop_shift()
            elif self.k.current_note_key != None:
                #Note keys: play chords
                print("On: {} chord".format(self.k.current_note_key));time.sleep_us(50)
                self.loop_chord() #returns when the chord is released
                print("Chord off");time.sleep_us(50)
            elif self.k.instr and (None == self.l.recording):
                #MIDI instrument selection loop
                self.loop_instr()
            elif self.k.volume:
                self.loop_volume()
            elif self.k.looper:
                self.loop_looper()
            elif self.k.drum:
                self.loop_drum()

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
            self.loop()
        self.p.stop_all_notes()
        self.d.clear()

o = None
while not o:
    try:
        o = PocketOrgan()
    except OSError:
        time.sleep(1)
        print(".", end="")

o.loop_waiting()

#end