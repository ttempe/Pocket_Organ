
from machine import Pin

class backlight:
  "drives the backlight of note keys."
  
  def __init__(self, data, oe, clk):
    self.data=Pin(data, Pin.OUT)
    self.oe=Pin(oe, Pin.OUT)
    self.clk=Pin(clk, Pin.OUT)
    self.off()

    #Si, Ut, La, Sol, Fa, Do, Mi, Re
    self.map= [6, 7, 5, 4, 3, 0, 2, 1]
  
  def send(self, v):
    self.data.value(v)
    self.clk.value(1)
    self.clk.value(0)
    
  def off(self):
    self.oe.value(1)
  
  def on(self):
    self.oe.value(0)
    
  def sendMap(self, green, red):
    "Takes as argument two lists of 8 binary values"
    self.off()
    for i in self.map:
      self.send(not(green[i]))
      self.send(not(red[i]))
    self.send(1)
    self.on()

  def test_colors(self):
    c0=[0,0,0,0,0,0,0,0]
    c1=[1,1,1,1,1,1,1,1]
    import time
    while(1):
      self.sendMap(c0, c1)
      time.sleep(1)
      self.sendMap(c1, c0)
      time.sleep(1)
      
def test():
  b = backlight(data="X21", oe="X20", clk="X19")
  b.test_colors()

