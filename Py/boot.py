#Set Micropython to load modules from the flash by default, and fall back to frozen modules.
from sys import path
if path[0] == "":
    path.pop(0)
    path.append("")
