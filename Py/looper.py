import time

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i

class Looper:
    def __init__(self, backlight, display):
        self.chord_channel = 14
        self.melody_channel = 15
        self.m = None #Midi;  Assigned by Midi itself, upon initialization
        self.b = backlight
        self.d = display
        self.recorded = 0     #bit map 
        self.playing = 0      #bit map
        self.recording = None #channel number
        self.recording_start_timestamp = None
        self.records = [[],[],[],[],[],[],[], []] 
        self.loop_start_timestamp = 0
        self.toggle_play_waitlist = 0 #bit map
   
    def append(self, event):
        if self.recording:
            if not self.recording_start_timestamp:
                #Set the start of the recording loop
                #TODO: align it to the last metronome beat or start of loop playback
                self.recording_start_timestamp = time.ticks_ms()
            channel = event[0]&0x0F
            self.records[channel>>1].append([time.ticks_ms()-self.recording_start_timestamp, event])
    
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
    
    def playback(self):
        pass

    def loop_exists(self, n):
        "was that loop recorded already?"
        return self.recorded & (1<<n)

    def delete_track(self, n):
        self.records[n]=[]
        self.recorded &= ~(1<<n)
        self.playing &= ~(1<<n)
        self.toggle_play_waitlist &= ~(1<<n)
        self.display()
        self.d.text("Loop {}\ndeleted".format(n))

    def start_recording(self, n):
        if 7 == n:
            self.d.text("Can't record\na loop on this\nkey", 2000)
        self.recording = n
        self.recording_start_timestamp = None
        self.display()
        self.d.text("Start recording\nloop {}".format(n), 2000)

    def stop_recording(self):
        "Returns whether a track was being recorded"
        if self.recording != None:
            self.d.text("Finish recording\nloop {}".format(self.recording), 2000)
            self.recorded |= 1<<self.recording
            self.recording = None

    def toggle_play(self, key):
        if (self.playing ^ self.toggle_play_waitlist) & (1<<key):
            #loop was playing. Stop it.
            self.d.text("Stop playing\nloop {}\n".format(key), 2000)
        else:
            #Loop was not playing. Start it.
            self.d.text("Start playing\nloop {}\n".format(key), 2000)
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
        if self.playing == 0 and self.toggle_play_waitlist != 0: #No loop was playing
            self.loop_start_timestamp = time.ticks_ms()
        else: #Some loops were playing
            for i in bits(self.toggle_play_waitlist & (~self.playing)):
                print("Now start playing loop {}".format(i))
                #TODO: skip all past timestamps in that loop
                #use an iterator?
                #Skip from within the iterator? Initialize the iterator here?
            for i in bits(self.toggle_play_waitlist & self.playing):
                print("Now stop playing loop {}".format(i))
                #TODO: reset the cursor? Just ignore?
        self.playing ^= self.toggle_play_waitlist
        self.toggle_play_waitlist = 0
        self.b.off()

#End
