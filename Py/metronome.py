import time

class Metronome:
    def __init__(self, midi):
        self.midi = midi
        self.bpm = 110
        self.beat_duration = 60000//self.bpm #in ms
        self.enable = False
        self.last_beat = time.ticks_ms()
        self.beats = 0 #nb of beats since device was turned on
        self.beat_divider = 48 #the smallest unit of time is beat_duration/beat_divider
        self.now = 0 #ticks, expressed in beats
        
    def set_bpm(self, bpm):
        self.bpm = bpm
        self.beat_duration = 60000/bpm
        
    def on(self):
        self.enable = True
    
    def off(self):
        self.enable = False
    
    def loop(self):
        t = time.ticks_ms()
        d = (t - self.last_beat)//self.beat_duration
        if d:
            self.last_beat += d * self.beat_duration
            self.beats += d
            self.start_of_beat = self.beats * self.beat_divider
            if self.enable:
                self.midi.note_on(9, 76, 64)
        #TODO: toggle NoteOff slightly after each beat?
        self.now = self.beats*self.beat_divider + (t-self.last_beat)//self.beat_divider

    def quantize(self, time):
        "Round a timestamp to the nearest beat"
        return round(time/self.beat_duration)*self.beat_duration
    
    def time_to_beats(self, t):
        return (t*self.beat_divider)//self.beat_duration
            
#End
