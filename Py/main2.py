import board
import W25Q128
import sys
import uos

def mount():
    w = W25Q128.W25Q128(board.flash_spi, board.flash_cs)
    b = W25Q128.BlockDev(w, board.flash_fs_size)
    fs = uos.VfsLfs2(b, mtime=False)
    uos.mount(fs, "/ext")
    sys.path.append("/ext")

mount()
