from board_po import midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.control_change import ControlChange
from adafruit_midi.midi_message import MIDIUnknownEvent
from adafruit_midi.pitch_bend import PitchBend

import time

#TODO: remove allocation of new buffer for each note played

class Midi:
    def __init__(self):
        #SAM2695 reset. Disables reverb, chorus, microphone, echo, spatial effects, equalizer. Polyphony is increased to 64 simultaneous notes
        #self.uart.write(bytearray([0xB0, 0x63, 0x37, 0xB0, 0x62, 0x5F, 0xB0, 0x06, 0x00]))
        pass

    def inject(self, midi_code):
        "For use by the looper"
        for m in midi:
            m.send(midi_code)

    def note_on(self, channel, note, vel=64):
        n = bytearray([0x90| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        for m in midi:
            m._send(n, 3)
        return n

        
    def note_off(self, channel, note, vel=64):
        n = bytearray([0x80| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        for m in midi:
            m._send(n, 3)
        return n

    def all_off(self, channel):
        n = bytearray([0xB0| (channel & 0x0F), 123, 0])
        for m in midi:
            m._send(n, 3)    
        return n

    def set_instr(self, channel, instr):
        n = bytearray([0xC0| (channel & 0x0F), 0, instr & 0x7F])
        for m in midi:
            m._send(n, 3)
        return n
    
    def set_controller(self, channel, controller, value):
        n = bytearray([0xB0| (channel & 0x0F), controller & 0x7F, value & 0x7F])
        for m in midi:
            m._send(n, 3)
        return n
            
    def set_master_volume(self, volume):
        n = bytearray([0xF0, 0x7F, 0x7F, 0x04, 0x01, 0x00, volume&127, 0xF7])
        for m in midi:
            m._send(n, 8)
        return n
    
#     def channel_aftertouch(self, channel, value):
#         #No effect on the SAM2695
#         n = bytearray([0xD0+(channel&0x0F), value&127])
#         self.uart.write(n)
#         return n
# 
#    def polyphonic_aftertouch(self, channel, note, value):
#         #No effect on the SAM2695
#         n = bytearray([0xA0+(channel&0x0F), note&127, value&127])
#         self.uart.write(n)
#         return n

    def pitch_bend(self, channel, value):
        "value is an integer from -127 to -127"
        n = bytearray([0xE0+(channel&0x0F), 0, 64+value//2])
        for m in midi:
            m._send(n, 3)
        return n
    
    def test2(self):
        while True:
            #self.set_instr(i,0)
            #self.set_master_volume(vol)
            self.note_on(0, 60)
            time.sleep(.200)
            self.note_on(0, 64)
            time.sleep(.200)
            self.note_on(0, 67)
            time.sleep(1.600)
            #self.all_off(0)
            self.note_off(0,60)
            self.note_off(0,64)
            self.note_off(0,67)
            time.sleep(1)
            
    def test3(self):
        while True:
            #self.set_instr(i,0)
            #self.set_master_volume(vol)
            self.note_on(0, 60)
            time.sleep(.200)
            self.note_on(0, 64)
            time.sleep(.200)
            self.note_on(0, 67)
            time.sleep(1.600)
            self.all_off(0)
#             self.old_note_off(0,60)
#             self.old_note_off(0,64)
#             self.old_note_off(0,67)
            time.sleep(1)

    def test0(self):
        "for checking on the oscilloscope"
        while True:
            self.note_on(0,60)
            self.note_off(0,60)
#End