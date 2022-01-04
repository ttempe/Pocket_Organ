
import time
import display
import board
d=C
import keyboard_AT42QT1110 as kb
k=kb.Keyboard()

minvals=[1000]*8
while(1):
    time.sleep_ms(200)
    d.disp.fill(0)
#    d.disp.text(str(board.vbat()),0,8)         #USB voltage
    for i, v in enumerate(board.keyboard_note_keys): #Level of each key
        v = k.uc1.read_analog(v)
        minvals[i]=min(minvals[i],v)
        d.disp.text(str(v)+"  "+str(v-minvals[i]),0,8*i) 
    d.disp.show()