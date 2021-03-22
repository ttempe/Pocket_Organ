import time
import midi
import metronome

# Only one chord is ever sent at once.
# TODO:
# * have Midi return the MIDI message string, and have Polyphony call the looper directly
# * update the chord shape when the user toggles the 3rd/5th/7th buttons

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i

class Polyphony:
    def __init__(self, keyboard, display, looper):
        self.pending = []   #list of notes scheduled for playing in the future
                            #format of each note: (note, velocity, ticks_ms)
        self.k = keyboard
        self.d = display
        self.l = looper
        self.l.p = self
        self.midi = midi.Midi()
        self.metronome = metronome.Metronome(self.midi)
        self.scale = [60, 62, 64, 65, 67, 69, 71, 72]
        self.chord_names = ["C", "D", "E", "F", "G", "A", "B", "C"]
        self.melody_keys_transpose = bytearray(8) #for keeping track of how which key was played
        self.instr = 22
        self.set_instr(self.instr)
        self.volume = 64
        self.set_volume(self.volume)
        #TODO: move the drum names to instr_names.py
        self.drums = [("Snare", 38), ("Bass drum", 36), ("Ride cymbal", 51), ("Low tom", 45), ("Mid tom", 48), ("High tom", 50), ("Open hi-hat", 46), ("Closed hi-hat", 42), ("Crash cymbal", 49) ]
        self.chord = [] #Currently playing chord
        self.strum_chord = [] #same chord, but with enough notes to cover all strumming keys
        self.strum_mute_old = 0
        self.strum_keys_old = 0
        self.default_velocity = 64
        
        #For continuous expression control
        self.playing_chord = None
        self.expr1_old = self.default_velocity
        self.expr1_time = 0

    def start_chord(self, quick_mode=False):
        def round_note(n):
            return n%12 + 60
        self.playing_chord = self.k.current_note_key
        root = self.scale[self.k.current_note_key] + self.k.sharp #current_note_key should not be None
        
        #Here is the logic to determine the chord shape
        aug = self.k.fifth and not self.k.minor
        dim = self.k.fifth and self.k.minor
        sus4 = self.k.third and not self.k.minor
        sus2 = self.k.third and self.k.minor

        #Triad
        self.chord = [   round_note(root),
                         round_note(root + 4 - self.k.minor + sus4 - sus2*2),
                         round_note(root + 7 + aug - dim)
                         ]
        #Seventh
        if self.k.seventh:
            self.chord.append(round_note(root+10-self.k.minor))
        if quick_mode:
            self.play_chord(self.default_velocity, 0)
        elif not self.k.strum_mute and not self.k.strum_keys:
            self.play_chord(self.default_velocity, 40)
        else:
            self.strum_keys_old = 0 #Play all keys on the next loop()
        self.d.disp_chord(
             self.chord_names[self.k.current_note_key] +
             ("#" if self.k.sharp else "") +
             ("m" if self.k.minor else "") +
             ("7" if self.k.seventh else "")
             )
        #extend that chord to cover all strumming keys
        if len(self.chord)<self.k.nb_strum_keys:
            self.strum_chord = [self.chord[0]-12, self.chord[1]-12]
            self.strum_chord.extend(self.chord)
            incr = 12
            while len(self.strum_chord)<self.k.nb_strum_keys:
                for n in self.chord:
                    self.strum_chord.append(n+incr)
                incr +=12

    def play_chord(self, velocity, timing): #timing = number of ms between successive notes
        """Starts playing all notes for the chord.
        The 1st one is played immediately, the following ones are spaced by timing (in milliseconds).
        """
        self.l.append(self.midi.note_on(self.l.chord_channel, self.chord[0], velocity))
        for i, n in enumerate(self.chord[1:], start=1):
            if timing:
                self.pending.append((n, velocity, time.ticks_ms()+timing*i))
            else:
                self.l.append(self.midi.note_on(self.l.chord_channel, n, velocity))                
        
    def stop_chord(self):
        self.l.append(self.midi.all_off(self.l.chord_channel))
        self.pending = []
        self.d.clear()
        self.strum_chord = []
        self.playing_chord = None
        self.expr1_none=-10

    def start_note(self, i):
        transpose = 12*self.k.fifth + 12*self.k.seventh - 12*self.k.third - 12*self.k.minor + 1*self.k.sharp
        self.melody_keys_transpose[i] = transpose
        self.l.append(self.midi.note_on(self.l.melody_channel, self.scale[i]+transpose, self.default_velocity))
    
    def stop_note(self, i):
        self.l.append(self.midi.note_off(self.l.melody_channel, self.scale[i]+self.melody_keys_transpose[i], self.default_velocity))

    def stop_all_notes(self):
        self.l.append(self.midi.all_off(self.l.melody_channel))
        
    def play_drum(self, note):
        name, note = self.drums[note]
        self.l.append(self.midi.note_on(self.l.drum_channel, note, self.default_velocity))
        return name

    def set_instr(self, instr):
        self.instr = instr
        self.midi.set_instr(self.l.chord_channel,  instr)
        self.midi.set_instr(self.l.melody_channel, instr)
        
    def set_volume(self, vol):
        #TODO: if changing in quick succession, only append every 0.1s (requires making a queue of volume changes)
        self.midi.set_controller(self.l.chord_channel, 7, vol)
        self.midi.set_controller(self.l.melody_channel, 7, vol)

    def set_master_volume(self, vol):
        #TODO: if changing in quick succession, only append every 0.1s (requires making a queue of volume changes)
        self.midi.set_master_volume(vol)
        
    def loop(self):
        self.metronome.loop()
        
        #Are we strumming?
        if self.strum_chord:
            #If the user just activated the strum mute:
            if self.k.strum_mute and not self.strum_mute_old:
                #Mute any key that's not being held
                for i, k in enumerate(self.strum_chord):
                    if not((self.k.strum_keys>>i)&1):
                        self.midi.note_off(self.l.chord_channel, k, self.default_velocity)
            #update newly released strum keys
            elif self.k.strum_mute:
                #Keys that were in _old but are no longer in _new
                for i in bits(self.strum_keys_old & (~self.k.strum_keys)):
                    self.midi.note_off(self.l.chord_channel, self.strum_chord[i], self.default_velocity)

            #update newly strummed keys
            #TODO: Apply the current velocity
            for i in bits(self.k.strum_keys & (~self.strum_keys_old)):
                self.midi.note_on(self.l.chord_channel, self.strum_chord[i], self.default_velocity)
                
            self.strum_mute_old = self.k.strum_mute
            self.strum_keys_old = self.k.strum_keys
        
        #Non-strummed chord:
        #Check if a note is due for playing, and play it. Assumes the notes are listed chronologycally.
        if len(self.pending):
            next = self.pending[0][2]
            if next <= time.ticks_ms():
                n = self.pending.pop(0)
                self.l.append(self.midi.note_on(self.l.chord_channel, n[0], n[1]))
        
        #Are we playing something? Update effects:
        if self.playing_chord != None:
            expr1 = self.k.notes_val[self.playing_chord]
            if abs(expr1 - self.expr1_old) > 1 and (time.ticks_ms() - self.expr1_time > 10):
                print(expr1)
                self.expr1_old = expr1
                self.expr1_time = time.ticks_ms()
                self.midi.set_controller(self.l.chord_channel, 11, int(127*expr1//self.k.notes_max))
                
                
#end
