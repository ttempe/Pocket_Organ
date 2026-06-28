"""Flash wrtite speed test.

https://chatgpt.com/share/6816e05e-e72c-8005-a364-95f27606465d

Assumption:
* Flash read and write operations are blocking on CircuitPython on RP2040. There is no preemption.
* Writes add an acceptable amount of delay (<2ms) if no bit changes from 0 to 1
* if a bit changes from 0 1, that triggers a flash block erase that takes at least 30ms typical, and also will be blocking (inacceptable while recording)

1. create a large file (multiple 4k blocks) filled with 0xFF. Close it.
2. Open it again. Now write (in small increments, without crossing 512b boundaries per write operation).
Time each write operation. It should always be <2ms.

"""
import os, time

filename = "track0.dat"

def create(nb_blocks=10):
    t0=time.monotonic_ns()//100000/10
    fd=open(filename, "w")
    for i in range(nb_blocks):
        fd.write(b"\xFF" * 4000)
    fd.close()
    print("Wrote a {}kB file in {} ms".format(nb_blocks*4, time.monotonic_ns()//100000/10-t0))

def record(nb_blocks=10):
    tmin=1000
    tmax=0
    thres = 40
    nb_high = 0
    fd=open(filename, "a")
    fd.seek(0)
    count=0
    for i in range(nb_blocks*1000):
        t0=time.monotonic_ns()//10000/100
        fd.write(b"\x00\x00\x00\x00")
        t =time.monotonic_ns()//10000/100-t0
        if t>6:
            print("{} ms (after {} writes)".format(t, count))
            count=0
        else:
            count+=1
#        print(t)
        tmin=min(t, tmin)
        tmax=max(t,tmax)
        nb_high += t>thres
        time.sleep(0.01)
    t0=time.monotonic_ns()//10000/100
    fd.close()
    print("Wrote {} records in {} ~ {} ms.\n {} of them took more than {}ms to write".format(nb_blocks*1000, tmin, tmax, nb_high, thres))
    print("File close time: {} ms".format(time.monotonic_ns()//10000/100-t0))    
