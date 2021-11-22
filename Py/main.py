#Start Pocket_Organ if the "Volume" key is pressed down
from board import main_startup_pin, keyboard_melody_led
from time import sleep

def start():
    print("Starting Pocket Organ")
    keyboard_melody_led(1)#Flash Shift led (it will be turned off during initialization)
    import pocket_organ


#Start if USB is disconnected
#Otherwise, start if Vol is pressed
import pyb
p=pyb.USB_VCP()
if p.isconnected():
    if not(main_startup_pin()):
        start()
else:
    start()
print("Not starting Pocket Organ")

#End
