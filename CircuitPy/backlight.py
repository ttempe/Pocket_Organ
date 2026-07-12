#Copyright Thomas TEMPE, 2020

from supervisor import ticks_ms
from board_po import backlight, backlight_map

N_PIXELS = len(backlight_map)
_BLUE = (0, 0, 255)
_OFF = (0, 0, 0)

HINT_DELAY_MS = 2000
LH_PERIOD_MS = 3000
LH_PEAK_HALF_MS = 400
NOTE_CYCLE_MS = 5000
NOTE_GROUP_PEAK_MS = 1250
NOTE_ENVELOPE_HALF_MS = 450

# Keyboard key index -> sweep group (C D E F G A B CC)
# Groups: 0=C,F,CC  1=D,G  2=E,A  3=B
KEY_TO_GROUP = (0, 1, 2, 0, 1, 2, 3, 0)


def _pixel_for_key(key):
    """
    NeoPixel index for keyboard key.
    Note keys 0-7: backlight_map[key]. LH keys 8-13: slot where map[slot]==key.
    """
    if key < 8:
        return backlight_map[key]
    for slot in range(8, N_PIXELS):
        if backlight_map[slot] == key:
            return slot
    return 0


def _cyclic_dist(t, center, period):
    d = t - center
    if d < 0:
        d += period
    if d > period // 2:
        d = period - d
    return d


def _tri_bump(t, center, half_width, period):
    d = _cyclic_dist(t, center, period)
    if d >= half_width:
        return 0
    return (half_width - d) * 255 // half_width


def _lh_pulse(t):
    peak = LH_PERIOD_MS // 2
    return _tri_bump(t % LH_PERIOD_MS, peak, LH_PEAK_HALF_MS, LH_PERIOD_MS)


def _note_sweep(t, key):
    peak = KEY_TO_GROUP[key] * NOTE_GROUP_PEAK_MS
    return _tri_bump(t % NOTE_CYCLE_MS, peak, NOTE_ENVELOPE_HALF_MS, NOTE_CYCLE_MS)


class Backlight:
    def __init__(self):
        self._hints_active = False
        self._note_hint = 0
        self._lh_hint = 0
        self._looper_red = 0
        self._looper_green = 0
        self._hints_start_ms = 0

    def set_hints(self, note_mask, lh_mask, looper_red=0, looper_green=0):
        self._hints_active = True
        self._note_hint = note_mask
        self._lh_hint = lh_mask
        self._looper_red = looper_red
        self._looper_green = looper_green
        self._hints_start_ms = ticks_ms()

    def clear_hints(self):
        self._hints_active = False
        for i in range(N_PIXELS):
            backlight[i] = _OFF
        backlight.show()

    def _render_hints(self, t_ms=0):
        t_anim = t_ms - self._hints_start_ms
        animating = t_anim >= HINT_DELAY_MS
        if animating:
            t_anim -= HINT_DELAY_MS
            lh_br = _lh_pulse(t_anim)

        for i in range(N_PIXELS):
            backlight[i] = _OFF

        for k in range(8):
            px = backlight_map[k]
            r = (self._looper_red >> k) & 1
            g = (self._looper_green >> k) & 1
            if r or g:
                backlight[px] = (r * 255, g * 255, 0)
            elif animating and (self._note_hint >> k) & 1:
                backlight[px] = (0, 0, _note_sweep(t_anim, k))

        if animating:
            for slot in range(8, N_PIXELS):
                key = backlight_map[slot]
                if (self._lh_hint >> key) & 1:
                    backlight[slot] = (0, 0, lh_br)

    def loop(self, t_ms=0):
        if not self._hints_active:
            return
        self._render_hints(t_ms)
        backlight.show()

    def display(self, red, green):
        """
        Set note-key backlights (keys 0~7).
        red and green are 8-bit bitmaps indexed by note key; both set yields orange.
        """
        self._hints_active = False
        for i in range(N_PIXELS):
            backlight[i] = _OFF
        for k in range(8):
            r = (red >> k) & 1
            g = (green >> k) & 1
            if r or g:
                backlight[backlight_map[k]] = (r * 255, g * 255, 0)
        backlight.show()

    def light_keys(self, keys):
        "Blue on note keys 0~7 where bit is set; others off."
        self._hints_active = False
        for i in range(N_PIXELS):
            backlight[i] = _OFF
        for k in range(8):
            if (keys >> k) & 1:
                backlight[backlight_map[k]] = _BLUE
        backlight.show()

    def light_one(self, k):
        self.light_keys(1 << k)

    def light_none(self):
        self.clear_hints()

#End
