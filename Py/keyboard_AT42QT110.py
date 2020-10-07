import AT42QT110
from machine import Pin, SPI
import time

#TODO:
#force a recalibration when switching between USB and battery power
#clean up slider code

class Keyboard:
    """
    This is the abstraction layer responsible for collecting all user input,
    including key mapping.
    """
    def __init__(self):
        self.melody_led = Pin("A0", Pin.OUT)
        self.melody_led(1)

        self.spi = SPI(1)
        self.uc1 = AT42QT110.AT42QT110(self.spi, Pin("B8", Pin.OUT))
        self.uc2 = AT42QT110.AT42QT110(self.spi, Pin("C5", Pin.OUT))
        self.uc3 = AT42QT110.AT42QT110(self.spi, Pin("C3", Pin.OUT))

        time.usleep(160) #give time to complete auto-calibration
        self.volume_pin = Pin("B0", Pin.IN, Pin.PULL_UP)
        self.instr_pin = Pin("C4", Pin.IN, Pin.PULL_UP)
        self.looper_pin = Pin("A4", Pin.IN, Pin.PULL_UP)
        self.drum_pin = Pin("A3", Pin.IN, Pin.PULL_UP)

        self.note_sliders = bytearray(8)
        self.notes = bytearray(8)
        self.note_sliders_old = bytearray(8)
        self.notes_old = bytearray(8)
        
        #time.sleep_ms(160)
        self.loop()
        self.melody_led(0)

                
    def loop(self):
        self.notes_old = self.notes[:]
        self.note_sliders_old = self.note_sliders[:]
#         t=c=0
#         while 0==t:
#             try:
#                 c+=1
#                 self.c1.read()
#                 self.c2.read()
#                 self.c3.read()
#                 self.c4.read()
#                 t=1
#             except:
#                 pass
#         if c>2:
#             print("Touch sensors: {} trials".format(c))
        self.uc1.read()
        self.uc2.read()
        self.uc3.read()        
        
        self.volume = not(self.volume_pin.value())
        self.instr = not(self.instr_pin.value())
        self.looper = not(self.looper_pin.value())
        self.drum = not(self.drum_pin.value())
        
        self.seventh = self.uc2.button(6)
        self.fifth = self.uc2.button(7)
        self.third = self.uc2.button(8)
        self.minor = self.uc2.button(0)
        self.shift = self.uc2.button(1)
        self.sharp = self.uc1.button(2)

        self.notes[0] = self.uc1.button(7) #Do
        self.notes[1] = self.uc1.button(6) #Re
        self.notes[2] = self.uc1.button(8) #Mi
        self.notes[3] = self.uc1.button(1) #Fa
        self.notes[4] = self.uc1.button(0) #Sol
        self.notes[5] = self.uc1.button(9) #La
        self.notes[6] = self.uc1.button(3) #Si
        self.notes[7] = self.uc1.button(4) | self.uc1.button(5) #Ut

        #self.slider_vol_pressed, self.slider_vol_val = self.c4.slider(2)
        #self.slider2_pressed, self.slider2_val = self.c4.slider(1)
        #self.slider3_pressed, self.slider3_val = self.c2.slider(3)

        #is there a key being pressed right now?
        self.current_note_key = None
        for i, n in enumerate(self.notes):
            if n:
                self.current_note_key = i
                break

        #TODO: implement melody lock
        self.melody_led(self.shift)
            
#end
            