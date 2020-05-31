import time
import midi

# This code assumes only one chord will ever be sent at once.

# TODO:
# * send the notes through the looper, in case they need to be recorded
#   (Only the looper knows which channel you're currently playing on)
#   (single notes must probably be sent to a separate channel, to allow overlaying them with chords)
# * convert the note_key number to actual midi notes
# * manage the playing of single notes.
#   Record which modifiers (sharp, octave+/-) were used for each key,
#   to turn them off gracefully


class Polyphony:
    def __init__(self, keyboard):
        self.pending = []   #list of notes scheduled for playing in the future
                            #format of each note: (note, velocity, ticks_ms)
        self.midi = midi.Midi()
        self.chord_channel = 0
        self.melody_channel = 1
        self.k = keyboard
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]
        
    def start_chord(self):
        root = self.scale[self.k.current_note_key] #current_note_key should not be None
        self.play_chord([root,
                         root + 4 - bool(self.k.minor),
                         root + 7
                         ], 64, 40)
    
    def play_chord(self, notes, velocity, timing): #timing = number of ms between successive notes
        """Starts playing a list of notes.
        The 1st one is played immediately, the following ones are spaced by timing (in milliseconds).
        """
        self.midi.note_on(self.chord_channel, notes[0], velocity) 
        for i, n in enumerate(notes[1:], start=1):
            self.pending.append((n, velocity, time.ticks_ms()+timing*i))
    
   