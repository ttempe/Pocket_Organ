import display
import backlight
import keyboard
import looper
import polyphony
import instr_names
import battery
import board_po as board

from supervisor import ticks_ms
from time import sleep
import gc #Garbage collector

#from microcontroller import watchdog


# TODO:
# * Auto-off (separate timeout if plugged off from USB)
# * Is it possible to move "down" to the "shift" key instead? if so, use up/down to move the capo as well.
# * Fix battery gauge
# * TODO: expand the chords when pressing additional (unused) note keys
# * What do I do with Shift+7 in melody mode?
# * Display "Shift", "Chords mode", "Drums mode" when switching modes
# * melody mode expression (partial keypress)
# * Record loop->Stop loop->Start loop=> the loop should restart at the beginning.
# * Measure the total time the musician has been playing. Save it to flash.
# * implement tuning
# * display note name (Do~Ut) while playing in melody mode
# * Auto-off after 30 minutes without playing
# * Todo: implement watchdog to turn off when loop stalls
#
# Prospective
# * Optimize the MCU settings for low-voltage operation: https://docs.micropython.org/en/latest/library/pyb.ADC.html#pyb-adc after read_vref()
# * Find a way of voiding the warranty before exposing the filesystem throught USB?
# * Handle crashes: error codes, displaying a QR code with instrument unique ID, version, timestamp, link to documentation/support (25*25 -> 47 characters) ;
#  -> generate it by catching the exception. Use https://github.com/JASchilz/uQR
# * Message to press and hold when the user releases the vol/instr/loop/drum/shift/3,5,7,m too fast
# * Midi MPE controller

def on_bits(num):
    for i in range(8):
        if (num>>i)&1:
            yield i

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
        self.d.loop(freeze_display)
        self.bat.loop()
        gc.collect()
        self.k.loop()
        if board.key_power.value:
            self.off()
        #TODO:watchdog
        #w.feed()

        
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
        #TODO: set the channel volume
        master = not(self.k.shift)
        print("Volume!")
        vname = "Master volume:" if master else "Channel volume:"
        self.d.disp_slider(self.p.volume, vname)
        while self.k.volume and (self.k.up or self.k.down): #make sure both are released before starting
            self.loop(freeze_display=True)
        peg = 0
        pressed = 0
        vol = self.p.volume if master else 0 #TODO: channel volume
        while self.k.volume or self.k.up or self.k.down:
            if 0==pressed:
                if self.k.up:
                    pressed=1
                elif self.k.down:
                    pressed=2
            if 0 != pressed:
                pressure = (self.k.notes_val[[None, 13, 12][pressed]])>>4 #level of either "up" or "down", depending on which one is pressed
                if pressure>peg: #TODO: add time/value filtering?
                    peg=pressure
                    vol = min(127, max(0, self.p.volume + (peg if 1==pressed else -peg)))
                    if master:
                        self.p.set_master_volume(vol)
                    else:
                        pass #TODO: channel volume?
                    self.d.disp_slider(vol, vname)
            self.loop(freeze_display=True)
            if 0 != pressed and not (self.k.up or self.k.down):
                self.p.volume = vol
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
        self.d.text("Melody mode")
        self.p.start_melody()
        self.p.update_melody()
        while None != self.k.current_note_key:
            self.loop()
            self.p.update_melody()
        self.p.stop_melody()

    def loop_drum(self):
        self.d.text("Drum")
        while None != self.k.current_note_key:
            for i in on_bits(self.k.bitmap&~self.k.bitmap_old):
                self.d.text(self.p.play_drum(i))
            self.loop()
            if self.k.current_note_key == None:
                self.check_function_keys()

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
            print("Looper not implemented")
#            self.loop_looper()  #TODO          
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
#    watchdog.timeout=2 # seconds
#    watchdog.mode = watchdog.WatchDogMode.RAISE
    
#     try:
    o = PocketOrgan()
    o.loop_waiting()
#TODO:
#    except watchdog.WatchDogTimeout:
#        print("Watchdog timeout. Turning off")
#        board.power_off.value = False #Turn off. Only works if no USB power supply.
#TODO: re-enable, add QR code?
#     except Exception as e:
#         import sys, os, pyb
#         fd = open("err.txt", "w")
#         fd.write(str(os.uname()))
#         fd.write("\nBattery: {:1.3}V; USB: {:1.3}V\n".format(board.vbat(), board.vusb()))
#         fd.write("USB connected\n" if pyb.USB_VCP().isconnected() else "USB NOT connected\n")
#         t=ticks_ms()//1000
#         fd.write("Uptime: {:02}h{:02}m{:02}s\n".format(t//3600, t%3600//60, t%60))
#         fd.write("HW version: {}\n".format(board.version))
#         sys.print_exception(e, fd)
#         fd.close()
#         fd = open("err.txt","r")
#         d.text(fd.read()[-300:-1], err=True)
#         raise(e)
        
start()

#end