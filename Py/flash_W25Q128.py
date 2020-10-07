#Flash memory abstraction layer for recording looper tracks to an on-board memory chip
#Copyright 2020 Thomas TEMPE

# Limitations of W25Q128:
# * each write operation can only write within a 256-byte page (address ends with 0x00).
# * need to erase (in min 4kB blocks) before writing
# * writing and erasing can take a long time (up to a minute)

#Strategy:
# * Allocate fixed block for each looper track.
# * erase a the memory immediately (in sequence, through self.loop()) when a loop is deleted
# * check the status before reading, and suspend the write if needed
# * block a user action that may cause a 2nd write in the UI for as long as the previous one is not finished
# * record the loop status in the UC flash memory before starting to erase, and after finishing recording
# * on startup, check that each erased loops are successfully erased
# * Buffer write operations to a local buffer. Try writing as soon as possible.
# * Check for BUSY status before accepting to start recording a loop.
# * Buffer the last read operations of one Midi command. If more is needed, suspend/resume the write operation, and perform a single read, to avoid disruption to the real-time playback.

#Open loopholes:
# * if you finish recording a loop, but the last Write operation (3ms max) did not finish before power loss, the end of the loop could be corrupted.

#TODO:
# * display write/erase or erase_whole_chip status on the screen
# * count the number of "read status" operations per cycle; add a test to only check every 40 ms?
# * handle all exceptions raised below

from machine import Pin, SPI
import W25Q128
import errno

class FlashError(RuntimeError):
    pass

class Flash:
    def __init__(self, nb_loops = 8):        
        self.ic = W25Q128.W25Q128(SPI(1), Pin("B12", Pin.OUT))
        self.nb_loops = nb_loops
        #Round down to an integer number of erase block sizes, to avoid erasing the beginning of the next loop
        self.memory_per_loop = (self.ic.capacity//nb_loops//self.ic.erase_block_size)*self.ic.erase_block_size 
        self.current_loop = None          #a loop here is one record (track), corresponding to one key of the looper
        self.write_buffer = bytearray(64) #small in-memory write buffer
        self.page_cursor = None           #cursor inside self.write_buffer. (Points to the end of valid data inside write_buffer)
        self.ic_cursor = 0                #cursor for writing in the flash IC. Position is relative to the start of that loop
        self.erase_cursor = None
        self.erase_start = None
        self.message = bytearray(8)
        self.read_cursors = [0]*nb_loops   #one cursor per loop
        self.read_buffer = [None]*nb_loops #one message per loop                    
        
    def check_erased(self, exists):
        """Check that every loop that is not recorded in the instrument is properly erased in flash, to avoid data corruption when recording on an un-erased sector.
        To be called on power-up, with a function for checking whether each track exists.
        """
        #Assumption 1: since the instrument doesn't let you start recording/erasing the 2nd loop before the 1st one is erased, on startup,
        #either you need to erase nothing, one loop (the instrument was turned off before erasing could finish), or the whole chip (factory 1st boot).
        #If at least 2 tracks need reset, it means the flash IC is new. Erase the whole chip.
        #Assumption 2: Erased IC memory value is 0xFF, which is not an expected value message.
        #Assumption 3: we erase tracks from end to start, and the IC chip possibly erases each block from start to end.
        #So, checking for the 1st and last byte of the 1st erase block of each loop should be enough
        error_tracks = []
        
        #Check all tracks
        for i in range(self.nb_loops):
            if not(exists(i)) and (self.ic.read(i * self.memory_per_loop, 1)[0] != 0xFF or self.ic.read(i * self.memory_per_loop - 1 + self.ic.erase_block_size, 1)[0] != 0xFF):
                #If the track is listed as deleted, but we find data for it in the flash IC (the 1st and last bytes of the 1st block are not both 0xFF)
                error_tracks.append(i)
        #print("tracks to erase: ", error_tracks)
        if len(error_tracks)>1:
            #Assume the whole chip is unformatted. Erase everything.
            print("Erasing whole chip. This will take 1~3 minutes")
            #TODO: display on the screen
            self.ic.erase_whole_chip()
            return 1
        elif 1==len(error_tracks):
            #Erase the whole loop
            #TODO: display on the screen
            print("Erasing track", error_tracks[0])
            self.erase(error_tracks.pop())
            return 0
        

    def start_recording(self, loop):
        #Does not check the machine state or memory status
        if self.ic.busy():
            raise FlashError("IC is busy")
        self.current_loop = loop
        self.page_cursor = 0   #cursor inside self.write_buffer
        self.ic_cursor = 0     #cursor for writing on the IC

        
    def record(self, buffer):
        if self.page_cursor + len(buffer) > len(self.write_buffer):
            #Memory overrun of the write buffer
            raise FlashError("Internal write buffer overrun")
        self.write_buffer[self.page_cursor:self.page_cursor+len(buffer)] = buffer
        self.page_cursor += len(buffer)
        
    def record_message(self, t, msg):
        "Records a midi message to the current loop."
        #Assumes either 2 or 3 octets for the message payload
        #Always writes 8 bytes per message       
        self.message[0]=(t>>24)
        self.message[1]=(t>>16)
        self.message[2]=(t>>8)
        self.message[3]=(t)
        if len(msg)==2:
            self.message[4:6]=msg[:]
            self.message[6]=0xFF #FF is an invalid value at this place in a MIDI message
        else:
            self.message[4:7]=msg[:]
        self.record(self.message)
        #print("recording message: ",t, msg, self.message)

    def write_page(self):
        "Write as much as possible to flash, in one go."
        if self.ic_cursor + self.page_cursor >= self.memory_per_loop:
            #Memory overrun on the chip.
            #TODO: handle?
            #This should never happen. 2Mb is enough to store 10 MIDI messages per second for 10 hours straight
            raise FlashError("Memory overrun while recording the loop")
        else:
            #Commit one write operation (as long as possible) to flash
            
            #First, determine how much to write
            start_of_write = self.memory_per_loop*self.current_loop + self.ic_cursor
            end_of_page = (start_of_write//self.ic.page_length + 1) * self.ic.page_length #limit the writing to the end of the page
            write_length = min( self.page_cursor, end_of_page-start_of_write)

            #Then commit to memory and update the internal buffer and cursors
            #print("Writing:", start_of_write, end_of_page, write_length, self.write_buffer[0:write_length])
            self.ic.write(start_of_write, self.write_buffer[0:write_length])
            
            self.write_buffer[0:self.page_cursor-write_length] = self.write_buffer[write_length:self.page_cursor]
            self.page_cursor -= write_length
            self.ic_cursor += write_length

    def erase(self, loop, length=None):
        "Erase a loop from the flash chip"
        #TODO: Display on the screen
        if not(length):
            length = self.memory_per_loop
        self.erase_start = loop * self.memory_per_loop
        #Starting from the last block.
        self.erase_cursor = (length // self.ic.erase_block_size) * self.ic.erase_block_size
        self.read_buffer[loop] = None

    def busy(self):
        "Is the flash device busy with any erase operation? (Refuse start of recording if so)"
        return bool((self.erase_cursor != None) or self.page_cursor >0 )

    def read_message(self, loop, cursor):
        "Returns one message. Caches one message from each loop in memory, for speed."
        #Assumes each message takes exactly 8 bytes in flash, and each MIDI payload is either 2 or 3 bytes
        if cursor != self.read_cursors[loop] or None == self.read_buffer[loop]:
            #update the read cache from flash
            self.read_cursors[loop] = cursor
            r = self.ic.read(self.memory_per_loop * loop + cursor * 8, 7)
            t = (r[0]<<24)+(r[1]<<16)+(r[2]<<8)+(r[3])
            #print("extracted from memory:", r)
            if 0xFF==r[6]:
                msg = r[4:6]
            else:
                msg = r[4:7]
            self.read_buffer[loop] = [t, msg]
        return self.read_buffer[loop]

    def finish_recording(self):
        #There might be some writing left to do (eg: self.page_cursor > 0).
        #Don't destruct anything.
        self.read_buffer[self.current_loop] = None

    def loop(self):
        if (self.erase_cursor != None) and not self.ic.busy():
            #Erase the next block
            if (self.ic.read(self.erase_cursor, 7)[0] != 0xFF):
                #Only erase if there's data written, to go faster.
                #0x00 gets written as the last byte of each record
                self.ic.erase_block(self.erase_cursor)
            if self.erase_cursor == self.erase_start:
                #We just sent the last order
                self.erase_cursor = None
                #print("Track", self.erase_start/self.ic.erase_block_size, "erase complete")
            else:
                self.erase_cursor -= self.ic.erase_block_size
        elif self.page_cursor and not self.ic.busy():
            #Midi message left to be written to memory
            self.write_page()

    def print(self, loop, pos, len):
        "print midi messages stored in memory, for debugging purposes"
        for i in range(len):
            t, m = self.read_message(loop, pos+i)
            print(t/48, m)

#Debug code. TODO:Remove
f = Flash()

#End