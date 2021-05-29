import time
import flash_W25Q128 as flash
import ustruct
import board

#TODO:
# * when some loops are recorded but none is playing:
#   * refuse to record (to keep them in sync)
#   * restart playing at the beginning
# * Queue delete operations to allow successive deletion of multiple tracks

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
        self.f = flash.Flash(8, display)
        
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

        self.load()
        
        #Check & fix inconsitent flash disk state
        if self.f.check_erased(self.loop_exists):
            #Whole flash is being erased. Make sure we don't expect any tracks
            self.recorded = 0

    def save(self):
        #Record loops state to flash IC: self.recorded, self.durations
        #Recording is scheduled, but may not happen immediately.
        #If the user turns off the instrument before saving is finished, the fact that there is no data will be detected during loading.
        print("Saving: ", self.recorded, self.durations)
        self.f.state_erase()
        buf= bytearray(4*(1+len(self.durations)))
        ustruct.pack_into("I", buf, 0, self.recorded)
        for i, d in enumerate(self.durations):
            ustruct.pack_into("I", buf, i*4+4, d)
        self.f.state_record(buf)
        
    def load(self):
        #Load back loops state from flash IC.
        if self.f.state_read(0,1)[0] == 255:
            if board.verbose:
                print("Loading failed: no loops recorded")
            #Check if there's anything written at all. Assume the flash is erased to value 0xFF, which is not a valid value for the 1st octet.
        else:
            self.recorded = ustruct.unpack_from("I", self.f.state_read(0, 4))[0]
            for i in range(len(self.durations)):
                self.durations[i] = ustruct.unpack_from("I", self.f.state_read(i*4+4, 4))[0]
            print("Loaded:", self.recorded, self.durations)

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
        if self.f.busy():
            self.d.text("Delete failed")
            self.d.text("Device busy. Try again in a few seconds", 1, tip=True)
        else:
            self.recorded &= ~(1<<n)
            self.durations[n] = 0
            self.playing &= ~(1<<n)
            self.toggle_play_waitlist &= ~(1<<n)
            self.display()
            self.save()
            self.f.erase(n) #Start erasing the memory prior to the next loop
            self.d.text("Loop {} deleted".format(self.loop_names[n]))

    def start_recording(self, n):
        #This only sets the stage.
        #The start of recording really happens in self.append()
        #Returns True on success
        if n >= 6:
            #Key Ut can't have a loop, because each loop takes 2 MIDI channels
            #(one for chords and one for melody), and channel 9 is reserved for drums
            self.d.text("Can't record a loop on this key")
            return False
        elif self.f.busy():
            self.d.text("Can't record")
            self.d.text("Device busy. Try again in a few seconds", 1, tip=True)
        else:
            self.recording = n
            self.recording_start_timestamp = None
            self.chord_channel, self.melody_channel = self.record_channels[n]
            self.p.set_instr(self.p.instr)
            self.p.set_volume(self.p.volume)

            self.display()
            self.d.text("Start recording loop {}".format(self.loop_names[n]))
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
                self.d.text("Finished recording loop {}".format(self.loop_names[self.recording]))
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
                d = self.p.metronome.round_to_beats(d)
                if self.playing:
                    #round up to a multiple of the shortest duration
                    #TODO: make that a sub-multiple as well?
                    #TODO: Handle the case where I stopped playing the shortest loop before recording:
                    #      Record the reference "min duration" for each loop?
                    #      Mandate that at least one recorded loop is playing?
                    min_duration = min([ self.durations[i] for i in bits(self.playing)])
                    #divide by 2 if possible
                    if min_duration%(self.p.metronome.beat_divider*2):
                        min_duration /= 2
                    self.durations[self.recording] = round(d/min_duration)*min_duration
                else:
                    #Make sure no recording is shorter than one metronome beat
                    self.durations[self.recording] = max( d, self.p.metronome.beat_divider)
                self.loop_start[self.recording] = self.recording_start_timestamp+self.durations[self.recording]
                self._start_playing(self.recording)
                self.cursors[self.recording] = 0
                self.save()
            else:
                self.d.text("Nothing recorded")
            self.recording = None
            self.p.metronome.off()
            self.f.finish_recording()
            return True
        else:
            return False

    def toggle_play(self, key):
        if (self.playing ^ self.toggle_play_waitlist) & (1<<key):
            #loop was playing. Stop it.
            self.d.text("Stop playing loop {}".format(self.loop_names[key]))
        else:
            #Loop was not playing. Start it.
            self.d.text("Start playing loop {}".format(self.loop_names[key]))
        self.toggle_play_waitlist ^= 1<<key
        if not(self.playing & (1<<key)):
            #loop was really not playing.
            self.d.text("Hold to delete",2, tip=True)
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
            self._start_playing(i)
            self.toggle_play_waitlist &= ~(1<<i)
        for i in bits(self.toggle_play_waitlist & self.playing):
            #loops to stop playing now
            #send an "all notes off" midi command
            self._stop_playing(i)
        self.toggle_play_waitlist = 0
        self.b.light_none()

    def pop_notes(self, loop):
        now = self.p.metronome.now - self.loop_start[loop]
        c = self.cursors[loop]
        if now > self.durations[loop]:
            #jump back to the start of the loop
            c=0
            self.loop_start[loop] += ((self.p.metronome.now-self.loop_start[loop])//self.durations[loop])*self.durations[loop]
            now = self.p.metronome.now - self.loop_start[loop]
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
        for i in range(8):
            if self.recorded & (1<<i):
                #Walk through all recorded loops
                self.pop_notes(i)
        self.f.loop()


#End
