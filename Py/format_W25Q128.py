import board
import W25Q128
import uos

w = W25Q128.W25Q128(board.flash_spi, board.flash_cs)
b = W25Q128.BlockDev(w, 256) #1Mb

#Format
uos.VfsLfs2.mkfs(b)
#uos.VfsFat.mkfs(b)

#Mount
fs = uos.VfsLfs2(b, mtime=False)
#fs = uos.VfsFat(b)

uos.mount(fs, "/img")

#End