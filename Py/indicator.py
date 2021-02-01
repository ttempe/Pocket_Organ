#Copyright Thomas TEMPE 2020
import display_stub as display

class Indicator:
    def __init__(self, d, images, state_callback, pos=None):
        """
        Manage one display indicator icon.
        The icon to be displayed at any time is determined by the state_callback funtion.
        pos is the position (in pixels) on the screen. If blank, the next slot will be allocated from the display.
        the indicator registers itself with Display. No need to keep a variable for it.
        """
        self.d = d #Display
        self.callback = state_callback
        self.last_img = None
        self.img = []
        for i in images:
            img, width, height = display.load_image(i)
            self.img.append(img)
        self.x_pos = d.register_indicator(self, 0 if pos else width+2)

    def display(self):
        "force display"
        self.last_img = self.callback()
        self.d.disp_indicator(self.img[self.last_img], self.x_pos)

    def loop(self):
        "refresh display only if the state has changed"
        v = self.callback()
        if v != self.last_img:
            self.d.disp_indicator(self.img[v], self.x_pos)
            self.last_img = v
            
#end