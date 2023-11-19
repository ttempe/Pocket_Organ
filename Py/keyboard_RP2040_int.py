#keyboard_RP2040.py
#This module contains the RP2040 capacitor keys sensor driver, which reads capacitve keys using a resistor+capa+diode setup
#One GPIO per key, plus one GPIO for the clock
#The clock pulses charge each capacitive keypads through a ~100k resistor. The overflow goes into a ~10nF reservoir capacitor.
#Once the reservoir's voltage is high enough, the corresponding pin's read level switches to high.
#When the key is pressed (keypad has higher capacitance), it takes more pulses to fill the reservoir.
#
#This driver consumes both PIO state machines and the second RP2040's second core, can't be instantiated twice on the same microcontroller


#Next actions:
# * add a reference electrode to measure timing more precisely
# * evaluate whether there are still oscillations in the readings
# * find the root cause of diminished readings when pressing 2 fingers at once
# * see if I can read through the PCB cover, with a short reading cycle

from machine import mem32, Pin
from micropython import const
import time, array
import rp2, gc
import _thread

import micropython
micropython.alloc_emergency_exception_buf(100)

#2023-01-27 profiling:
# polling every 4 pulses: 39.3ms

#self.semaphore = _thread.allocate_lock()
#_ADDR_IN  = const(0xd0000004)#GPIO input register for the RP2040
#self.keys_mask = sum([1<<i for i in keys])	#integer
_WAIT = const(7)

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _pulsePIO():
    set(pins, 1)[_WAIT]
    set(pins, 0)[_WAIT]


class Keyboard_RP2040:
    def __init__(self, CAPA_CLK_pin, keys): #Give a pin number and a list of pin numbers
        self.t0 = 0
        self._CAPA_CLK = Pin(CAPA_CLK_pin, Pin.OUT, value=0)			#machine.Pin
        self.keys = [Pin(key, Pin.OPEN_DRAIN) for key in keys]		#list of pins
        self.values = array.array("i", (0 for i in keys))
        for c, v in enumerate(self.keys):
            v.irq( self.handlerFactory(c), trigger=Pin.IRQ_RISING, hard=True)

    def handlerFactory(self, pin):
        def handler(p):
            self.values[pin]=time.ticks_us()-self.t0
        return handler

    def _flush(self):
        "Flushes the reservoir capacitors before starting a reading cycle"
        for key in self.keys:
            key(0) #current sink
        for key in self.keys:
            key(1) #high-impedence

    def loop(self):
        #Having these as local variable saves ~15% execution time
        pulse = rp2.StateMachine(0, _pulsePIO, freq=4000000, set_base=self._CAPA_CLK)
        pulse.active(0)
        
        while True:
            #Prepare:
            self._flush()
            for i, v in enumerate(self.values):
                self.values[i] = 0
            
            #Measure
            self.t0 = time.ticks_us()
            pulse.active(1)
            time.sleep_ms(150)
            
            #clean-up
            pulse.active(0)
            print(self.values)
            gc.collect();   
            time.sleep_ms(30)            

#k = Keyboard_RP2040(5, [0, 1, 2, 3, 9, 10, 11, 12, 13, 14, 16, 20, 21])
k  = Keyboard_RP2040(5, [0, 1, 2, 9, 3, 10, 11, 12, 13, 20, 16, 14, 21])
k.loop()
