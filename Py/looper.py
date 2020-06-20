import time

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i

class Looper:
    def __init__(self, backlight, display):
        self.record_channels = [(2,3), (4,5), (6,7), (8,10), (11,12), (13, 14), (0, 1)]
        self.chord_channel, self.melody_channel = self.record_channels[-1]
        #self.metronome_channel = 9 #This is imposed by General MIDI
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
        self.loop_start_timestamp = 0
        self.toggle_play_waitlist = 0 #bit map
        self.loop_names = ["C", "D", "E", "F", "G", "A"]
   
    def append(self, event):
        if None != self.recording:
            if not self.recording_start_timestamp:
                #Set the start of the recording loop
                #TODO: align it to the last metronome beat or start of loop playback
                self.recording_start_timestamp = self.p.metronome.timestamp
                t = 0
            else:
                t = self.p.metronome.quantize(time.ticks_ms()-self.recording_start_timestamp)
            self.records[self.recording].append([t, event])
            print(len(self.records[self.recording]));time.sleep_ms(30)
    
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
            #TODO: record the instrument and volume. Manage cases where the user changes the instr or volume while recording.
            #TODO: Check the "nothing recorder" message conditions, below
            self.display()
            self.d.text("Start recording\nloop {}".format(self.loop_names[n]), 2000)
            self.p.metronome.on()

    def stop_recording(self):
        "Returns whether a track was being recorded"
        if self.recording != None:
            if len(self.records[self.recording]):
                #Loop was actually recorded
                self.d.text("Finish recording\nloop {}".format(self.loop_names[self.recording]), 2000)
                self.recorded |= 1<<self.recording
                self.chord_channel, self.melody_channel = self.record_channels[-1]
                self.durations[self.recording] = self.p.metronome.quantize(time.ticks_ms()-self.recording_start_timestamp)
                self.durations_max = max(self.durations)
                #TODO: Start playing immediately
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

    def apply_ui(self):
        """
        Executes all the pending play toggle actions.
        Called when the user releases the "loop" button.
        """
        if 0 == self.playing and self.toggle_play_waitlist != 0:
            #No loop was playing, starting to play first loop
            self.cursors = [0, 0, 0, 0, 0, 0, 0, 0]
            self.loop_start_timestamp = time.ticks_ms()
        else: #Some loops were playing
            for i in bits(self.toggle_play_waitlist & (~self.playing)):
                print("Now starting playing loop {}".format(i))
                #TODO: skip all past timestamps in that loop
                #use an iterator?
                #Skip from within the iterator? Initialize the iterator here?
            for i in bits(self.toggle_play_waitlist & self.playing):
                print("Now stopping playing loop {}".format(i))
                #TODO: reset the cursor? Just ignore?
                #TODO: send a "all notes off" midi command
        self.playing ^= self.toggle_play_waitlist
        self.toggle_play_waitlist = 0
        self.b.off()

    def loop(self):
        #TODO: if you just finished recording a loop (while playing others), will its cursor be wrong?
        now = time.ticks_ms() - self.loop_start_timestamp
        if now > self.durations_max:
            self.loop_start_timestamp += self.durations_max
            now = time.ticks_ms() - self.loop_start_timestamp
            self.cursors = [0,0,0,0,0,0,0,0]
            
        #TODO: make this more pythonic
        #TODO: don't wait for the next cycle if multiple events need to be played together
        for loop in range(0, 6):
            c = self.cursors[loop]
            if len(self.records[loop]):
                #Loop exists
                t, n = self.records[loop][c]
                if t >= now:
                    #Found a note. Play it?
                    print("found", loop, t)
                    if self.playing & (1<<loop):
                        self.p.midi.inject(n)
                    c+=1
                    #if c>=len(self.records[loop]):
                    #    c=0
                    #self.cursors[loop] = c
                    #t, n = self.records[loop][c]
        

#End
