import TTY6955
from machine import Pin, I2C
import time


class Keyboard:
    """
    This is the abstraction layer responsible for collecting all user input,
    including key mapping.
    """
    def __init__(self):
        self.i2c = I2C(scl="B6", sda="B7", freq=100000)
        
        self.c1 = TTY6955.TTY6955(self.i2c, addr=0x50, slider1_pads = 3, slider2_pads=3, slider3_pads=3,
                                  key_acknowledge_times=4, dynamic_threshold=False)
        self.c2 = TTY6955.TTY6955(self.i2c, addr=0x51, slider1_pads = 3, slider2_pads=3, slider3_pads=3,
                     nb_keys = 1, key_acknowledge_times=4, dynamic_threshold=False)
        self.c3 = TTY6955.TTY6955(self.i2c, addr=0x52, slider1_pads = 3, slider2_pads=3, slider3_pads=3,
                     nb_keys= 0, key_acknowledge_times=4, dynamic_threshold=False)
        self.c4 = TTY6955.TTY6955(self.i2c, addr=0x53, slider1_pads = 3, slider2_pads=3, slider3_pads=3,
                     nb_keys = 1, key_acknowledge_times=4, dynamic_threshold=False)
        time.sleep(1) #give time to complete auto-calibration
        self.volume_pin = Pin("B0", Pin.IN, Pin.PULL_UP)
        self.instr_pin = Pin("C4", Pin.IN, Pin.PULL_UP)
        self.loop_pin = Pin("A7", Pin.IN, Pin.PULL_UP)
        self.drum_pin = Pin("A6", Pin.IN, Pin.PULL_UP)
        self.note_sliders = bytearray(8)
        self.notes = bytearray(8)
        self.note_sliders_old = bytearray(8)
        self.notes_old = bytearray(8)
        time.sleep_ms(100)
        self.read()
            
    def note_key(self):
        """is one note key being pressed? Returns:
        * whether a key was pressed
        * its index
        """
        for i, n in enumerate(self.notes):
            if n:
                return True, i
        return False, False
    
    def read(self):
        self.notes_old = self.notes[:]
        self.note_sliders_old = self.note_sliders[:]
        self.c1.read()
        self.c2.read()
        self.c3.read()
        self.c4.read()
        #self.volume = self.volume_pin.value()
        #self.instr = self.instr_pin.value()
        #self.loop = self.loop_pin.value()
        #self.drum = self.drum_pin.value()
        self.minor = self.c1.button(3)
        self.seventh = self.c1.button(4)
        self.fifth = self.c1.button(5)
        self.third = self.c1.button(6)
        self.shift = self.c4.button(0)
        self.sharp = self.c2.button(0)
        self.notes[0], self.note_sliders[0] = self.c3.slider(1) #Do
        self.notes[1], self.note_sliders[1] = self.c3.slider(2) #Re
        self.notes[2], self.note_sliders[2] = self.c3.slider(3) #Mi
        self.notes[3], self.note_sliders[3] = self.c1.slider(1) #Fa
        self.notes[4], self.note_sliders[4] = self.c1.slider(2) #Sol
        self.notes[5], self.note_sliders[5] = self.c1.slider(3) #La
        self.notes[6], self.note_sliders[6] = self.c2.slider(1) #Si
        self.notes[7], self.note_sliders[7] = self.c2.slider(1) #Ut
        self.slider_vol_pressed, self.sl_vol_val = self.c4.slider(3)
        self.slider2_pressed, self.slider2_val = self.c4.slider(1)
        self.slider3_pressed, self.slider3_val = self.c2.slider(3)
        
 