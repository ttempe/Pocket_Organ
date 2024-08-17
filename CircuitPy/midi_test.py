import usb_midi, busio, board
import adafruit_midi
import time
from adafruit_midi import note_off, note_on

midi_UART = busio.UART(tx=board.GP16, rx=None, baudrate=31250)

from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn

midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)
#midi = adafruit_midi.MIDI(midi_out=midi_UART, out_channel=0)

while True:
    for i in range(48, 72):
        midi.send(NoteOn(i, 64))
        time.sleep(0.2)
        midi.send(NoteOn(i+4, 40))
        time.sleep(0.6)
        midi.send(NoteOff(i, 0)) 
        time.sleep(0.2)
        midi.send(NoteOff(i+4, 0)) 
