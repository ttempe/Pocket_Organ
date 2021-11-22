import time
import midi
import metronome
import board
import instr_names

# Only one chord is ever sent at once.
# TODO:
# * when the note key is not pressed, turn off strumming notes as they are released
# * add modulation wheel expression (channel 1)
# * have Midi return the MIDI message string, and have Polyphony call the looper directly

scale = [60, 62, 64, 65, 67, 69, 71, 72]
        
def bits(n, range):
    "8-bit bit map iterator"
    for i in range(0, range):
        if n&(1<<i):
            yield i

def round_note(n):
    return n%12 + 60

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
        self.transpose = 0
        self.melody_keys_transpose = bytearray(8) #for keeping track of how which key was played
        self.instr = 22
        self.set_instr(self.instr)
        self.volume = 64
        self.set_volume(self.volume)
        self.chord = []       #Currently playing chord
        self.strum_chord = [] #same chord, but with enough notes to cover all strumming keys
        self.strum_mute_old = False
        self.strum_keys_old = 0   #bitmap
        self.strum_keys_all = 0   #bitmap of all active notes
        self.default_velocity = 64
        
        #For continuous expression control
        self.playing_chord_key  = None #Number of the key being pressed, from 0 to 7
        self.playing_notes  = 0
        self.expr1_old      = self.default_velocity
        #self.expr1_time     = 0
        self.expr_bend_old  = 0
        #self.expr_bend_time = 0
        self.bend_baseline  = 0
        self.chord_shape_name = ""
        self.chord_sharp    = 0 #-1 for bemol, +1 for sharp
        self.chord_sharp_old= 0 #same; this value corresponds to the last one displayed
        self.chord_disp_timestamp = 0
        
    def start_chord(self, quick_mode=False):
        self.playing_chord_key = self.k.current_note_key
        self.playing_chord_level = self.k.current_key_level
        self.root = round_note(self.k.current_key_level + self.transpose) #current_note_key should not be None

        #Determine the chord shape
        self.third = self.k.third
        self.sus4 = self.k.third and not self.k.minor
        self.sus2 = self.k.third and self.k.minor
        self.fifth = self.k.fifth
        self.aug = self.k.fifth and not self.k.minor
        self.dim = self.k.fifth and self.k.minor
        self.seventh = self.k.seventh
        self.minor = self.k.minor and not (self.dim or self.sus2)


        self.update_chord()

        if quick_mode:
            self.play_chord(self.default_velocity, 0)
        elif not self.k.strum_mute and not self.k.strum_keys:
            self.play_chord(self.default_velocity, 40)
        else:
            self.strum_keys_old = False #Play all keys on the next loop()

    def update_chord(self):
        #Triad
        self.chord = [   round_note(self.root),                                             #The root
                         round_note(self.root + 4 - self.minor + self.sus4 - self.sus2*2),  #The 3rd
                         round_note(self.root + 7 + self.aug - self.dim)                    #The 5th
                         ]
        #Seventh
        if self.seventh:
            self.chord.append(round_note(self.root+10-self.minor))
        if 7 == self.playing_chord_key:
            #When playing Ut, Move the root key up one octave to make it sound different from Do
            self.chord[0]=self.chord[0]+12

        #Map the chord over the strumming keys
        unrounded_chord = [ self.root, self.root + 4 - self.minor + self.sus4 - self.sus2*2, self.root + 7 + self.aug - self.dim]
        if self.seventh:
            unrounded_chord.append(self.root+10-self.minor)
        self.strum_chord = [unrounded_chord[0]-24]
        incr = -12
        while len(self.strum_chord)<len(board.keyboard_strum_keys):
            for n in unrounded_chord:
                self.strum_chord.append(n+incr)
            incr +=12
                            
        #Prepare for display of chord name
        self.chord_shape_name =   ("m" if self.minor else "") + ("7" if self.seventh else "") + ("dim" if self.dim else "aug" if self.aug else "") + ("sus4" if self.sus4 else "sus2" if self.sus2 else "")
        self.chord_sharp_old = None #Force re-display next time
        #self.chord_disp_timestamp = 0 #Don't update -> display will be immediate on the next call to loop()

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
        #self.l.append(self.midi.all_off(self.l.chord_channel))
        strum = [self.strum_chord[i] for i in bits(self.k.strum_keys, len(board.keyboard_strum_keys))]
        for n in self.chord:
            if n not in strum:
                self.l.append(self.midi.note_off(self.l.chord_channel, n, self.default_velocity))                
        self.pending = []
        self.d.clear()
        self.playing_chord_key = None
        self.expr1_none=-10
        self.chord_sharp_old = None

    def start_note(self, i):
        transpose = 12*self.k.fifth + 12*self.k.seventh - 12*self.k.third - 12*self.k.minor + 1*self.k.sharp
        self.melody_keys_transpose[i] = transpose
        self.playing_notes += 1
        self.l.append(self.midi.note_on(self.l.melody_channel, scale[i] + self.transpose + transpose, self.default_velocity))
    
    def stop_note(self, i):
        self.playing_notes -= 1
        self.l.append(self.midi.note_off(self.l.melody_channel, scale[i] + self.transpose + self.melody_keys_transpose[i], self.default_velocity))

    def stop_all_notes(self):
        self.playing_notes = 0
        self.l.append(self.midi.all_off(self.l.melody_channel))
        
    def play_drum(self, note):
        name, note = instr_names.drums[note]
        self.l.append(self.midi.note_on(self.l.drum_channel, note, self.default_velocity))
        return name

    def set_instr(self, instr):
        self.instr = instr
        self.midi.set_instr(self.l.chord_channel,  instr)
        self.midi.set_instr(self.l.melody_channel, instr)
        
    def set_volume(self, vol):
        #TODO: time filtering?
        self.midi.set_controller(self.l.chord_channel, 7, vol)
        self.midi.set_controller(self.l.melody_channel, 7, vol)

    def set_master_volume(self, vol):
        #TODO: time filtering?
        self.midi.set_master_volume(vol)
        
    def loop(self):
        self.metronome.loop()
        
        #Are we strumming?
        if self.strum_chord:
            #If the user just activated the strum mute or released a chord key:
            if (self.k.strum_mute and not self.strum_mute_old):
                #Mute any key that's not being held
                for k in bits(self.strum_keys_all & ~self.k.strum_keys, len(board.keyboard_strum_keys)):
                    self.l.append(self.midi.note_off(self.l.chord_channel, self.strum_chord[k], self.default_velocity))
                self.strum_keys_all = 0
            #update newly released strum keys
            elif self.k.strum_mute:
                #Keys that were in _old but are no longer in _new
                for i in bits(self.strum_keys_old & (~self.k.strum_keys), len(board.keyboard_strum_keys)):
                    self.l.append(self.midi.note_off(self.l.chord_channel, self.strum_chord[i], self.default_velocity))

            #update newly strummed keys
            for i in bits(self.k.strum_keys & (~self.strum_keys_old), len(board.keyboard_strum_keys)):
                self.l.append(self.midi.note_on(self.l.chord_channel, self.strum_chord[i], self.default_velocity))
                
            self.strum_mute_old = self.k.strum_mute
            self.strum_keys_old = self.k.strum_keys
            self.strum_keys_all |= self.k.strum_keys
        
        #scheduled chord notes:
        #Check if a note is due for playing, and play it. Assumes the notes are listed chronologycally.
        if len(self.pending):
            next = self.pending[0][2]
            if next <= time.ticks_ms():
                n = self.pending.pop(0)
                self.l.append(self.midi.note_on(self.l.chord_channel, n[0], n[1]))


        #Playing a chord
        if self.playing_chord_key != None:
            #Update sharp/flat status
            if self.playing_chord_level != self.k.current_key_level:
                self.stop_chord()
                self.start_chord()
            #Update chord shape
            if self.third != self.k.third:
                self.l.append(self.midi.note_off(self.l.chord_channel, self.chord[1], self.default_velocity))
                self.sus4 = self.k.third and not self.k.minor
                self.sus2 = self.k.third and self.k.minor
                self.third = self.k.third
                self.update_chord()
                self.l.append(self.midi.note_on(self.l.chord_channel, self.chord[1], self.default_velocity))
            if self.fifth != self.k.fifth:
                self.l.append(self.midi.note_off(self.l.chord_channel, self.chord[2], self.default_velocity))
                self.aug = self.k.fifth and not self.k.minor
                self.dim = self.k.fifth and self.k.minor
                self.fifth = self.k.fifth
                self.update_chord()
                self.l.append(self.midi.note_on(self.l.chord_channel, self.chord[2], self.default_velocity))
            if self.seventh and not self.k.seventh:
                self.l.append(self.midi.note_off(self.l.chord_channel, self.chord[3], self.default_velocity))
                self.seventh = self.k.seventh
                self.update_chord()
            elif not self.seventh and self.k.seventh:
                self.seventh = self.k.seventh
                self.update_chord()
                self.l.append(self.midi.note_on(self.l.chord_channel, self.chord[3], self.default_velocity))
            
            #Update expression
            #Channel expression (volume): vary pressure on the key being played
            expr1 = self.k.notes_val[self.playing_chord_key]
            if abs(expr1 - self.expr1_old) > 10:# and (time.ticks_ms() - self.expr1_time > 10):#Filtering
                self.expr1_old = expr1
                #self.expr1_time = time.ticks_ms()
                self.l.append(self.midi.set_controller(self.l.chord_channel, 11, expr1//2+64))

             #full-tone bending (press the 1st key of the previous/next line).
            expr_bend = (self.k.key_expr_up - self.k.key_expr_down)//2+64
            if abs(expr_bend - self.expr_bend_old) > 4:# and (time.ticks_ms() - self.expr_bend_time > 10):#Filtering
                self.expr_bend_old = expr_bend
                #self.expr_bend_time = time.ticks_ms()
                self.l.append(self.midi.pitch_bend(self.l.chord_channel, expr_bend))

            #Update the display if needed (depends on the bending status)
            self.chord_sharp = (expr_bend - 48)//32
            if self.chord_sharp != self.chord_sharp_old and (time.ticks_ms() - self.chord_disp_timestamp) > 200:
                self.chord_sharp_old = self.chord_sharp
                self.chord__disp_timestamp = time.ticks_ms()
                #Don't count the "capo" in the chord display.
                #Makes it harder to play with other musicians, but easier to follow tablatures
                self.d.disp_chord(instr_names.note_names[(self.chord[0] + self.chord_sharp - self.transpose)%12], self.chord_shape_name) 
                                    
#end
