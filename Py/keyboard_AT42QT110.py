import AT42QT110
import time
import board

#TODO:
#force a recalibration when switching between USB and battery power
#clean up slider code

class Keyboard:
    """
    This is the abstraction layer responsible for collecting all user input,
    including key mapping.
    """
    def __init__(self):
        self.melody_led = board.keyboard_melody_led
        self.melody_led(1)

        self.uc1 = AT42QT110.AT42QT110(board.keyboard_spi, board.keyboard_uc1_cs)
        self.uc2 = AT42QT110.AT42QT110(board.keyboard_spi, board.keyboard_uc2_cs)
        self.uc3 = AT42QT110.AT42QT110(board.keyboard_spi, board.keyboard_uc3_cs)

        time.usleep(160) #give time to complete auto-calibration
        self.volume_pin = board.keyboard_volume_pin
        self.instr_pin = board.keyboard_instr_pin
        self.looper_pin = board.keyboard_looper_pin
        self.drum_pin = board.keyboard_drum_pin

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
            