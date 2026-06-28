from board_po import verbose, version, vbat_read, vusb_read
from supervisor import ticks_ms

# TODO:
# - Add a display of the battery level as a bar graph
# - Calibrate for effect of load on displayed level

# Resting OCV lookup for single-cell Li-ion: (voltage V, true SOC %), ascending voltage
_OCV = [(3.00, 0), (3.50, 10), (3.65, 20), (3.75, 40), (3.82, 60), (3.95, 80), (4.20, 100), (10000, 101)]
_RESERVE_SOC = 10  # display 0% when 10% true capacity remains

def state_of_charge(v):
    """Use lookup table to convert voltage to state of charge(%). 
    Leave 10% of capacity as reserve. to avoid over-discharging."""
    for i in range(len(_OCV) - 1):
        v0, s0 = _OCV[i]
        v1, s1 = _OCV[i + 1]
        if v0 <= v <= v1:
            true_charge = s0 + (s1 - s0) * (v - v0) / (v1 - v0)
            return max(0, min(100, (true_charge - _RESERVE_SOC) / (100 - _RESERVE_SOC) * 100))
    return 0

class Battery:
    def __init__(self, disp):
        self.last_time = 0
        self.d = disp
        self.disp_update = 0
        self.last_lvl = None
        self.vbat = vbat_read()

    def loop(self):
        if ticks_ms()-self.last_time > 500: #Update every 1/2s
            lvl = state_of_charge(self.vbat) if vusb_read()<4.5 else None

            if lvl != self.last_lvl:
                if verbose:
                    print("battery level changing to", lvl)
                self.d.disp_batt(lvl)
            self.last_lvl = lvl

            if verbose:
                if (self.disp_update & 0x8) == 0:
                    self.d.status.text = "{}V {}".format(vbat_read  (), "-\|/"[self.disp_update%4])
                else:
                    self.d.status.text = "v{} {}".format(version, "-\|/"[self.disp_update%4])
                self.disp_update += 1
            self.last_time = ticks_ms()

#End
