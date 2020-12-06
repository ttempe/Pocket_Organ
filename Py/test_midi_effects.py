import keyboard_AT42QT1110 as keyboard
import midi
import time

#Analog keys experimentation

#Conclusion: SAM2695 only supports modulation, expression, depth, chorus, and pitch bend

k = keyboard.Keyboard()
m = midi.Midi()
m.set_instr(0, 22)
m.note_on(0, 64, 32)
while 1:
    a= (178-k.uc1.read_analog(4))*1.3
    b= 247-k.uc1.read_analog(5)
    c= int(min(a/(a+b)*128, 127))
    m.set_controller(0, 81, c)
    #m.aftertouch(0, int(c))
    #m.polyphonic_aftertouch(0, 64, c)
    #m.pitch_bend(0, c)
    print(c)
    time.sleep_ms(100)

#Controllers:
# 1: modulation
# 2: breath ->no effect
# 4: pedal  ->no effect
# 11:expression
# 12,13: effects->no effect
# 70,71,72,74,75->no effect
# 81:         -> no effect
# 91: depth1
# 92: tremolo -> no effect
# 93: chorus
# 94,95       -> no effect
# 
