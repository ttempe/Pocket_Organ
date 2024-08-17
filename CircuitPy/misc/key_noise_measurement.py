import time
import random

def reading(addr):
    return random.randint(-1000,1000)+10000 if addr in [1, 2, 4] else 0

def histogram(sensors, divisor, median, spread, duration=2):
    t0 = time.time()
    hist = [[0]*spread for i in range(len(sensors))]
    while time.time()-t0<duration:
        for sensor in sensors:
            val = min(max(reading(sensor)//divisor-median+spread//2,0), spread-1)
            hist[sensor][val]+=1
    
    for sensor in sensors:
        print(sensor, ",", ",".join([str(i) for i in hist[sensor]]))
        
histogram([0,1,2], 100, 100, 10)
