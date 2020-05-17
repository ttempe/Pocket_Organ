import keyboard
import midi

class PocketOrgan:
    def __init__(self):
        self.k = keyboard.Keyboard()
        self.midi = midi.Midi()
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]
#        for i in range(0, 9):
#            self.k.c1.set_threshold(i, 10)
        for i, v in enumerate([6, 6, 6, 12, 12, 12, 8, 8, 8]):
            self.k.c1.set_threshold(i, v)
    
    def play_notes(self):
        while 1:
            self.k.read()
            for i in range(0,3):
                if self.k.notes[i] and not self.k.notes_old[i]:
                    #start playing i
                    self.midi.note_on(0, self.scale[i])
                elif self.k.notes_old[i] and not self.k.notes[i]:
                    #stop playing i
                    self.midi.note_off(0, self.scale[i])

o = PocketOrgan()