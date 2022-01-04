import board
board.keyboard_crosstalk = None
import keyboard_AT42QT1110 as keyb
import time

#TODO: review the thersholds
print("Hello!")
k = keyb.Keyboard()
s = k.vol_slider

##Check note keys
# while 1:
#     k.loop()
#     if max(k.notes_val)>20:
#         for v in k.notes_val:
#             #print(v, ", ", end="")
#             print("{:.2}, ".format(v/max(k.notes_val)), end="")
#         print()
#     time.sleep_ms(200)

##Note keys original values
vmax = [0,0]
vmin = [300,300]
while 1:
    k.loop()
    n=[]
    for note, button in enumerate(board.keyboard_note_keys):
        n.append(k.uc1.read_analog(button))
    time.sleep_ms(50)
    #print(n)
    v =[n[6], n[7]]
    vmax = [max(i,j) for i,j in zip(v, vmax)] 
    vmin = [min(i,j) for i,j in zip(v, vmin)]
    if k.current_note_key != None:
        print(v, vmax, vmin)

##Test slider sensors
#while 1:
#    k.loop()
#    for e in s.electrodes:
#        print(s.uc.read_analog(e), ",", end="")
#    print("")
#    time.sleep_ms(100)