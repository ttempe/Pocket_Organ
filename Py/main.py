import board

pin = board.main_startup_pin
if not(pin()):
    #Start if the "volume" key is pressed on startup
    import fileutils
    fileutils.mount()
    import pocket_organ
else:
    print("Hold the Volume key while powering on to start the instrument")

#End
