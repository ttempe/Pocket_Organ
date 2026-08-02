"""Loop-section timers: avg and peak (active only when board.verbose)."""
import board_po as board
import gc
from time import monotonic_ns

# name -> [sum_us, count, peak_us]
total = {}
counts = {}
peaks = {}
last_timestamp = 0
last_disp = 0

def stamp(name = None):
    if board.verbose:
        global last_timestamp, last_disp
        if name is not None:
            t1 = monotonic_ns()//1000
            duration = t1 - last_timestamp
            total[name] = total.get(name, 0) + duration
            counts[name] = counts.get(name, 0) + 1
            peaks[name] = max(peaks.get(name, 0), duration)
            last_timestamp = t1
        else:
            last_timestamp = monotonic_ns()//1000
            if last_timestamp - last_disp > 1_000_000:
                dump()
                last_disp = last_timestamp

def dump():
    global total, counts, peaks

    for name in total.keys():
        #avg(ms) (peak(ms))
        print(f"{name}:{total[name]/counts[name]/1000:.1f}({peaks[name]/1000:.1f})", end="\t")
    print(f" mem:{gc.mem_free()//1024}k")
    total = {}
    counts = {}
    peaks = {}
