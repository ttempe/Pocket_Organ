#Copyright Thomas TEMPE, 2020

import time
import board

class Backlight:
    def __init__(self):
        
        self.oe_pin   = board.backlight_oe_pin
        ##Note: in case we want to switch to PWM (untested; not supported on C14)
        #from pyb import Pin, Timer
        #tim = Timer(8, freq=1000)
        #self.ch = tim.channel(1, Timer.PWM, pin=self.oe_pin)
        #self.ch.pulse_width_percent(50)

        self.data_pin = board.backlight_data_pin
        self.clk_pin  = board.backlight_clk_pin
        #self.intensity = 128
        self.off()
        
    def on(self):
        #self.oe_pin.intensity(self.intensity)
        self.oe_pin(0)
    
    def off(self):
        self.oe_pin(1)
        
    def push_bit(self, v):
        self.data_pin(v)
        self.clk_pin(1)
        self.clk_pin(0)
    
    def display(self, red, green):
        """
        Set the note key backlight LEDS, and turns the display on.
        Takes around 600 us on Version 14B
        """
        red = ~red
        green = ~green
        self.off()
        for i in range(0, 8):
            self.push_bit( (green >> board.backlight_leds[i])& 1)
            self.push_bit( (red   >> board.backlight_leds[i])& 1)
        self.push_bit(0)
        self.on()
        
    def light_one(self, k):
        self.display(0, 1<<k)
        
    def light_none(self):
        self.display(0, 0)

#End
