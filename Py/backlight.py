import time
from machine import Pin

class Backlight:
    def __init__(self):
        self.oe_pin   = Pin("B3",  Pin.OUT)
        self.data_pin = Pin("B9",  Pin.OUT)
        self.clk_pin  = Pin("C9", Pin.OUT)
        self.intensity = 128
        #self.LED = [5, 7, 6, 4, 3, 2, 1, 0]
        self.LED = [0, 1, 2, 3, 4, 6, 7, 5]
        
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
        for i in range(0, 8):
            self.push_bit( (g >> self.LED[i])& 1)
            self.push_bit( (r >> self.LED[i])& 1)

b = Backlight()

b.on()
b.push(0, 255)