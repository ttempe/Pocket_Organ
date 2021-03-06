import board
import time

#controllers
bank_select_MSB = const(0x00)
bank_select_LSB = const(0x20)

class Midi:
    def __init__(self):
        #TODO: Move to Board
        self.uart = board.midi_UART
        #board.midi_rst(0)
        #time.sleep_ms(200)
        board.midi_rst(1)
        time.sleep_ms(200)
        #SAM2695 reset. Disables reverb, chorus, microphone, echo, spatial effects, equalizer. Polyphony is increased to 64 simultaneous notes
        #self.uart.write(bytearray([0xB0, 0x63, 0x37, 0xB0, 0x62, 0x5F, 0xB0, 0x06, 0x00]))


    def inject(self, midi_code):
        "For use by the looper"
        self.uart.write(midi_code)

    def note_on(self, channel, note, vel=64):
        n = bytearray([0x90| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        self.uart.write(n)
        return n

        
    def note_off(self, channel, note, vel=64):
        n = bytearray([0x80| (channel & 0x0F),
                       note & 0x7F,
                       vel & 0x7F])
        self.uart.write(n)
        return n
 
    def all_off(self, channel):
        n = bytearray([0xB0| (channel & 0x0F),
                       123,
                       0])
        self.uart.write(n)
        return n

    def set_instr(self, channel, instr):
        n = bytearray([0xC0| (channel & 0x0F),
                       0,
                       instr & 0x7F])
        self.uart.write(n)
        return n
    
    def set_controller(self, channel, controller, value):
        n = bytearray([0xB0| (channel & 0x0F),
                       controller & 0x7F,
                       value & 0x7F])
        self.uart.write(n)
        return n
    
    def set_master_volume(self, volume):
        n = bytearray([0xF0, 0x7F, 0x7F, 0x04, 0x01, 0x00, volume&127, 0xF7])
        self.uart.write(n)
        return n
    
#     def channel_aftertouch(self, channel, value):
#         #No effect on the SAM2695
#         n = bytearray([0xD0+(channel&0x0F), value&127])
#         self.uart.write(n)
#         return n
# 
#     def polyphonic_aftertouch(self, note, channel, value):
#         #No effect on the SAM2695
#         n = bytearray([0xA0+(channel&0x0F), note&127, value&127])
#         self.uart.write(n)
#         return n

    def pitch_bend(self, channel, value):
        n = bytearray([0xE0+(channel&0x0F), 0, value&127])
        self.uart.write(n)
        return n

    def test2(self):
        while 1 :
            self.note_on(0, 60)
            time.sleep_ms(200)
            self.note_on(0, 64)
            time.sleep_ms(200)
            self.note_on(0, 67)
            time.sleep_ms(1600)
            self.note_off(0,60)
            self.note_off(0,64)
            self.note_off(0,67)
            time.sleep(1)
            
    def test1(self):
        while 1:
            self.uart.write(b"\x90\x40\x60")
            time.sleep(1)
            self.uart.write(b"\x80\x40\x60")

#End
