#keyboard_RP2040.py
#This module contains the RP2040 capacitor keys sensor driver, which reads capacitve keys using a resistor+capa+diode setup
#One GPIO per key, plus one GPIO for the clock
#The clock pulses charge each capacitive keypads through a ~100k resistor. The overflow goes into a ~10nF reservoir capacitor.
#Once the reservoir's voltage is high enough, the corresponding pin's read level switches to high.
#When the key is pressed (keypad has higher capacitance), it takes more pulses to fill the reservoir.
#
#This driver consumes both PIO state machines and the second RP2040's second core, can't be instantiated twice on the same microcontroller


from machine import mem32, Pin
from micropython import const
import time, array
import rp2
import _thread

#2023-01-27 profiling:
# polling every 4 pulses: 39.3ms

_ADDR_IN  = const(0xd0000004)#GPIO input register for the RP2040
_WAIT = const(3)
        
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _pulsePIO():
    set(pins, 1)[_WAIT]
    set(pins, 0)[_WAIT]

class Keyboard_RP2040:
    def __init__(self, CAPA_CLK_pin, keys):
        #Give a pin number and a list of pin numbers
        self._CAPA_CLK = Pin(CAPA_CLK_pin, Pin.OUT, value=0)			#machine.Pin
        self.keys = [Pin(key) for key in keys]		#list of pins
        self.keys_mask = sum([1<<i for i in keys])	#integer
        self.values = array.array("i", (0 for i in keys))
        self.keys[0].irq(lambda p:self.h(0), trigger=Pin.IRQ_RISING)
        self.keys[1].irq(lambda p:self.h(1), trigger=Pin.IRQ_RISING)
        self.keys[2].irq(lambda p:self.h(2), trigger=Pin.IRQ_RISING)
        self.keys[3].irq(lambda p:self.h(3), trigger=Pin.IRQ_RISING)
        self.keys[4].irq(lambda p:self.h(4), trigger=Pin.IRQ_RISING)
        self.keys[5].irq(lambda p:self.h(5), trigger=Pin.IRQ_RISING)
        self.keys[6].irq(lambda p:self.h(6), trigger=Pin.IRQ_RISING)
        self.keys[7].irq(lambda p:self.h(7), trigger=Pin.IRQ_RISING)
        self.keys[8].irq(lambda p:self.h(8), trigger=Pin.IRQ_RISING)
        self.keys[9].irq(lambda p:self.h(9), trigger=Pin.IRQ_RISING)
        self.keys[10].irq(lambda p:self.h(10), trigger=Pin.IRQ_RISING)
#         for i, k in enumerate(self.keys):
#             self.keys[0].irq(handler = lambda p :print(p), trigger=Pin.IRQ_RISING)
        self.t0 = 0
        self.__count = 0
        #self.semaphore = _thread.allocate_lock()

    def h(self, pin):
        print(pin)
        self.values[pin]=time.ticks_us()-self.t0
        self.__count += 1

    def _flush(self):
        "Flushes the reservoir capacitors before starting a reading cycle"
        for i, key in enumerate(self.keys):
            key.init(Pin.OUT, value=0)	#current sink
            self.values[i]=0
        for key in self.keys:
            key.init(Pin.IN) 			#high-impedence

    def loop(self):
        total=0;total_time = 0; count=0 #for speed benchmarking
        #Having these as local variable saves ~15% execution time
        values = array.array("i", (0 for i in self.keys))
        pulse = rp2.StateMachine(0, _pulsePIO, freq=4000000, set_base=self._CAPA_CLK)
        pulse.active(0)
        
        while True:
            #Prepare:
            t0 = time.ticks_us()
            self._flush()
            self.__count = 0
            self.t0 = time.ticks_us()
            for i, j in enumerate(self.values):
                self.values[i]=0 

            #Measure
            pulse.active(1)
            while self.__count < 10 and time.ticks_us()-t0 < 2000000:
                time.sleep_ms(100)
            
            #clean-up
            pulse.active(0)
            total_time += (time.ticks_us()-t0)//1000
            count += 1
            print(self.values, total_time/count)
            time.sleep_ms(400)            

#k = Keyboard_RP2040(5, [0, 1, 2, 3, 9, 10, 11, 12, 13, 14, 16, 20, 21])
k = Keyboard_RP2040(5, [0, 1, 2, 3, 9, 10, 12, 14, 16, 20, 21])
k.loop()
