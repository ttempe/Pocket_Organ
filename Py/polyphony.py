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
    def __init__(self):
        self.pending = []   #list of notes scheduled for playing in the future
                            #format of each note: (channel, note, velocity, ticks_ms)
        self.midi = midi.Midi()
        
    def play_chord(self, channel, notes, velocity, timing): #timing = number of ms between successive notes
        """Starts playing a list of notes.
        The 1st one is played immediately, the following ones are spaced by timing (in milliseconds).
        """
        self.midi.note_on(channel, notes[0], velocity) 
        for i, n in enumerate(notes, start=1):
            self.pending.append((channel, n, velocity, time.ticks_ms()+timing*i))
    
    def stop_chord(self, channel):
        self.pending = []
        #TODO: send a midi signal to kill all notes from this channel
    
    def loop(self):
        #Check if a note is due for playing, and play it. Assumes the notes are listed chronologycally.
        next = self.pending[0][3]
        if next <= time.ticks_ms():
            n = self.pending.pop(0)
            self.midi.note_on(n[0], n[1], n[2])
        