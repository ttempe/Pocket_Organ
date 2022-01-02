import display
import backlight
import keyboard_AT42QT1110 as keyboard
import looper
import polyphony
import instr_names
import battery
import board

import time
import gc #Garbage collector

# TODO:
# * Write to flash: Don't wait for loop(), attempt to start writing on each message (time message writes to determine a minimum queue size)
# * Fix battery gauge display
# * Configure the struming comb UC to not recalibrate during long presses
# * Observe capacitive readings drift when battery voltage decreases
# * Display "Shift", "Chords mode", "Drums mode" when switching modes
# * melody mode expression (partial keypress)
# * Message to press and hold when the user releases the vol/instr/loop/drum/shift/3,5,7,m
# * Record loop->Stop loop->Start loop=> the loop should restart at the beginning.
# * Add a reinit() call to each of the SPI chip drivers, to setup the bus for itself with optimal speed. Takes ~150 us.
#   -> Done for AT42QT1110 1.5M; not done for SSD1306 10M; not done for flash TBD
# * MIDI USB output
#   -> Not supported on Micropython (2021-09). Apparently supported on CircuitPython. Try out bluetooth first, with an external ESP32.
# * Practice the looper. Is it flexible enough in handling loops of various lengths?
# * Measure the total time the musician has been playing. Save it to flash.
# * implement tuning
# * Optimize loop erase time
# * display note name (Do~Ut) while playing in melody mode
# * Exception display: clip to the letter, not word, to display file name.
# * Melody mode bending: review and improve

# Prospective
# * Freeze the contents of img/*.pbm. (Add it to .py files directly?)
# * Find a way of voiding the warranty before exposing the filesystem throught USB?
# * Handle crashes: error codes, displaying a QR code with instrument unique ID, timestamp, link to documentation/support (25*25 -> 47 characters) ;
#  -> generate it by catching the exception. Use https://github.com/JASchilz/uQR
# * Midi MPE controller

# Notes:
# * using a custom Micropython build, see: https://forum.micropython.org/viewtopic.php?t=4673

class PocketOrgan:
    def __init__(self, d=None):
        self.min_loop_duration=12 #ms
        self.d = d if d else display.Display()
        self.b = backlight.Backlight()
        self.k = keyboard.Keyboard()
        self.l = looper.Looper(self.b, self.d)
        self.p = polyphony.Polyphony(self.k, self.d, self.l)
        self.l.p = self.p
        self.bat = battery.Battery(self.d)
        self.last_t = time.ticks_ms()
        self.last_t_disp = 0
        self.longest_loop = 0

    def loop(self, freeze_display=False):
        self.l.loop()
        self.p.loop()
        self.d.loop(freeze_display)
        self.bat.loop()
        gc.collect();
        self.k.loop()
        #make sure we have constant time between loops
        t=time.ticks_ms()
        #display longest time
        time.sleep_ms(max(0,self.min_loop_duration-(t-self.last_t)))
        if board.verbose:
            self.longest_loop = max(self.longest_loop, t-self.last_t)
            if t-self.last_t_disp > 500:
                self.d.indicator_txt(str(self.longest_loop)+"ms", 24)
                self.longest_loop = 0
                self.last_t_disp = t
        self.last_t = t

    def loop_volume(self):
        #TODO: set the channel volume
        master = not(self.k.shift)
        vname = lambda: "Master volume:" if master else "Channel volume:"
        self.d.disp_slider(self.p.volume, vname())
        slider_old=0
        self.p.strumming = False #temporarily disable strumming
        while self.k.volume:
            if self.k.slider_val != slider_old and (self.k.slider_val != None):
                self.p.set_master_volume(self.k.slider_val)
                self.d.disp_slider(self.k.slider_val, vname())
                slider_old = self.k.slider_val
            self.loop(freeze_display=True)
        self.p.strumming = True

    def loop_looper(self):
        #TODO: Allow to delete a track even while it's playing.
        last_tap_timestamp = 0
        if not self.l.stop_recording():
            self.d.text("Looper")
            self.d.text("{} BPM".format(self.p.metronome.bpm), 1)
            self.d.text('Tap "minor" to set rythm', 2, tip=True)
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
                        if (time.ticks_ms()-t)>1500 and not(self.l.playing & (1<<key)):
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
                                    self.d.text("Start recording quick loop")
                                    self.d.text("Again for normal mode", 2, tip=True)
                                    self.p.metronome.off()
                                else:
                                    self.d.text("Start recording")
                                    self.d.text("Press again for quick loop mode", 1, tip=True)
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
                #Note: human beat precision & recognition is ~ 10~15ms, or around one loop.
                now = time.ticks_ms()
                duration = now-last_tap_timestamp
                if last_tap_timestamp and duration < 2000 and duration >300:
                    #it's the 2nd tap
                    self.p.metronome.set_bpm(60000//duration)
                    self.d.text("{} BPM".format(self.p.metronome.bpm), 1)
                    self.d.text("tap till it's right!", 2, tip=True)
                else:
                    self.d.text("...tap again", 2, tip=True)
                last_tap_timestamp=now
                while self.k.minor:
                    #wait for "minor" key release
                    self.loop(freeze_display=True)
                    
            elif (self.k.seventh and self.p.metronome.bpm<200)or (self.k.third and self.p.metronome.bpm>30):
                #manually adjust the BPM (+/-)
                self.p.metronome.set_bpm( (self.p.metronome.bpm//5)*5+5*self.k.seventh - 5*self.k.third)
                self.d.text("{} BPM".format(self.p.metronome.bpm), 1)
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
                
            self.loop(freeze_display=True)
            

        self.l.apply_ui()

    def loop_instr(self):
        """Let the user select an instrument from the MIDI bank for the current channel.
        Either one press on a note key (choose the 1st instrument of the family)
        or 2 successive presses (choose an instrument within this family).
        """
        instr_old = None
        k1 = k1_shift = k2 = 0 #these are te successive keys pressed for instrument
        self.d.text("Choose family")
        self.d.text("Hold Melody key for additional families.", 1, tip=True)
        while self.k.instr:
            #TODO: display whether the shift key is being pressed
            if self.k.current_note_key != None: #1st key pressed
                family = self.k.current_note_key + (self.k.shift<<3)
                self.d.text(instr_names.instrument_families[family])
                self.d.text("Choose instr in family", 1, tip=True)
                instr2 = 0
                while self.k.current_note_key != None and self.k.instr:
                    self.loop(freeze_display=True)
                #1st key released
                while self.k.instr:
                    while self.k.current_note_key == None and self.k.instr:
                        #wait for 2nd key press, or Instr key release
                        self.loop(freeze_display=True)
                    if self.k.current_note_key != None:
                        #2nd note key pressed
                        if self.k.current_note_key == instr_old:
                            #Pressing the same key multiple time moves to the next instr within that family
                            instr2 = (instr2 +1)&0x07
                        else:
                            instr2 = self.k.current_note_key
                            instr_old = self.k.current_note_key
                    instr = (family << 3) + instr2
                    self.d.text(instr_names.instrument_names[instr], 1)
                    self.d.text("Press again for next", 2, tip=True)
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
            if self.k.shift or self.k.melody_lock:
                self.loop_melody()
                if board.verbose:
                    #TODO: Display the pitch & velocity on the OLED display in real time
                    pass                
        #root note key released. Stop chord and return
        self.p.stop_chord()
        self.b.light_none()

    def loop_drum(self):
        self.d.text("Drum")
        while self.k.drum:
            for i in range(0,8):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    name = self.p.play_drum(i)
                    self.d.text(name)
            self.loop()
            if self.k.current_note_key == None:
                self.check_function_keys()

    def loop_capo(self):
        print_txt = lambda lvl: "Capo {} ({})".format(lvl, instr_names.note_names[lvl])
        self.d.text(print_txt(self.p.transpose))
        t = 0
        old_sharp = 0
        last_text=""
        while self.k.capo or self.k.current_note_key != None:
            level, sharp = self.k.current_note_key_level()
            if level != None and level != self.p.transpose and ( not(old_sharp) or sharp or time.ticks_ms()-t > 400):
                #400 ms grace period when releasing a sharp (combinaison of 2 keypresses)
                self.p.transpose = level%12
                text = print_txt(level)
                if text != last_text:
                    self.d.text(text)
                    last_text = text
                t = time.ticks_ms() #Grace period to allow sharps
                old_sharp = sharp
            self.loop(freeze_display=True)

    def loop_tune(self):
        self.d.text("Not implemented")
        while self.k.loop:
            self.loop(freeze_display=True)

    def loop_melody(self):
        lock_old = False
        if self.k.melody_lock and not lock_old:
            self.d.text("Melody mode")
            lock_old = True

        self.p.start_melody()
        
        while self.k.shift or self.k.melody_lock or (self.k.current_note_key != None):
            self.p.update_melody()
            self.loop(freeze_display=True)
            if self.k.current_note_key == None and self.p.playing_chord_key == None:
                self.check_function_keys()
        self.p.update_melody() #let the melody mode finish gracefully
        self.p.stop_melody()

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while 1:
            self.loop()
            if self.k.shift or self.k.melody_lock:
                self.loop_melody()
            elif self.k.current_note_key != None:
                #Note keys: play chords
                self.loop_chord() #returns when the chord is released
            else:
                self.check_function_keys()
                
    def check_function_keys(self):
        if self.k.instr:
            if self.l.recording:
                self.d.text("Can't change instrument while recording", tip=True)
                while self.k.instr:
                    self.loop() #wait for key release
            else:
                #MIDI instrument selection loop
                self.loop_instr()
        elif self.k.volume:
            self.loop_volume()
        elif self.k.looper:
            if self.k.shift:
                self.loop_tune()
            else:
                self.loop_looper()            
        elif self.k.drum and not self.k.drum_old:
            self.loop_drum()
        elif self.k.capo:
            self.loop_capo()


def start():
    d = display.Display()
    try:
        o = PocketOrgan()
        o.loop_waiting()
    except Exception as e:
        import sys
        fd = open("err.txt", "w")
        sys.print_exception(e, fd)
        fd.close()
        fd = open("err.txt","r")
        d.text(fd.read(), tip=True)
        raise(e)
        
start()

#end