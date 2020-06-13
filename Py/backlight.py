import time
from machine import Pin

class Backlight:
    def __init__(self):
        self.oe_pin   = Pin("B3",  Pin.OUT)
        self.data_pin = Pin("B9",  Pin.OUT)
        self.clk_pin  = Pin("C0", Pin.OUT)
        self.intensity = 128
        self.LED = [1, 2, 0, 3, 4, 5, 6, 7]
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
    
    def push(self, r, g):
        r = ~r
        g = ~g
        for i in range(0, 8):
            self.push_bit( (g >> self.LED[i])& 1)
            self.push_bit( (r >> self.LED[i])& 1)
        self.push_bit(0)
        
    def light_one(self, k):
        self.push(0, 1<<k)
        self.on()

#End
