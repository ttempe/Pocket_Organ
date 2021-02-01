import board
import W25Q128
import uos

w = W25Q128.W25Q128(board.flash_spi, board.flash_cs)
b = W25Q128.BlockDev(w, board.flash_fs_size)

def format():
    uos.VfsLfs2.mkfs(b)
    #uos.VfsFat.mkfs(b)

def mount():
    fs = uos.VfsLfs2(b, mtime=False)
    #fs = uos.VfsFat(b)
    uos.mount(fs, "/ext")

def checksum(filename):
    fd = open(filename)
    s = 0
    r = bytearray(fd.read())
    for v in r:
        s = (s+v)&65535
    fd.close()
    return s, len(r)

def copy(f1, f2):
    fd1=open(f1)
    fd2=open(f2, "w")
    d = fd1.read()
    print("Copying {}:\t{} bytes\t".format(f1, len(d)), end="")
    fd2.write(d)
    fd1.close()
    fd2.close()
    (s1, l1) = checksum(f1)
    (s2, l2) = checksum(f2)
    if s1==s2 and l1==l2:
        print("checksum OK")
    else:
        print("Checksum: error")
    
def store(file):
    copy("/flash/"+file, "/ext/"+file)
    print(checksum("/flash/"+file))
    print(checksum("/ext/"+file))
    
def move(file):
    copy("/flash/"+file, "/ext/"+file)
    uos.remove("/flash/"+file)
    
def move_all():
    for (filename, type, *a) in uos.ilistdir("/flash"):
        if type == 0x8000 and filename[-4:]==".pbm": #regular file
            copy("/flash/"+filename, "/ext/"+filename)
            uos.remove("/flash/"+filename)

def check_all():
    for (filename, type, *a) in uos.ilistdir("/flash"):
        if type==0x8000 and filename[-3:]==".py":
            print(filename)
            fd=open("/flash/"+filename)
            if not len(fd.read()):
                print(" ! Empty file")        
            fd.close()

def ls():
    print("/flash: {}".format(uos.listdir("/flash")))
    print("/ext: {}".format(uos.listdir("/ext")))    

#End
    