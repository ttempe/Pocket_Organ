import board_po as board
import mux
from supervisor import ticks_ms

# TODO:
# - Calibrate for effect of load on displayed level

# Resting OCV lookup for single-cell Li-ion: (voltage V, true SOC %), ascending voltage
_OCV = [(3.00, 0), (3.50, 10), (3.65, 20), (3.75, 40), (3.82, 60), (3.95, 80), (4.20, 100), (10000, 101)]
_RESERVE_SOC = 10  # display 0% when 10% true capacity remains
_BAT_FILL_MAX = 14  # match display._BAT_FILL_MAX
_CHARGE_ANIM_MS = 80
_CHARGE_PERIOD_MS = 2500

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
        self.anim_time = 0
        self.d = disp
        self.vbat = mux.vbat_read()
        if mux.vusb_read() < 4.5:
            self.last_lvl = state_of_charge(self.vbat)
            self.d.disp_bat(self.last_lvl)
        else:
            self.last_lvl = None
            self.d.disp_bat_charging(0)

    def loop(self):
        now = ticks_ms()
        if mux.vusb_read() >= 4.5:
            if now - self.anim_time >= _CHARGE_ANIM_MS:
                fill_w = int(_BAT_FILL_MAX * ((now % _CHARGE_PERIOD_MS) / _CHARGE_PERIOD_MS))
                self.d.disp_bat_charging(fill_w)
                self.anim_time = now
            self.last_lvl = None
        elif now - self.last_time > 500:
            self.vbat = self.vbat * 0.5 + mux.vbat_read() * 0.5
            lvl = state_of_charge(self.vbat)
            if lvl != self.last_lvl:
                if board.verbose:
                    print("battery level changing to", lvl)
                self.d.disp_bat(lvl)
            self.last_lvl = lvl
            self.last_time = now

#End
