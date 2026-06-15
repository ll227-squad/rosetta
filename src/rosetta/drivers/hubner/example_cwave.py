import time
import math
import gtr

cwave = gtr.Gtr()

cwave.connect('192.168.202.10')

status = cwave.get_status()

print(status)
