#Copyright Thomas TEMPE, 2020

from board_po import backlight, backlight_map

green = (0,255,0)
orange = (255,255,0)
red = (255,0,0)
off = (0,0,0)


class Backlight:
#     def __init__(self):
#         pass
        
    def on(self):
        pass
    
    def off(self):
        pass
        
    def push_bit(self, v):
        pass
    
    def display(self, red, green):
        """
        Set the note key backlight LEDS, and turns the display on.
        """
        self.on()
        
    def light_one(self, k):
        self.display(0, 1<<k)
        
    def light_none(self):
        self.display(0, 0)

#End
