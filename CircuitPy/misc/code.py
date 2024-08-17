import digitalio, board
import time, supervisor

def pinOut(p, value=None):
    ret = digitalio.DigitalInOut(p)
    ret.direction = digitalio.Direction.OUTPUT
    if value!=None:
        ret.value =value
    return ret

def check_power_button():
    if not(power_button.value):
        t0=supervisor.ticks_ms()
        LED.value=False
        print("Power pressed")
        while supervisor.ticks_ms() - t0 < 200:
            if not(power_button.value):
                print("Power released")
                return
        print("Turning off now")
        power.value=False

LED = pinOut(board.GP25, value=True)
power = pinOut(board.GP10, value=True)
#power_button = digitalio.DigitalInOut(board.GP11)
#digitalio.Pull.UP #Pulled up by the power pin already.
power_button = digitalio.DigitalInOut(board.GP12) #debug

print("Turned on")

while True:
    check_power_button()