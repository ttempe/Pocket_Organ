#Copyright Thomas TEMPE, 2020

from board_po import backlight, backlight_map


class Backlight:
    def display(self, red, green):
        """
        Set note-key backlights (keys 0~7).
        red and green are 8-bit bitmaps; both set yields orange (looper paused).
        """
        for k in range(8):
            r = (red >> k) & 1
            g = (green >> k) & 1
            backlight[backlight_map[k]] = (r*255, g*255, 0)
        backlight.show()

    def light_keys(self, keys):
        "Blue on note keys 0~7 where bit is set; others off."
        for k in range(8):
            if (keys >> k) & 1:
                backlight[backlight_map[k]] = (0, 0, 255)
            else:
                backlight[backlight_map[k]] = (0, 0, 0)
        backlight.show()

    def light_one(self, k):
        self.light_keys(1 << k)

    def light_none(self):
        self.display(0, 0)

#End
