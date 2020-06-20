import time

class Metronome:
    def __init__(self, midi):
        self.midi = midi
        self.timestamp = 0
        self.bpm = 110
        self.beat_duration = 60000//self.bpm
        self.enable = False
        
        
    def set_bpm(self, bpm):
        self.bpm = bpm
        self.beat_duration = 60000/bpm
        
    def on(self):
        self.enable = True
        self.start_timestamp = time.ticks_ms()
    
    def off(self):
        self.enable = False
    
    def loop(self):
        t = time.ticks_ms()
        if self.enable:
            if t - self.timestamp > self.beat_duration:
                if t - self.timestamp - 100 < self.beat_duration:
                    self.midi.note_on(9, 76, 64)
                self.timestamp = t - (t % self.beat_duration)

    def quantize(self, time):
        #TODO
        return time
        
#End
