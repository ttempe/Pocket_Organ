#Start Pocket_Organ if the "Volume" key is pressed down
from board import main_startup_pin, keyboard_melody_led
from time import sleep

sleep(1)
if not(main_startup_pin()):
    print("Starting Pocket Organ")
    keyboard_melody_led(1)
    import pocket_organ
else:
    print("Starting in REPL mode.\nHold the Volume key while powering on to start the instrument")

#End
