import display
import backlight
import keyboard
import looper
import polyphony
import instr_names
import battery
import midi
import board_po as board

from supervisor import ticks_ms
from time import sleep
import gc #Garbage collector
import sys

# TODO V31:
# Write documentation for the instrument
# Backlight potential other keys (hints) when pressing volume, capo, instr...
# Turn off all midi sounds when turning on the instrument, and on interrupt
# How much memory do I have? How fast will the looper run out? What happens then?
# Audit the code, module by module


# TODO V32:
# Strumming
# Test force_on, and force_off. 
# Turn off when battery is low.
# Turn off when idle for a long time, or when USB is unplugged after not playing for a long time.
# Measure and tune power consumption
# Measure and tune loop time

# TODO Later:
# Save the loops in .mid format to the filesystem
# QR code for diagnostics: instrument unique ID, version, link to documentation/support, total play time, error code (25*25 -> 47 characters) Use https://github.com/JASchilz/uQR
# Message to press and hold when the user releases the vol/instr/loop/drum/shift/3,5,7,m too fast

# TODO Prospective:
# * Improved MIDI expression compatibility
#   now: sending CC11 signals, which are supported by SAM2695) 
#   later: add Channel Pressure (0xD0) that are better supported on computers.
#   make it configurable, somehow...
# * Record loop->Stop loop->Start loop=> the loop should restart at the beginning.
# * Measure the total time the musician has been playing. Save it to flash.
# * implement tuning (Shift+Capo)
# * Build a firmware image, including the instrument code?
# * Find a way of voiding the warranty before allowing to flash the firmware.

def on_bits(num):
    for i in range(8):
        if (num>>i)&1:
            yield i

_MODE_NAMES = ("Chords mode", "Melody mode", "Drums mode")

class PocketOrgan:
    def __init__(self):
        #Keep on
        board.power_off.value = True
        print("\nTurning on")
        
        self.min_loop_duration=12 #ms
        self.d = display.Display()
        self.b = backlight.Backlight()
        self.k = keyboard.Keyboard()
        self.l = looper.Looper(self.b, self.d)
        self.p = polyphony.Polyphony(self.k, self.d, self.l)
        self.l.p = self.p
        self.bat = battery.Battery(self.d)
        self.last_t = ticks_ms()
        self.last_t_disp = 0
        self.longest_loop = 0
        self.last_mode = self.k.mode

    def off(self):
        #TODO: wait for end of disk write operation
        #TODO: stop MIDI out, interrupt loop playing, abort any loop recording in progress
        #TODO: reset the other parameters (volume, current instrument, ...)
        #TODO: clear screen
        pressed_time = 0
        while pressed_time < 5:
            if not board.key_power.value: #released early
                return
            sleep(0.1)
            pressed_time += 1
        print("Turning off")
        board.power_off.value = False
        #If running on battery, power will stop here
        #The following code will only execute if the board is being powered from USB when the power off button was pressed
        self.d.clear()
        while board.key_power.value:
            #wait for key release
            pass
        print("Released")
        pressed_time = 0
        #Turn back on if there is a sustained press
        #TODO: turn screen on
        while pressed_time < 5:
            if board.key_power.value:
                #Pressed
                sleep(0.1)#anti-rebound
                pressed_time += 1
            else:
                pressed_time = 0
        print("Turning on")
        board.power_off.value = True
        self.d.text("Pocket Organ")
        while board.key_power.value:
            #wait for key release
            pass
        self.d.clear()
                        

    def loop(self, freeze_display=False):
        self.l.loop()
        self.p.loop()
        if not freeze_display:
            self.d.loop() 
        self.bat.loop()
        gc.collect()
        self.k.loop()
        if self.k.mode != self.last_mode:
            self.last_mode = self.k.mode
            self.d.text(_MODE_NAMES[self.k.mode])
        #if board.key_power.value: #Todo
        #    self.off()
        
        #measure & display max loop time
        t=ticks_ms()
        if board.verbose:
            self.longest_loop = max(self.longest_loop, t-self.last_t)
            if t-self.last_t_disp > 500:
                self.d.latency.text="{}ms".format(self.longest_loop)
                #print("longest loop:",self.longest_loop)
                self.longest_loop = 0
                self.last_t_disp = t
        self.last_t = ticks_ms()

    def loop_volume(self):
        master = not(self.k.shift)
        if not master and self.l.recording is not None:
            self.d.text("Can't change channel vol while recording")
            while self.k.volume:
                self.loop(freeze_display=True)
            return
        vname = "Master volume:" if master else "Channel volume:"
        base = self.p.master_volume if master else self.p.channel_volume
        self.d.disp_slider(base, vname)
        while self.k.volume and (self.k.pressed(board.key_up) or self.k.pressed(board.key_down)):
            self.loop(freeze_display=True)
        peg = 0
        pressed = 0
        vol = base
        while self.k.volume or self.k.pressed(board.key_up) or self.k.pressed(board.key_down):
            if 0==pressed:
                if self.k.pressed(board.key_up):
                    pressed=1
                    key = board.key_up
                elif self.k.pressed(board.key_down):
                    pressed=2
                    key = board.key_down
            if 0 != pressed:
                pressure = (self.k.notes_val[key])//16
                if pressure>peg:
                    peg=pressure
                    vol = min(127, max(0, base + (peg if 1==pressed else -peg)))
                    if master:
                        self.p.set_master_volume(vol)
                    else:
                        self.p.set_channel_volume(vol)
                    self.d.disp_slider(vol, vname)
            self.loop(freeze_display=True)
            if 0 != pressed and not (self.k.pressed(board.key_up) or self.k.pressed(board.key_down)):
                base = self.p.master_volume if master else self.p.channel_volume
                peg = 0
                pressed = 0


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
                    t = ticks_ms()
                    while self.k.pressed(key):
                        #While key is not released:
                        if (ticks_ms()-t)>1500: #and not(self.l.playing & (1<<key)):
                            #Long press
                            self.l.delete_track(key)
                            while self.k.pressed(key):
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
                        while self.k.looper or self.k.pressed(key):
                            self.loop(freeze_display=True)
                            if self.k.looper and not self.k.pressed(key):
                                released = True
                            elif self.k.looper and self.k.pressed(key) and released:
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
                            if self.l.recording != None:
                                self.l.stop_recording()
                            self.l.leave_looper()
                            return
                    else:
                        #Recording start failed
                        while self.k.pressed(key):
                            self.loop(freeze_display=True)
                        
            elif self.k.minor:
                #Set the beat by tapping it on the "minor" key
                #Note: human beat precision & recognition is ~ 10~15ms, or around one loop.
                now = ticks_ms()
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
            

        self.l.leave_looper()
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
                sleep(0.5)
                self.p.stop_chord()
                sleep(0.2)
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
        while self.k.pressed(root):
            self.loop()
            if board.verbose:
                #TODO: Display the pitch & velocity on the OLED display in real time
                pass                
        #root note key released. Stop chord and return
        self.p.stop_chord()
        self.b.light_none()

    def loop_melody(self):
        self.p.start_melody()
        self.p.update_melody()
        shown = ()
        while None != self.k.current_note_key:
            self.loop(freeze_display=True)
            self.p.update_melody()
            self.b.light_keys(self.k.bitmap & 0xFF)
            names = self.p.melody_note_names()
            if names != shown:
                shown = names
                self.d.text(" ".join(names) if names else "")
        self.b.light_none()
        self.p.stop_melody()

    def loop_drum(self):
        self.d.text("Drum")
        while None != self.k.current_note_key:
            for i in on_bits(self.k.bitmap&~self.k.bitmap_old):
                self.d.text(self.p.play_drum(i))
            self.loop()
            self.b.light_keys(self.k.bitmap & 0xFF)
            if self.k.current_note_key == None:
                self.check_function_keys()
        self.b.light_none()

    def loop_capo(self):
        print_txt = lambda lvl: "Capo {} ({})".format(lvl, instr_names.note_names[lvl])
        self.d.text(print_txt(self.p.transpose)) #Disp previous capo level
        key = None
        sharp = False
        sharp_old = 0
        level = 0
        changed = False
        while self.k.capo or self.k.current_note_key!=None or self.k.sharp: #Hold control till the user releases the key
            
            if self.k.current_note_key != key and self.k.current_note_key != None: #Set level on keypress
                key = self.k.current_note_key
                level = keyboard.key_levels[key]
                self.d.text(print_txt(level+sharp))
                changed = True

            if self.k.sharp and not(sharp_old): #Toggle sharp with every press
                sharp = not(sharp)
                changed = True
                self.d.text(print_txt(level+sharp))
                
            sharp_old = self.k.sharp
            self.loop(freeze_display=True)

        if changed:
            self.p.transpose = level+sharp


    def loop_tune(self):
        self.d.text("Not implemented")
        while self.k.loop:
            self.loop(freeze_display=True)

    def loop_waiting(self):
        "starting loop, waiting for 1st keypress"
        while True:
            self.loop()
            if self.k.current_note_key != None: #Keypress
                #Enter the right loop. Return when the keypress is released
                if keyboard.chord == self.k.mode:
                    self.loop_chord()
                elif keyboard.melody == self.k.mode:
                    self.loop_melody()
                else:
                    self.loop_drum()
            self.check_function_keys() #Returns immediately unless a key was pressed
                
    def check_function_keys(self):
        if self.k.volume:
            self.loop_volume()
        elif self.k.looper:
            self.loop_looper()
        elif self.k.instr:
            if self.l.recording:
                self.d.text("Can't change instrument while recording", tip=True)
                while self.k.instr:
                    self.loop() #wait for key release
            else:
                #MIDI instrument selection loop
                self.loop_instr()
        elif self.k.capo:
            self.loop_capo()

def start():
    "Start and catch exception"
    organ = None
    try:
        organ = PocketOrgan()
        organ.loop_waiting()
    except Exception as e:
        try:
            for channel in range(16):
                organ.midi.all_off(channel)
            #organ.d.display_error(e) #TODO
        except Exception:
            pass
        raise

start()

#end