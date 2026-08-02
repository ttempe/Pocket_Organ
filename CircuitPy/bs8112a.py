# Holtek BS8112A-3 capacitive touch (12 keys).

import time

_REG_KEYSTATUS0 = 0x08
_REG_SETTINGS = 0xB0
_KEY_MASK = 0x0FFF  # Key1..Key12

# Option2 @ 0xB4: bit7=1, bit6=LSC (0=faster general, 1=more power-saving)
_OPTION2_LSC_OFF = 0x98

# Kn_TH bits5:0: valid 8..63. Higher = less sensitive (better for direct skin contact).
_THRESHOLD = 63
# Key12 C0H bit6 Mode: 0=Key12 touch (needed for 12-pad comb), 1=IRQ

_OPTION2_FAST_RESPONSE = 0x9C


class BS8112AStub:
    "No hardware: never reports pad presses."
    def read_keys(self):
        return 0


class BS8112A:
    def __init__(self, i2c, address=0x50, threshold=_THRESHOLD):
        self._i2c = i2c
        self._addr = address
        self._buf = bytearray(2)
        self._configure(threshold)

    def _try_i2c(self, func):
        deadline = time.monotonic() + 0.01  # try briefly, then fail open
        while time.monotonic() < deadline:
            if self._i2c.try_lock():
                try:
                    func()
                    return True
                finally:
                    self._i2c.unlock()
            time.sleep(0.0001)
        return False

    def _configure(self, threshold):
        """
        Write B0..C0 settings block (must finish within ~6s of power-on).
        17 register bytes + 8-bit checksum of those 17 bytes.
        """
        th = max(8, min(63, int(threshold))) & 0x3F
        data = bytearray([
            0x00,
            0x00, 0x83, 0xF3,
            _OPTION2_FAST_RESPONSE,
        ])
        for _ in range(11):
            data.append(th)
        data.append(th)
        checksum = sum(data) & 0xFF
        payload = bytes([_REG_SETTINGS]) + data + bytes([checksum])
        i2c = self._i2c
        try:
            self._try_i2c(lambda: i2c.writeto(self._addr, payload))
        except OSError:
            pass

    def read_keys(self):
        """Return 12-bit keymap: bit0=Key1 .. bit11=Key12. 0 on I2C failure."""
        i2c = self._i2c
        try:
            if not self._try_i2c(lambda: i2c.writeto_then_readfrom(
                self._addr, bytes([_REG_KEYSTATUS0]), self._buf
            )):
                return 0
        except OSError:
            return 0

        return (self._buf[0] | ((self._buf[1] & 0x0F) << 8)) & _KEY_MASK


def make(i2c, address=0x50):
    "Return real driver if i2c bus exists, else a stub."
    if i2c is None:
        return BS8112AStub()
    return BS8112A(i2c, address)
