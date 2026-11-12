import mss 
import sys
import numpy as np
import pytesseract
from mss.tools import to_png

from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
from pytesseract import Output

import cv2

folder = Path('./Screenshots')
scnum = 0
for scts in folder.iterdir():
    scnum += 1

app = QApplication(sys.argv)

WIDTH = 300
HEIGHT = 100

with mss.MSS() as sct:
    screen = sct.monitors[1]

    pos = QCursor.pos()

    mouse_x = pos.x()
    mouse_y = pos.y()

    # Желаемое положение области
    left = mouse_x - WIDTH // 2
    top = mouse_y - HEIGHT // 2

    # Границы экрана
    min_left = screen["left"]
    min_top = screen["top"]

    max_left = screen["left"] + screen["width"] - WIDTH
    max_top = screen["top"] + screen["height"] - HEIGHT

    # Ограничение положения области
    left = max(min_left, min(left, max_left))
    top = max(min_top, min(top, max_top))

    region = {
        "left" : left,
        "top" : top,
        "width" : WIDTH,
        "height" : HEIGHT
        }

    screenshot = sct.grab(region)
    image = np.asarray(screenshot)

    image = cv2.cvtColor( image, cv2.COLOR_BGRA2RGB)

    data = pytesseract.image_to_data(image, lang = "eng", config="--psm 6", output_type=Output.DICT)

    print("\nРаспознанные слова:")

    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue

        print(
            f"{word!r}: "
            f"x={data['left'][i]}, "
            f"y={data['top'][i]}, "
            f"w={data['width'][i]}, "
            f"h={data['height'][i]}, "
            f"confidence={data['conf'][i]}"
        )

    to_png(screenshot.rgb, screenshot.size, output = f'./Screenshots/debug{scnum}.png')

    print("Положение мыши:", mouse_x, mouse_y)
    print("Область захвата:", region)

    local_x = mouse_x - left
    local_y = mouse_y - top

    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue

        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]

        if(x < local_x < (x + w) and y < local_y < y + h):
            print("Слово: ", word)
            print("Координаты:", left + x, top + y)
            print("Длина:", w, "Ширина:", h)
            break
    else:
            print("Слова нет") 
