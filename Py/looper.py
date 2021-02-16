import time
import flash_W25Q128 as flash
import indicator

#TODO:
# * check whether the IC is free before deleting/starting recording a loop
#
# * allocate the channels to the loops dynamically, only use the ones you need -> extra flexibility
# * alternately, set some channels to percussion only and/or melody only.
# * refuse to record if some loops are recorded but none is playing?
#
# * save loop state to microcontroller flash

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i

class Looper:
    def __init__(self, backlight, display):
        self.record_channels = [(2,3), (4,5), (6,7), (8,10), (11,12), (13, 14), (0, 1)]
        self.chord_channel, self.melody_channel = self.record_channels[-1]
        self.drum_channel = 9 #This is imposed by General MIDI
        self.p = None #Polyphony; Assigned by Polyphony itself, upon initializatinon
        self.b = backlight
        self.d = display
        self.f = flash.Flash(8)
        self.recorded = 0     #bit map 
        self.playing = 0      #bit map
        self.recording = None #channel number
        self.recording_start_timestamp = None
        self.record_lengths = [0]*8
        self.cursors = [0]*8
        self.durations = [0]*8
        self.loop_start = [0]*8 #Timestamps
        self.toggle_play_waitlist = 0 #bit map
        self.loop_names = ["C", "D", "E", "F", "G", "A"]
        self.quick_time = None

        #TODO: load recorded tracks status here

        #Check & fix inconsitent flash disk state

        if self.f.check_erased(self.loop_exists):
            #Whole flash is being erased. Make sure we don't expect any tracks
            self.recorded = 0
        indicator.Indicator(self.d, ["flash_blank", "flash_w"], self.indicator_status) #The indicator registers itself with display
    
    def indicator_status(self):
        return 1 if self.f.busy() else 0
    
    def append(self, event):
        #Called by Polyphony for every Midi event
        if None != self.recording:
            #We are in the process of recording
            if not self.recording_start_timestamp:
                #This is the 1st note in the loop. Use it as the start date.
                self.recording_start_timestamp = self.p.metronome.now
            if self.quick_time != None:
                #Quick loop recording
                t = self.quick_time
            else:
                t = self.p.metronome.now - self.recording_start_timestamp
            #print ("Note time: ", self.p.metronome.now/48, "-", self.recording_start_timestamp/48, "=", t/48, "note:", event);time.sleep_ms(10)
            self.f.record_message(t, event)
            self.record_lengths[self.recording]+=1

    def display(self):
        #Display loops status on the note keys backlight
        #red    = recording
        #orange = recorded and paused
        #green  = recorded and playing
        
        #This translates to:
        #Green component = (recorded or playing) and not recording
        #Red component   = recording or (recorded and not playing)
        playing = self.playing ^ self.toggle_play_waitlist
        recording = (1 << self.recording) if (self.recording!=None) else 0
        green = (self.recorded | playing) & ~recording
        red =  recording | (self.recorded & ~playing)
        self.b.display( red, green)

    def loop_exists(self, n):
        "was that loop recorded already?"
        return self.recorded & (1<<n)

    def delete_track(self, n):
        if not self.f.busy():
            self.f.erase(n)
            self.recorded &= ~(1<<n)
            self.durations[n] = 0
            self.playing &= ~(1<<n)
            self.toggle_play_waitlist &= ~(1<<n)
            self.display()
            self.d.text("Loop {}\ndeleted".format(self.loop_names[n]))

    def start_recording(self, n):
        #This only sets the stage.
        #The start of recording really happens in self.append()
        #Returns True on success
        if n >= 6:
            #Key Ut can't have a loop, because each loop takes 2 MIDI channels
            #(one for chords and one for melody), and channel 9 is reserved for drums
            self.d.text("Can't record\na loop on this\nkey", 2000)
            return False
        else:
            self.recording = n
            self.recording_start_timestamp = None
            self.chord_channel, self.melody_channel = self.record_channels[n]
            self.p.set_instr(self.p.instr)
            self.p.set_volume(self.p.volume)

            self.display()
            self.d.text("Start recording\nloop {}".format(self.loop_names[n]), 2000)
            self.p.metronome.on()
            self.f.start_recording(self.recording)
            self.quick_time = None
            return True
    
    def start_recording_quick(self):
        #Called after start_recording. Switches to "quick looper" mode.
        self.quick_time = 0
        self.recording_start_timestamp = 0
    
    def quick_increment(self):
        #Move quick mode to next chord
        self.quick_time += self.p.metronome.beat_divider
    
    def stop_recording(self):
        "Returns whether a track was successfully recorded"
        if self.recording != None:
            if self.record_lengths[self.recording]>0:
                #Loop was actually recorded
                now = self.p.metronome.now
                self.d.text("Finish recording\nloop {}".format(self.loop_names[self.recording]), 2000)
                self.recorded |= 1<<self.recording
                self.chord_channel, self.melody_channel = self.record_channels[-1]
                #Add a final event with a duration long into the future, to simplify the code in self.pop_note()
                self.f.record_message(self.p.metronome.now + 1000, b"  ")
                self.record_lengths[self.recording] += 1
                #Set new loop duration
                if self.quick_time:
                    d = self.quick_time
                else:
                    d = now - self.recording_start_timestamp
                #print("Raw duration: ", d/48, "=", now/48, "-", self.recording_start_timestamp/48)
                d = self.p.metronome.round_to_beats(d)
                if self.playing:
                    #round up to a multiple of the shortest duration
                    #TODO: make that a sub-multiple as well?
                    #TODO: Handle the case where I stopped playing the shortest loop before recording. Record the reference "min duration" for each loop? Mandate that at least one recorded loop is playing?
                    min_duration = min([ self.durations[i] for i in bits(self.playing)])
                    #divide by 2 if possible
                    if min_duration%(self.p.metronome.beat_divider*2):
                        min_duration /= 2
                    self.durations[self.recording] = round(d/min_duration)*min_duration
                    #print("Duration: ", d/48, ", rounded to", self.durations[self.recording]/48)
                else:
                    #Make sure no recording is shorter than one metronome beat
                    #print("Duration: ", d/48)
                    self.durations[self.recording] = max( d, self.p.metronome.beat_divider)
                self.loop_start[self.recording] = self.recording_start_timestamp+self.durations[self.recording]
                self._start_playing(self.recording)
                self.cursors[self.recording] = 0
            else:
                self.d.text("Nothing recorded", 2000)
            #print("Recorded", self.record_lengths[self.recording], "events")
            self.recording = None
            self.p.metronome.off()
            self.f.finish_recording()
            return True
        else:
            return False

    def toggle_play(self, key):
        if (self.playing ^ self.toggle_play_waitlist) & (1<<key):
            #loop was playing. Stop it.
            self.d.text("Stop playing\nloop {}\n".format(self.loop_names[key]), 2000)
        else:
            #Loop was not playing. Start it.
            self.d.text("Start playing\nloop {}\n".format(self.loop_names[key]), 2000)
        self.toggle_play_waitlist ^= 1<<key
        if not(self.playing & (1<<key)):
            #loop was really not playing.
            self.d.text("Hold to delete", 7, 2000)
        self.display()

    def _start_playing(self, i):
        self.playing |= 1<<i
       
    def _stop_playing(self, i):
        self.playing &= ~(1<<i)
        for c in self.record_channels[i]:
            self.p.midi.all_off(c)
            
    def apply_ui(self):
        """
        Executes all the pending play toggle actions.
        Called when the user releases the "loop" button.
        """
        for i in bits(self.toggle_play_waitlist & (~self.playing)):
            #loops to start playing now
            #print("Now starting playing loop {}".format(i))
            self._start_playing(i)
            self.toggle_play_waitlist &= ~(1<<i)
            #print("Loop", i, "will be starting at", self.loop_start[i])
        for i in bits(self.toggle_play_waitlist & self.playing):
            #loops to stop playing now
            #print("Now stopping playing loop {}".format(i))
            #send an "all notes off" midi command
            self._stop_playing(i)
        self.toggle_play_waitlist = 0
        self.b.light_none()

    def pop_notes(self, loop):
        now = self.p.metronome.now - self.loop_start[loop]
        c = self.cursors[loop]
        if now > self.durations[loop]:
            #jump back to the start of the loop
            #print("Restarting loop", loop, "start", self.loop_start[loop]/48, "duration: ", self.durations[loop]/48, "now: ", now/48, "ticks:", self.p.metronome.now/48)
            c=0
            self.loop_start[loop] += ((self.p.metronome.now-self.loop_start[loop])//self.durations[loop])*self.durations[loop]
            now = self.p.metronome.now - self.loop_start[loop]
            #print("Restarted. now: ", now/48, "start", self.loop_start[loop]/48, "index: ", c, "ticks:", self.p.metronome.now/48)        
            #Stop all playing notes, just in case
            for d in self.record_channels[loop]:
                self.p.midi.all_off(d)
        t, msg = self.f.read_message(loop, c)
        while t <= now:
            #In case there are multiple messages to be played now:
            if self.playing & (1<<loop):
                #actually play the note
                #print("Loop", loop, "playing note n.", c, "now: ", now/48, "recorded time: ", t/48, "ticks:", self.p.metronome.now/48)
                self.p.midi.inject(msg)
            c+=1
            t, msg = self.f.read_message(loop, c)
        self.cursors[loop]=c
    
    def loop(self):
        #Play active loops
        #print("Tick: ", self.p.metronome.now/48);time.sleep_ms(100)
        for i in range(8):
            if self.recorded & (1<<i):
                #Walk through all recorded loops
                self.pop_notes(i)
        self.f.loop()


#End
