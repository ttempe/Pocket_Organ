


class Looper:
    def __init__(self):
        self.chord_channel = 0
        self.melody_channel = 1
        
        
    
    def append(self, event):
        channel = event[0]&0x0F
        