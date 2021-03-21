import display_stub as display
import backlight
import keyboard_AT42QT1110 as keyboard
import looper
import polyphony
import instr_names_stub as instr_names

import time
import gc #Garbage collector

#TODO:
# * implement capo and tune
# * add key expression (bending?); filter the messages
# * improve latency by measuring the derivative of key analog values and synchronizing the acquisition cycle with the main loop
# * Store fonts as frozen bytecode with https://github.com/peterhinch/micropython_data_to_py
# * Add an itermediary-sized font with https://github.com/peterhinch/micropython-font-to-py. (Pre-compiled fonts: https://github.com/peterhinch/micropython-font-to-py)
# * Get notifications working; add a "write/erase" notification
# * Save the status of recorded loops into flash memory somewhere
# * Split the volume slider into channel-specific (hold a Note key) and global (no keypress)
# * Get the OLED display working
# * Add the ability to modify the chord shape on the fly (sus, dim...)
# * Find a way of voiding the warranty before exposing the filesystem throught USB?
# * Build a stand-alone firmware flasher program
# * Add a reinit() call to each of the SPI chip drivers, to setup the bus for itself with optimal speed. Takes ~150 us.
# * Get the accelerometer working
# * Fix MIDI output; have it tested by experienced DAW users.
# * Practice the looper. Is it flexible enough in handling loops of various lengths?
# * Do I need a 5th button? (eg: for storing sets of loops)
# * Disable FS access?
# * Measure the time the musician has been playing
# * Run the filesystem files with higher priority than the frozen bytecode?
# * Display PocketOrgan.longest_loop on the OLED, for debugging purposes

class PocketOrgan:
    def __init__(self):
        self.min_loop_duration=12 #ms        
        self.d = display.Display()
        self.b = backlight.Backlight()
        self.k = keyboard.Keyboard()
        self.l = looper.Looper(self.b, self.d)
        self.p = polyphony.Polyphony(self.k, self.d, self.l)
        self.last_t = time.ticks_ms()
        self.longest_loop = 0

    def loop(self, freeze_display=False):
        self.l.loop()
        self.p.loop()
        self.d.loop(freeze_display)
        gc.collect();
        self.k.loop()
        #make sure we have constant time between loops
        t=time.ticks_ms()        
        time.sleep_ms(max(0,self.min_loop_duration-(t-self.last_t)))
        self.longest_loop = max(self.longest_loop, t-self.last_t)
        self.last_t = t

    def loop_volume(self):
        #TODO: set the master and channel volumes separately
        volume_old=0       
        while self.k.volume:
            if self.k.volume_val != volume_old and self.k.volume_val:
                self.p.set_master_volume( self.k.volume_val)
                self.d.disp_volume(self.k.volume_val)
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
                    if self.l.start_recording(key):
                        #Recording start success
                        #Capture the UI until the key and the "loop" button are both released
                        #or detect additional presses to the key
                        quick = False
                        released = False
                        while self.k.looper or self.k.notes[key]:
                            self.loop(freeze_display=True)
                            if self.k.looper and not self.k.notes[key]:
                                released = True
                            elif self.k.looper and self.k.notes[key] and released:
                                #new press. Toggle "quick recording" on and off
                                released = False
                                quick = not(quick)
                                if quick:
                                    self.d.text("Start recording\nquick loop ", 2000)
                                    self.p.metronome.off()
                                else:
                                    self.d.text("Start recording\nnormal loop", 2000)
                                    self.p.metronome.on()
                        #Keys released. Return?
                        if quick:
                            self.l.start_recording_quick()
                            self.loop_quick()
                            return
                    else:
                        #Recording start failed
                        while self.k.notes[key]:
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
        k1 = k1_shift = k2 = 0 #these are te successive keys pressed for instrument
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

    def loop_quick(self):
        #Quick loop record mode.
        #TODO: Stop all currently playing instruments
        #TODO: bug: the timing of the chords is not aligned to the metronome
        self.p.metronome.pause()
        self.p.midi.all_off(self.l.melody_channel)
        print("Entering quick loop recorder")
        while not self.k.looper:
            self.loop()
            if None != self.k.current_note_key:
                #note key pressed
                self.p.start_chord(quick_mode=True)
                self.l.quick_increment()
                time.sleep_ms(500)
                self.p.stop_chord()
                time.sleep_ms(200)
                while None != self.k.current_note_key:
                    #Wait for key release
                    self.loop()           
        print("Exiting quick loop recorder")
        self.p.metronome.resume()

    def loop_chord(self):
        "Currently playing a chord"
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
        self.b.light_none()

    def loop_drum(self):
        while self.k.drum:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    name = self.p.play_drum(i)
                    self.d.text(name, duration=1000)
            if self.k.sharp and not self.k.sharp_old:
                name = self.p.play_drum(8)
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

def start():
    o = PocketOrgan()
    o.loop_waiting()
start()

#end