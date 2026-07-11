import board_po as board
import gc
import json
from supervisor import ticks_ms

#TODO:
# * when some loops are recorded but none is playing:
#   * refuse to record (to keep them in sync)
#   * restart playing at the beginning
# * Queue delete operations to allow successive deletion of multiple tracks
# * Persist loops to filesystem / .mid export

def bits(n):
    "8-bit bit map iterator"
    for i in range(0, 8):
        if n&(1<<i):
            yield i


class TrackStore:
    "In-memory MIDI event storage (one list per track)."

    def __init__(self, n_tracks=8):
        self.tracks = [[] for _ in range(n_tracks)]
        self._rec = 0

    def busy(self):
        return False

    def loop(self):
        pass

    def start_recording(self, n):
        self._rec = n
        self.tracks[n].clear()

    def finish_recording(self):
        pass

    def record_message(self, t, event):
        self.tracks[self._rec].append((t, bytes(event)))

    def read_message(self, track, index):
        events = self.tracks[track]
        if index >= len(events):
            if events:
                return events[-1][0] + 1000, b""
            return 1000, b""
        return events[index]

    def erase(self, n):
        self.tracks[n].clear()


class Looper:
    def __init__(self, backlight, display):
        self.record_channels = [(2,3), (4,5), (6,7), (8,10), (11,12), (13, 14), (0, 1)]
        self.chord_channel, self.melody_channel = self.record_channels[-1]
        self.drum_channel = 9 #This is imposed by General MIDI
        self.p = None #Polyphony; assigned by PocketOrgan
        self.b = backlight
        self.d = display
        self.store = TrackStore(8)

        self.recorded = 0     #bit map
        self.playing = 0      #bit map
        self.recording = None #track index, or None
        self.recording_start_timestamp = None
        self.record_lengths = [0]*8
        self.cursors = [0]*8
        self.durations = [0]*8
        self.loop_start = [0]*8 #Timestamps
        self.toggle_play_waitlist = 0 #bit map
        self.loop_names = ["C", "D", "E", "F", "G", "A"]
        self.quick_time = None

    def save(self):
        pass #Future: persist to flash or filesystem

    def load(self):
        pass #Future: load from flash or filesystem

    def iter_events(self, track):
        "For future .mid export."
        return self.store.tracks[track]

    def append(self, event):
        #Called by Polyphony for every Midi event
        if None != self.recording:
            if not self.recording_start_timestamp:
                self.recording_start_timestamp = self.p.metronome.now
                self.p.prepend_loop_channel_volume()
            if self.quick_time != None:
                t = self.quick_time
            else:
                t = self.p.metronome.now - self.recording_start_timestamp
            self.store.record_message(t, event)
            self.record_lengths[self.recording]+=1

    def display(self):
        #red    = recording
        #orange = recorded and paused
        #green  = recorded and playing
        playing = self.playing ^ self.toggle_play_waitlist
        recording = (1 << self.recording) if (self.recording!=None) else 0
        green = (self.recorded | playing) & ~recording
        red =  recording | (self.recorded & ~playing)
        self.b.display( red, green)

    def loop_exists(self, n):
        "was that loop recorded already?"
        return self.recorded & (1<<n)

    def delete_track(self, n):
        if self.playing & (1<<n):
            self._stop_playing(n)
        self.recorded &= ~(1<<n)
        self.durations[n] = 0
        self.playing &= ~(1<<n)
        self.toggle_play_waitlist &= ~(1<<n)
        self.display()
        self.store.erase(n)
        self.d.text("Loop {} deleted".format(self.loop_names[n]))
        gc.collect()

    def start_recording(self, n):
        #Returns True on success
        if n >= 6:
            self.d.text("Can't record a loop on this key")
            return False
        self.recording = n
        self.recording_start_timestamp = None
        self.record_lengths[n] = 0
        self.chord_channel, self.melody_channel = self.record_channels[n]
        self.p.set_instr(self.p.instr)
        self.store.start_recording(self.recording)
        self.p.bake_loop_channel_volume()

        self.display()
        self.d.text("Start recording loop {}".format(self.loop_names[n]))
        self.p.metronome.on()
        self.quick_time = None
        return True

    def start_recording_quick(self):
        self.quick_time = 0
        self.recording_start_timestamp = 0

    def quick_increment(self):
        self.quick_time += self.p.metronome.beat_divider

    def stop_recording(self):
        "Returns whether recording was in progress"
        if self.recording != None:
            if self.record_lengths[self.recording]>0:
                now = self.p.metronome.now
                self.d.text("Finished recording loop {}".format(self.loop_names[self.recording]))
                self.recorded |= 1<<self.recording
                self.chord_channel, self.melody_channel = self.record_channels[-1]
                self.store.record_message(self.p.metronome.now + 1000, b"  ")
                self.record_lengths[self.recording] += 1
                if self.quick_time:
                    d = self.quick_time
                else:
                    d = now - self.recording_start_timestamp
                d = self.p.metronome.round_to_beats(d)
                if self.playing:
                    min_duration = min([ self.durations[i] for i in bits(self.playing)])
                    if min_duration%(self.p.metronome.beat_divider*2):
                        min_duration //= 2
                    self.durations[self.recording] = int(round(d/min_duration)*min_duration)
                else:
                    self.durations[self.recording] = int(max( d, self.p.metronome.beat_divider))
                self.loop_start[self.recording] = self.recording_start_timestamp+self.durations[self.recording]
                self._start_playing(self.recording)
                self.cursors[self.recording] = 0
            else:
                self.d.text("Nothing recorded")
            self.recording = None
            self.p.metronome.off()
            self.store.finish_recording()
            gc.collect()
            return True
        else:
            return False

    def toggle_play(self, key):
        if (self.playing ^ self.toggle_play_waitlist) & (1<<key):
            self.d.text("Stop playing loop {}".format(self.loop_names[key]))
        else:
            self.d.text("Start playing loop {}".format(self.loop_names[key]))
        self.toggle_play_waitlist ^= 1<<key
        self.d.text("Hold to delete",2, tip=True)
        self.display()

    def _start_playing(self, i):
        self.playing |= 1<<i

    def _stop_playing(self, i):
        self.playing &= ~(1<<i)
        for c in self.record_channels[i]:
            self.p.midi.all_off(c)

    def leave_looper(self):
        "Metronome is looper-scoped; fifth toggle and idle click stop on exit."
        if self.recording is None:
            self.p.metronome.off()

    def apply_ui(self):
        for i in bits(self.toggle_play_waitlist & (~self.playing)):
            self._start_playing(i)
            self.toggle_play_waitlist &= ~(1<<i)
        for i in bits(self.toggle_play_waitlist & self.playing):
            self._stop_playing(i)
        self.toggle_play_waitlist = 0
        self.b.light_none()
        if self.recording is None and not self.playing:
            self.p.metronome.off()

    def pop_notes(self, loop):
        now = self.p.metronome.now - self.loop_start[loop]
        c = self.cursors[loop]
        if self.durations[loop] == 0:
            raise Exception(f"duration is 0 for loop {loop}")
        elif now > self.durations[loop]:
            c=0
            self.loop_start[loop] += ((self.p.metronome.now-self.loop_start[loop])//self.durations[loop])*self.durations[loop]
            now = self.p.metronome.now - self.loop_start[loop]
            for d in self.record_channels[loop]:
                self.p.midi.all_off(d)
        t, msg = self.store.read_message(loop, c)
        while t <= now:
            if self.playing & (1<<loop):
                if msg:
                    self.p.midi.inject(msg)
            c+=1
            t, msg = self.store.read_message(loop, c)
        self.cursors[loop]=c

    def loop(self):
        for i in range(8):
            if self.recorded & (1<<i):
                self.pop_notes(i)
        self.store.loop()

#End
