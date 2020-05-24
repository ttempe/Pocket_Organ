# Micropython driver for the TTY6955/TTY6945
# Capacitive touch key sensor IC
# Copyright 2020, Thomas TEMPE
# DWTFYL license.
#
# The two IC apparently have the same features and protocole,
# and differ only by the number of pads they can drive.
# Warning: these chip can drive up to 3 sliders, but can't detect when you touch 2 sliders
# at the same time.
#


import errno

class TTY6955:
    def __init__(self, i2c, addr=0x50,
                 slider1_pads=0, slider2_pads=0, slider3_pads=0,
                 single_key_mode=False, power_save_mode=False, dynamic_threshold=True,
                 auto_reset_mode = 0x01, key_acknowledge_times = 4, nb_keys=None):
        """
        Addr = i2c address of the TTY6955 chip
        sliderX_pads = number of pads to be used for each slider. Default is none.
        auto reset time: 0=disabled; 1=15s (default); 2=30s; 3=1min
        key_acknowledge_times = nb of times to detect a touch before reporting it.
        Recommended 3 or 4
        By default, nb_keys will be set to the maximum. override it to speed up reading.

        For the other parameters, please refer to the datasheet. Good luck.
        """
        nb_slider_pads = slider1_pads+slider2_pads+slider3_pads
        if nb_slider_pads>16:
            raise InputError("Too many slider pads (16 max)")
        self.i2c = i2c
        self.addr = addr
        self.output = []
        self.nb_sliders = bool(slider1_pads)+bool(slider2_pads)+bool(slider3_pads)
        if None == nb_keys:
            self.nb_keys = 16-nb_slider_pads
        else:
            self.nb_keys = nb_keys
        self.buf = bytearray(6)
        self.mv = memoryview(self.buf)
        self.buf[0] = ( 0x80 +                      #IICM + CT
                        0x20 * single_key_mode +    #KOM
                        0x10 +                      #AA : changed by set_thersholds() 
                        0x08 * power_save_mode +    #PSM
                        0x04 * dynamic_threshold +  #DT
                        auto_reset_mode             #ART
                        )
        self.buf[1] = ( ((self.nb_keys & 0x1F) << 3) +
                        ((key_acknowledge_times -1) & 0x7) #KAT
                        )
        self.buf[2] =   (slider2_pads << 4) + slider1_pads
        self.buf[3] = ( 0 +                         #Key off num
                        slider3_pads
                        )

        self.i2c.writeto(self.addr, self.mv[0:4])
        
    def set_threshold(self, pad, sensitivity):
        """
        Lets you set custom thresholds for each pad, for use
        with dynamic_threshold=False.
        sensitivity is a 12-bit integer.
        The lower the value, the more sensitive the pad.
        The datasheet recommends defaulting to 0x010, going no lower
        than 0x008. If sensitivity is still not sufficient with 0x008,
        it recommends increasing the CS capacitor (while keeping it under
        39 nF).
        """
        self.buf[0] = 0xC0 + (pad & 0x0F)
        self.buf[1] = sensitivity & 0x0FF
        self.buf[2] = (sensitivity & 0xF00) >> 8
        self.i2c.writeto(self.addr, self.mv[0:3])

    def set_sleep(self, threshold):
        """Set the TPSLP sleep mode thresholds.
        This is a 12-bit integer. It's not clear to me how it works,
        but it governs entering the sleep mode.
        The datasheet reports 1.1mA consumption while awake, and
        5.3~10.0 uA consumption while in sleep mode (VDD=3V).
        """
        self.buf[0] = 0xD0
        self.buf[1] = threshold & 0x0FF
        self.buf[2] = (threshold & 0xF00) >> 8
        self.i2c.writeto(self.addr, self.mv[0:3])        
                    
    def read(self):
        "call this method to actually read the data from the sensor"
        self.i2c.readfrom_into(self.addr, self.buf)
        self.buttons = self.buf[1] + (self.buf[2]<<8)
        #if not(self.buf[0] & 0b10000000):
        #    raise Exception("The touch IC reports invalid calibration.")

    def slider(self, num):
        """
        Takes the slider number as input: 1, 2, or 3
        returns a tuple: (is_pressed, slider value)
        the slider value is an integer between 0 and 255.
        
        Call read() before using!
        """
        return ((self.buf[0]>>(num-1))&1, self.buf[num+2])

    def button(self, num):
        """
        returns the state of the button.
        Note: button numbering skips any pads used for sliders.
        Eg: if you declare no sliders, then pin n. 2 (TP4) refers to button 4.
        However, if you declare a 3-pad slider, then the same pin n.2 (TP4) will become button 1.
        Buttons are counted from 0.
    
        Call read() before using!
        """
        return (self.buttons>>num) & 1

    def output_debug(self):
        """
        Displays the contents of the sensor output in binary display.
        Useful for debugging your board.
        
        Summary:
        * the first bit should be 1; otherwise all you're getting is noise.
        * the 2nd bit is 1 on reset, gets pulled down by any form of configuration
        * the last 3 bits of the 1st octet indicate whether the 3 sliders are being touched
        * the next 2 octets indicate the bit-by-bit status of all touch keys
        * the last 3 octets are the analog reading of the finger position on the 3 sliders

        Call read() before using!
        """
        for c in self.buf:
            print("{:08b} ".format(c), end="")
        print()