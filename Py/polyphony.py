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
    def __init__(self, keyboard, display):
        self.pending = []   #list of notes scheduled for playing in the future
                            #format of each note: (note, velocity, ticks_ms)
        self.midi = midi.Midi()
        self.chord_channel = 0
        self.melody_channel = 1
        self.k = keyboard
        self.d = display
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]
        self.chord_names = ["C", "D", "E", "F", "G", "A", "B", "C"]
        self.melody_keys_transpose = bytearray(8) #for keeping track of how which key was played

        self.set_instr(22)
        
    def start_chord(self):
        root = self.scale[self.k.current_note_key] + self.k.sharp #current_note_key should not be None
        chord = [root,
                         root + 4 - bool(self.k.minor),
                         root + 7
                         ]
        if self.k.seventh:
            chord.append(root+10)
        self.play_chord(chord, 64, 40)
        self.d.disp_chord(
        #print(
             self.chord_names[self.k.current_note_key] +
             ("#" if self.k.sharp else "") +
             ("m" if self.k.minor else "") +
             ("7" if self.k.seventh else "")
             )
    
    def play_chord(self, notes, velocity, timing): #timing = number of ms between successive notes
        """Starts playing a list of notes.
        The 1st one is played immediately, the following ones are spaced by timing (in milliseconds).
        """
        self.midi.note_on(self.chord_channel, notes[0], velocity) 
        for i, n in enumerate(notes[1:], start=1):
            self.pending.append((n, velocity, time.ticks_ms()+timing*i))
        
    def stop_chord(self):
        self.midi.all_off(self.chord_channel)
        self.pending = []
        self.d.clear()

    def start_note(self, i):
        transpose = 12*self.k.fifth + 12*self.k.seventh - 12*self.k.third - 12*self.k.minor + 1*self.k.sharp
        self.melody_keys_transpose[i] = transpose
        self.midi.note_on(self.melody_channel, self.scale[i]+transpose, 64)
    
    def stop_note(self, i):
        self.midi.note_off(self.melody_channel, self.scale[i]+self.melody_keys_transpose[i], 64)

    def stop_all_notes(self):
        self.midi.all_off(self.melody_channel)

    def set_instr(self, instr):
        self.midi.set_instr(self.chord_channel,  instr)
        self.midi.set_instr(self.melody_channel, instr)
        
    def set_volume(self, vol):
        print(vol)
        self.midi.set_controller(self.chord_channel, 7, vol)
        self.midi.set_controller(self.melody_channel, 7, vol)

    def loop(self):
        #Check if a note is due for playing, and play it. Assumes the notes are listed chronologycally.
        if len(self.pending):
            next = self.pending[0][2]
            if next <= time.ticks_ms():
                n = self.pending.pop(0)
                self.midi.note_on(self.chord_channel, n[0], n[1])
                
#end
                
