
def load_image(name):
    "takes a filename, returns a framebuffer"
    return "", 10, 10

class Display:
    def __init__(self):
        pass

    def disp_image(self, img):
        pass

    def disp_indicator(self, img, pos):
        pass

    def disp_chord(self, text):
        pass

    def text(self, text, line=0, duration=None):
        print(text)

    def disp_volume(self, volume, text = "Volume"):
        pass

    def clear(self):
        pass

    def register_indicator(self, i, width):
        pass

    def loop(self, freeze_display=None):
        pass

#end
