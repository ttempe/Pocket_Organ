import time

#TODO:
# * allocate the channels to the loops dynamically, only use the ones you need -> extra flexibility
# * alternately, set some channels to percussion only and/or melody only.

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
        self.recorded = 0     #bit map 
        self.playing = 0      #bit map
        self.recording = None #channel number
        self.recording_start_timestamp = None
        self.records = [[],[],[],[],[],[],[],[]]
        self.cursors = [0, 0, 0, 0, 0, 0, 0, 0]
        self.durations = [0, 0, 0, 0, 0, 0, 0, 0]
        self.delta = [0,0,0,0,0,0,0,0] #Time deltas between respective loops, used to ensure they are aligned to each other
        self.durations_max = 0
        self.loop_start = [0,0,0,0,0,0,0,0] #Timestamps
        self.toggle_play_waitlist = 0 #bit map
        self.loop_names = ["C", "D", "E", "F", "G", "A"]
   
    def append(self, event):
        if None != self.recording:
            if not self.recording_start_timestamp:
                #This is where "start recording" really happens
                if self.playing:
                    #Set the delta from any playing loop
                    if self.playing:
                        #TODO: fix the delta calculation. Should not just use the same delta as someone else
                        self.delta[self.recording] = self.delta[next(bits(self.playing))]
                    else:
                        self.delta[self.recording] = 0
                    print("Delta set to", self.delta[self.recording])
                    
                    #Align the starting point with the most recent loop start
                    self.recording_start_timestamp = max(self.loop_start)
                else:
                    #Align with the nearest beat
                    self.recording_start_timestamp = self.p.metronome.now
                self.p.set_instr(self.p.instr)
                self.p.set_volume(self.p.volume)
            t = self.p.metronome.now - self.recording_start_timestamp
            #print ("Note time: ", self.p.metronome.now, "-", self.recording_start_timestamp, "=", t/self.p.metronome.beat_divider);time.sleep_ms(10) 
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
        #This only sets the stage.
        #The start of recording really happens in self.append()
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
        "Returns whether a track was successfully recorded"
        if self.recording != None:
            if len(self.records[self.recording])>4:
                #Loop was actually recorded
                self.d.text("Finish recording\nloop {}".format(self.loop_names[self.recording]), 2000)
                self.recorded |= 1<<self.recording
                self.chord_channel, self.melody_channel = self.record_channels[-1]
                
                #Set new loop duration
                d = self.p.metronome.start_of_beat - self.recording_start_timestamp
                if self.playing:
                    #round to a multiple of the shortest duration
                    #TODO: Handle the case where I stopped playing the shortest loop before recording. Record the reference "min duration" for each loop?
                    min_duration = min([ self.durations[i] for i in bits(self.playing)])
                    #TODO: accept half of mid_duration, in case it's a whole number of beats
                    self.durations[self.recording] = round(d/min_duration)*min_duration
                    print("Duration: ", d, ", rounded to", self.durations[self.recording])
                else:
                    #Make sure no recording is shorter than one metronome beat
                    self.durations[self.recording] = max( d, self.p.metronome.beat_divider)
                self.durations_max = max(self.durations)
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
        self.loop_start[i] = self.p.metronome.start_of_beat 

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

    def pop_notes(self, loop):
        now = self.p.metronome.now - self.loop_start[loop] - self.delta[loop]
        c = self.cursors[loop]
        ret = []
        t, msg = self.records[loop][c]
        #print("loop", loop, "start: ", t, "Now: ", now, "(", ticks, self.loop_start[loop], ")");time.sleep_ms(50)
        while t <= now:
            if self.playing & (1<<loop):
                #actually play the note
                print("Playing note n.", c, "time: ", t, "now: ", now)
                self.p.midi.inject(msg)
            c+=1
            if c>=len(self.records[loop]):
                #loop
                c=0
                self.loop_start[loop] += self.durations[loop]
                break 
            t, msg = self.records[loop][c]
        self.cursors[loop]=c
    
    def loop(self):
        #Play active loops
        for i in range(0,8):
            self.pop_notes(i)


#End
