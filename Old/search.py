import mss
import mss.tools 
from pathlib import Path
import pytesseract
from PIL import Image  

folder = Path('./Screenshots')
scnum = 0
for scts in folder.iterdir():
    scnum += 1

with mss.mss() as sct:
    monitor = sct.monitors[1]

    screenshot = sct.grab(monitor)

    mss.tools.to_png(screenshot.rgb, screenshot.size, output = f'./Screenshots/image{scnum}.png')

    text = pytesseract.image_to_string(f'./Screenshots/image{scnum}.png', lang = 'eng')

print(text)