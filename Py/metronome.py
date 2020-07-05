import time

class Metronome:
    def __init__(self, midi):
        self.midi = midi
        self.bpm = 110
        self.beat_duration = 60000//self.bpm #in ms
        self.enable = False
        self.last_beat = time.ticks_ms()     #in ms
        self.beats = 0         #nb of beats since device was turned on (fixed-point)
        self.now = 0           #nb beats (fixed-point)
        self.beat_divider = 48 #the smallest unit of time is beat_duration/beat_divider
        
    def set_bpm(self, bpm):
        self.bpm = bpm
        self.beat_duration = 60000/bpm        
        
    def on(self):
        self.enable = True
    
    def off(self):
        self.enable = False
        
    def toggle(self):
        self.enable = not(self.enable)
    
    def loop(self):
        t = time.ticks_ms()
        d = (t - self.last_beat)//self.beat_duration
        if d:
            self.last_beat += d * self.beat_duration #last start of beat (ms)
            self.beats += d * self.beat_divider      #last start of beat (fixed-point)
            if self.enable:
                self.midi.note_on(9, 76, 64)
        self.now = self.beats + ((t-self.last_beat)*self.beat_divider)//self.beat_duration
 
    def round_to_beats(self, d):
        "Round a fixed-point duration to the nearest number of beats"
        return round(d/self.beat_divider)*self.beat_divider
        
    def time_to_beats(self, t):
        return (t*self.beat_divider)//self.beat_duration
            
#End
