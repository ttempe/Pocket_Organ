import keyboard
from time import sleep

k= keyboard.Keyboard()


def sample(count = 1000):
    vmin = [66000]*16
    vmax = [1] * 16
    c = count
    while c>0:
        for i in range(16):
            r = k._read_addr(i)
            vmax[i] = max(r, vmax[i])            
            vmin[i] = min(r, vmin[i])
        c-=1
    
    return vmin, vmax

def record():
    while True:
        a,b=sample(20000)
        for i in a+b:
            print(i, end=", ")
        print()
        #sleep(1)

def test2():
    d = [0]*550
    for i in range(550):
        d[i]=k._read_addr(0)
    print(d)
  
def test3():
    addr=0
    keyb_muxA.value = addr&0x8
    keyb_muxB.value = addr&0x4
    keyb_muxC.value = addr&0x2
    adc = keyb_ADC[addr&0x1]
    for i in range(500):
        v = [adc.value, adc.value, adc.value, adc.value, adc.value, adc.value, adc.value, adc.value, adc.value]
        v.sort()
        print(v)
        #return v[4]
        v=adc.value

