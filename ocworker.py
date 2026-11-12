import cv2
import mss
import pytesseract
import numpy as np
from pytesseract import Output
from PySide6.QtCore import Slot, QObject, Signal


class OCRWorker(QObject):

    result = Signal(object, object)
    error = Signal(str)

    @Slot(object)
    def process(self, region):
        try:
            with mss.MSS() as ms:
                screenshot = ms.grab(region)

            image = np.asarray(screenshot)

            image = cv2.cvtColor(
                image,
                cv2.COLOR_BGRA2RGB
            )

            data = pytesseract.image_to_data(
                image,
                lang="eng",
                config="--psm 6",
                output_type=Output.DICT
            )

            self.result.emit(region, data)

        except Exception as e:
            self.error.emit(str(e))