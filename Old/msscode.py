import mss
import mss.tools
import numpy as np

with mss.MSS() as sct:
    monitor = sct.monitors[1]
    print(monitor.width)
    #print(sct.monitors[0])