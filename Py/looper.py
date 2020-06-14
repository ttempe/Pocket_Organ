import time

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i

class Looper:
    def __init__(self, backlight):
        self.chord_channel = 14
        self.melody_channel = 15
        self.m = None #Midi;  Assigned by Midi itself, upon initialization
        self.b = backlight
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
        #red = recording
        #orange = recorded and paused
        #green = recorded and playing
        playing = self.playing
        rec = (1 << self.recording) if self.recording else 0
        red =  (self.recorded & ~self.playing) | rec
        green = self.recorded & self.playing & ( ~rec) 
        self.b.display( red, green)
    
    def playback(self):
        pass

    def delete_track(self, n):
        self.records[n]=[]
        self.recorded &= ~(1<<n)
        self.playing &= ~(1<<n)

    def start_recording(self, n):
        self.recording = n
        self.recording_start_timestamp = None

    def apply_ui(self):
        """
        Executes all the pending play toggle actions.
        Called when the user releases the "loop" button.
        """
        if self.playing == 0 and self.toggle_play_waitlist != 0: #No loop was playing
            self.loop_start_timestamp = time.tick_ms()
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

#End
