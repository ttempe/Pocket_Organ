from machine import ADC, Pin

count=1000
adc = ADC(Pin(26))

d = []
sumval=0
sumdiff=0
for i in range(count):
    d.append(adc.read_u16())
for i, v in enumerate(d):
    sumval += v
avg = sumval/count
for i, v in enumerate(d):
    sumdiff += abs(v-avg)
stdev = sumdiff/count

print(avg, stdev)
                