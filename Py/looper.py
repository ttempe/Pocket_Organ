import time

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i
#TODO:
# * record timestamps in nb of beats (fixed-point) instead of nb of millisecond, to allow tempo tricks

class Looper:
    def __init__(self, backlight, display):
        self.record_channels = [(2,3), (4,5), (6,7), (8,10), (11,12), (13, 14), (0, 1)]
        self.chord_channel, self.melody_channel = self.record_channels[-1]
        #self.drum_channel = 9 #This is imposed by General MIDI
        self.p = None #Polyphony; Assigned by Polyphony itself, upon initializatinon
        self.b = backlight
        self.d = display
        self.recorded = 0     #bit map 
        self.playing = 0      #bit map
        self.recording = None #channel number
        self.recording_start_timestamp = None
        self.records = [[],[],[],[],[],[],[],[]]
        self.cursors = [0, 0, 0, 0, 0, 0, 0, 0]
        self.durations = [0, 0, 0, 0, 0, 0, 0, 0]
        self.durations_max = 0
        self.loop_start = [0,0,0,0,0,0,0,0] #Timestamps
        self.toggle_play_waitlist = 0 #bit map
        self.loop_names = ["C", "D", "E", "F", "G", "A"]
   
    def append(self, event):
        if None != self.recording:
            if not self.recording_start_timestamp:
                #Set the start of the recording loop
                if self.playing:
                    #Align the starting point with the shortest loop
                    self.recording_start_timestamp = max(self.loop_start)
                else:
                    #Align with the nearest beat
                    self.recording_start_timestamp = self.p.metronome.quantize(self.p.metronome.timestamp)
                self.p.set_instr(self.p.instr)
                self.p.set_volume(self.p.volume)
            t = time.ticks_ms()-self.recording_start_timestamp
            print (t);time.sleep_ms(10) 
            self.records[self.recording].append([t, event])
    
    def display(self):
        #As seen from the player:
        #red = recording
        #orange = recorded and paused
        #green = recorded and playing
        
        #This translates to:
        #Green = (recorded or playing) and not recording
        #Red = recording or (recorded and not playing)
        playing = self.playing ^ self.toggle_play_waitlist
        recording = (1 << self.recording) if (self.recording!=None) else 0
        green = (self.recorded | playing) & ~recording
        red =  recording | (self.recorded & ~playing)
        self.b.display( red, green)

    def loop_exists(self, n):
        "was that loop recorded already?"
        return self.recorded & (1<<n)

    def delete_track(self, n):
        self.records[n]=[]
        self.recorded &= ~(1<<n)
        self.durations[n] = 0
        self.playing &= ~(1<<n)
        self.toggle_play_waitlist &= ~(1<<n)
        self.display()
        self.d.text("Loop {}\ndeleted".format(self.loop_names[n]))

    def start_recording(self, n):
        if 6 <= n:
            self.d.text("Can't record\na loop on this\nkey", 2000)
        else:
            self.recording = n
            self.recording_start_timestamp = None
            self.chord_channel, self.melody_channel = self.record_channels[n]
            self.display()
            self.d.text("Start recording\nloop {}".format(self.loop_names[n]), 2000)
            self.p.metronome.on()
            #TODO: make sure this gets recorded somewhere in Flash 
            #for c in self.record_channels[n]:
            #    self.p.midi.set_instr(c, self.p.instr)
            #    self.p.midi.set_controller(c, 7, self.p.volume)#Set volume
        

    def stop_recording(self):
        "Returns whether a track was being recorded"
        if self.recording != None:
            if len(self.records[self.recording])>4:
                #Loop was actually recorded
                self.d.text("Finish recording\nloop {}".format(self.loop_names[self.recording]), 2000)
                self.recorded |= 1<<self.recording
                self.chord_channel, self.melody_channel = self.record_channels[-1]
                self.durations[self.recording] = max(
                    self.p.metronome.quantize(time.ticks_ms())-self.recording_start_timestamp,
                    self.p.metronome.beat_duration) #Make sure no recording is shorter than one beat
                self.durations_max = max(self.durations)
                #TODO: Start playing immediately
                self._start_playing(self.recording)
            else:
                self.d.text("Nothing recorded", 2000)
            self.recording = None
            self.p.metronome.off()
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
        print(hex(self.playing))
        self.playing |= 1<<i
        print(hex(self.playing))
        self.cursors[i]=0
        self.loop_start[i] = self.p.metronome.quantize(time.ticks_ms())

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
            print("Now starting playing loop {}".format(i))
            self._start_playing(i)
            self.toggle_play_waitlist &= ~(1<<i)
            print("Loop", i, "will be starting at", self.loop_start[i])
        for i in bits(self.toggle_play_waitlist & self.playing):
            #loops to stop playing now
            print("Now stopping playing loop {}".format(i))
            #send an "all notes off" midi command
            self._stop_playing(i)
        self.toggle_play_waitlist = 0
        self.b.off()

    def pop_notes(self, loop, ticks):
        now = ticks-self.loop_start[loop]
        c = self.cursors[loop]
        ret = []
        t, msg = self.records[loop][c]
        #print("loop", loop, "start: ", t, "Now: ", now, "(", ticks, self.loop_start[loop], ")");time.sleep_ms(50)
        while t<= now:
            #print(c, t, msg)
            self.p.midi.inject(msg)
            c+=1
            if c>=len(self.records[loop]):
                c=0
                self.loop_start[loop] += self.durations[loop]
                break 
            t, msg = self.records[loop][c]
        self.cursors[loop]=c
    
    def loop(self):
        #Play active loops
        ticks = time.ticks_ms()
        for i in range(0,6):
            if self.playing & (1<<i):
                self.pop_notes(i, ticks)


#End
