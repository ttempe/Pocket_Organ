from machine import Pin, I2C
import time
import TTY6955


i2c = I2C(scl="B6", sda="B7", freq=100000) #Note: TTY6955 is limited to 100kHz i2c
time.sleep_ms(100)

def test_all_buttons():
    touch_sensor = TTY6955.TTY6955(i2c)
    time.sleep_ms(2000) #Auto calibration can take a long time
                        #until done, read() will raise an exception
    while 1:
        touch_sensor.read() #read the data from the IC
        touch_sensor.output_debug()
        time.sleep_ms(200)        

def test_slider():
    touch_sensor = TTY6955.TTY6955(i2c, slider1_pads=3) #the first 3 pads are grouped together
    time.sleep_ms(2000) #Auto calibration can take a long time
                        #until done, read() will raise an exception
    while 1:
        touch_sensor.read() #read the data from the IC
        (touched, value) = touch_sensor.slider(1) #pins TP0, TP1, TP2
        print("Slider1: touched = {}; value = {}".format(touched, value))
        button_touched = touch_sensor.button(0) #pin TP3
        time.sleep_ms(200)        

def test_buttons():
    touch_sensor = TTY6955.TTY6955(i2c)
    time.sleep_ms(2000) #Auto calibration can take a long time
                        #until done, read() will raise an exception
    while 1:
        touch_sensor.read() #read the data from the IC
        print(
            touch_sensor.button(0), ",", #pin TP0
            touch_sensor.button(1), ",", #pin TP1
            touch_sensor.button(2)       #pin TP2
            )
        time.sleep_ms(200)        
