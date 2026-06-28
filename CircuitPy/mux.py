# MUX shift-register addressing and hall-sensor power control.
# GPIO pins are defined in board_po.py.
import board_po as board, time

def set_addr(addr):
    board.keyb_muxA.value = addr & 0x2
    board.keyb_muxB.value = addr & 0x4
    board.keyb_muxC.value = addr & 0x8


def read_addr(addr):
    "For calibration"
    power_on()
    set_addr(addr)
    adc = board.keyb_ADC[addr&0x1]
    time.sleep(0.00001) #let it settle, 10us
    val = (adc.value+adc.value)>>1
    power_off()
    return val


def power_on():
    if board.keyb_vbus is not None:
        board.keyb_vbus.value = False


def power_off():
    if board.keyb_vbus is not None:
        board.keyb_vbus.value = True


def vbat_read():
    "Return Volts"
    power_on()
    set_addr(board.vbat_addr)
    v = read_addr(board.vbat_addr) / .32 * 3.3 / 65535
    power_off()
    return v


def vusb_read():
    "Return Volts"
    power_on()
    set_addr(board.vusb_addr)
    v = read_addr(board.vusb_addr) / .32 * 3.3 / 65535
    power_off()
    return v

