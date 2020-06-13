


class Looper:
    def __init__(self, backlight):
        self.chord_channel = 0
        self.melody_channel = 1
        self.m = None #Midi;  Assigned by Midi itself, upon initialization
        self.b = backlight
        
    
    def append(self, event):
        channel = event[0]&0x0F
    
    def playback():
        pass

    
#End
