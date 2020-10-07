#W25Q128 driver
#Copyright 2020 Thomas TEMPE
#DWTFYL license

import time

#W25Q128 is a 128 Mbit (16 Mo) SPI flash memory with 4kB sectors
#address space is 24 bit, which is exactly 16 Mo
#write operations: memory is split into 64k pages of 256 bytes each
#
#BUS:
# * reads data on the rising edge of CLK, writes on the falling edge
# * Supports SPI bus speed of up to 133MHz with the "fast read" instruction (104MHz with voltage <3.0V)
# * Supports SPI bus speed of up to 50MHz with the "read" instruction
# * Also supports dual/quad operations (data bus width of 2 or 4 bits). We're not using these.

#Power consumption is up to 25mA during write operations, but max 60uA in standby
#The chip is not initialized when it is new

# Limitations:
# * each write operation can only write within a 256-byte page (address ends with 0x00).
# * need to erase (in min 4kB blocks) before writing
# * writing and erasing can take a long time (up to a minute)

class W25Q128:
    def __init__(self, spi, cs):
        "class for one W25Q128 flash memory IC. cs is a Pin object for the SPI cable select pin"
        self.spi = spi
        self.cs = cs
        self.rate = 50000000#50MHz
        self.last_op_was_write = False
        self.page_length = 256 #for writing
        self.erase_block_size = 65536 #needs to match the instructions in erase_block()

        #Start communicating with the device
        self.reinit()
        id = self.get_id()
        if not (id[0] in [0xEF]):
            print("Warning: unknown flash memory chip manufacturer. Proceeding anyways")
        self.capacity = { 64:16*1024*1024 }[id[1]] #Fill in additional chip values here
        
    def reinit(self):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)

    def send_command(self, cmd, addr=None, write=None, read=None):
        "Send a single SPI command. Optionally write data specified in 'write'. Optionally read and return 'read' bytes."
        #self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        r = None
        self.cs(0)
        self.spi.write(cmd)
        if addr != None:
            self.spi.write(bytes( [ (addr>>16)&0xFF, (addr>> 8)&0xFF, (addr)&0xFF ] ) )
        if write != None:
            self.spi.write(bytearray(write))
        if read != None:
            r = self.spi.read(read)
        self.cs(1)
        return r

    def get_id(self):
        return self.send_command(b"\x9F", read=2)

    def read(self, addr, len):
        #Reading 1~8 bytes typically takes 180 us
        busy = self.busy()
        if busy:
            #Chip is busy with a long write/erase operation
            self.send_command(b"\x75") #Suspend
            time.sleep_us(20)
        r = self.send_command(b"\x03", addr, read=len) # Read
        if busy:
            #Chip was busy. Resume write/erase operation
            self.send_command(b"\x7A") #Resume
            time.sleep_us(20)
        return r

    def erase_block(self, addr):
        "erase a block"
        #erase time per block, typical/max
        #4kB: 45/400ms
        #32kB: 120/1600ms
        #64kB: 150/2000ms
        self.last_op_was_write = True
        self.send_command(b"\x06") #Write enable
        
        ##if you change this, remember to adjust self.erase_block_size in __init__()
#        self.send_command(b"\x20", addr = addr&0xFFF000) #erase 4k sector
#        self.send_command(b"\x52", addr = addr&0xFF8000) #erase 32k block
        self.send_command(b"\xD8", addr = addr&0xFF0000) #erase 64k block

    def erase_whole_chip(self):
        #Takes between 40s (typical)  and 200s (max)
        self.last_op_was_write = True
        self.send_command(b"\x06") #Write enable
        self.send_command(b"\x60") #erase whole chip

    def write(self, addr, data):
        "Write within a 256-byte page."
        #Command 0x02: Page Program: write up to 256 bytes of data onto previously erased (0xFF) memory location
        #A partial page write is possible, but each call can only write within one page.
        #If writing beyond the page boundary, the write operation will wrap to the beginning of the page.
        #One full page write takes typical 0.7ms (max 3ms)
        #Sending one full page takes ~510us
        self.last_op_was_write = True
        self.send_command(b"\x06") #Write enable
        self.send_command(b"\x02", addr, write=data) #Write enable
    
    def busy(self):
        "Checks whether the previous write/erase operation is complete."
        #Call command "read_status_register", check the "BUSY" bit
        if True == self.last_op_was_write:
            busy = self.send_command(b"\x05", read=1)[0]&1
            if busy:
                return True
            else:
                self.last_op_was_write = False
        return False

# Test code
from machine import Pin, SPI
Pin("B8",  Pin.OUT).value(1)
Pin("A8", Pin.OUT).value(1)
Pin("C3", Pin.OUT).value(1)
Pin("C5", Pin.OUT).value(1)

flash = W25Q128(SPI(1), Pin("B12", Pin.OUT))

# #test busy
# #flash.write(0, b"Hello world")
# t = time.ticks_us()
# flash.read(0,10)
# print(time.ticks_us()-t)
# flash.erase_64k(65536)
# flash.read(0,10)

#End
