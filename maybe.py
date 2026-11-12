import sys
import mss
import requests
from mss.tools import to_png
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPoint, QThread, Slot, QObject
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
import cv2
import pytesseract
from pytesseract import Output
import time 


folder = Path('./Screenshots')
WIDTH = 300
HEIGHT = 100

class TranslationPopup(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.PlainText)

        self.label.setStyleSheet("""
            QLabel {
                background-color: #242B36;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 30px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.hide()

    def show_translation(self, text, pos):

        self.label.setText(text)
        self.adjustSize()

        self.move(pos)
        self.show()


class TranslateWorker(QObject):

    result = Signal(str, str)
    error = Signal(str, str)

    @Slot(str)
    def translate(self, word):
        try:
            response = requests.get(
                "https://api.mymemory.translated.net/get",
                params={
                    "q": word,
                    "langpair": "en|ru"
                },
                timeout=5
            )

            response.raise_for_status()
            data = response.json()

            if data.get("responseStatus") != 200:
                raise ValueError(
                    data.get("responseDetails")
                    or "Translation API error"
                )

            translation = data["responseData"]["translatedText"]

            self.result.emit(word, translation)

        except Exception as e:
            self.error.emit(word, str(e))



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


class Overlay(QWidget):
    cursor_moved = Signal(int, int)
    find_word = Signal(str)

    request_ocr = Signal(object)

    request_translate = Signal(str)
    translation_ready = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.translation_cache = {}

        self.translate_target = ""
        self.translation_inflight = None

        self.translate_timer = QTimer(self)
        self.translate_timer.setSingleShot(True)
        self.translate_timer.setInterval(350)

        self.translate_timer.timeout.connect(
            self.start_translation_if_needed)

        self.last_cursor_pos = QCursor.pos()

        self.capture_pending = False    

        self.last_move_time = time.monotonic()
        self.last_request_time = 0.0
        self.last_capture_time = 0.0

        self.idle_delay = 0.3
        self.refresh_interval = 1.5

        #Поток для OCR

        self.ocr_thread = QThread(self)

        self.ocr_worker = OCRWorker()
        self.ocr_worker.moveToThread(self.ocr_thread)

        self.request_ocr.connect(self.ocr_worker.process)
        self.ocr_worker.result.connect(self.on_ocr_result)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_thread.finished.connect(self.ocr_worker.deleteLater)
        
        self.ocr_thread.start()

        #Поток для перевода 

        self.translate_thread = QThread(self)

        self.translate_worker = TranslateWorker()
        self.translate_worker.moveToThread(self.translate_thread)

        self.request_translate.connect(
            self.translate_worker.translate)

        self.translate_worker.result.connect(
            self.on_translate_result)

        self.translate_worker.error.connect(
            self.on_translate_error)
        self.translate_thread.finished.connect(
            self.translate_worker.deleteLater)

        self.translate_thread.start()

        #

        self.show_debug_rect = False    

        self.current_word = ""

        self.region = None
        self.data = {"text": []}

        self.local_x = 0
        self.local_y = 0
        self.scnum = 0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setGeometry(QApplication.primaryScreen().geometry())

        self.pryamo = QRect(0, 0, 300, 100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_cursor)
        self.timer.start(30)

        self.photo_timer = QTimer(self)
        self.photo_timer.timeout.connect(self.check_photo)
        self.photo_timer.start(50)



    def schedule_translation(self, word):

        self.translate_timer.stop()

        word = word.strip().strip(".,!?;:\"'()[]{}").lower()

        self.translate_target = word

        if not word:
            self.translation_ready.emit("", "")
            return

        if word in self.translation_cache:
            translation = self.translation_cache[word]
            self.translation_ready.emit(word, translation)
            return

        self.translation_ready.emit(word, "Переводится...")

        self.translate_timer.start()



    def start_translation_if_needed(self):

        word = self.translate_target

        if not word:
            return

        if word in self.translation_cache:
            self.translation_ready.emit(
                word,
                self.translation_cache[word]
            )
            return

        # Предыдущий HTTP-запрос ещё выполняется
        if self.translation_inflight is not None:
            return

        self.translation_inflight = word

        self.request_translate.emit(word)



    @Slot(str, str)
    def on_translate_result(self, word, translation):

        self.translation_cache[word] = translation

        self.translation_inflight = None

        if word == self.translate_target:
            self.translation_ready.emit(word, translation)

        elif (
            self.translate_target
            and not self.translate_timer.isActive()
        ):
            self.start_translation_if_needed()


    @Slot(str, str)
    def on_translate_error(self, word, message):

        print(f"Ошибка перевода {word}: {message}")

        self.translation_inflight = None

        if word == self.translate_target:
            self.translation_ready.emit(
                word,
                "Ошибка перевода"
            )

        elif (
            self.translate_target
            and not self.translate_timer.isActive()
        ):
            self.start_translation_if_needed()


    @Slot(object, object)
    def on_ocr_result(self, region, data):

        self.region = region
        self.data = data

        self.last_capture_time = time.monotonic()
        self.capture_pending = False

        self.take_a_word_under_cursor()




    @Slot(str)
    def on_ocr_error(self, message):

        print("Ошибка OCR:", message)

        self.capture_pending = False





    def check_photo(self):

        if self.capture_pending:
            return

        now = time.monotonic()
        pos = QCursor.pos()

        if pos != self.last_cursor_pos:
            self.last_cursor_pos = pos
            self.last_move_time = now
            return

        if now - self.last_move_time < self.idle_delay:
            return

        # Не повторяем неудачные запросы слишком часто
        if now - self.last_request_time < 0.5:
            return

        outside_region = self.region is None

        if self.region is not None:
            r = self.region

            outside_region = not (
                r["left"] <= pos.x() < r["left"] + r["width"]
                and
                r["top"] <= pos.y() < r["top"] + r["height"]
            )

        outdated = (
            now - self.last_capture_time
            >= self.refresh_interval
        )

        if outside_region or outdated:
            self.take_a_photo()





    def check_cursor(self):
        pos = QCursor.pos()
        
        self.cursor_moved.emit(pos.x(), pos.y())
        
        self.take_a_word_under_cursor()




    def take_a_photo(self):

        if self.capture_pending:
            return

        pos = QCursor.pos()

        screen = (
            QApplication.screenAt(pos)
            or QApplication.primaryScreen()
        )

        bounds = screen.geometry()

        width = min(WIDTH, bounds.width())
        height = min(HEIGHT, bounds.height())

        left = pos.x() - width // 2
        top = pos.y() - height // 2

        min_left = bounds.x()
        min_top = bounds.y()

        max_left = bounds.x() + bounds.width() - width
        max_top = bounds.y() + bounds.height() - height

        left = max(min_left, min(left, max_left))
        top = max(min_top, min(top, max_top))

        region = {
            "left": left,
            "top": top,
            "width": width,
            "height": height
        }

        self.capture_pending = True
        self.last_request_time = time.monotonic()

        self.request_ocr.emit(region)




    def take_a_word_under_cursor(self):
        if self.region is None:
            return
        pos = QCursor.pos()

        local_x = pos.x() - self.region["left"]
        local_y = pos.y() - self.region["top"]

        found_word = ""
        self.show_debug_rect = False

        

        for i, word in enumerate(self.data["text"]):

            if not word.strip():
                continue

            x = self.data["left"][i]
            y = self.data["top"][i]
            w = self.data["width"][i]
            h = self.data["height"][i]

            if (x <= local_x < x + w and y <= local_y < y + h):

                global_x = self.region["left"] + x
                global_y = self.region["top"] + y

                local_pos = self.mapFromGlobal(
                    QPoint(global_x, global_y)
                )

                found_word = word

                self.pryamo = QRect(local_pos.x(), local_pos.y(), w, h)

                self.show_debug_rect = True
                break
        if found_word != self.current_word:
            self.current_word = found_word
            self.find_word.emit(found_word)
            
            self.schedule_translation(found_word)
        self.update()


    def stop_worker(self):

        self.timer.stop()
        self.photo_timer.stop()
        self.translate_timer.stop()

        self.ocr_thread.quit()
        self.translate_thread.quit()

        self.ocr_thread.wait()
        self.translate_thread.wait()


    def paintEvent(self, event):
        if not self.show_debug_rect:
            return
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 180, 255, 60), 2))
        painter.setBrush(QColor(0, 180, 255, 60))
        painter.drawRect(self.pryamo)






class MainWindow(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.popup = TranslationPopup(self)

        self.overlay.translation_ready.connect(self.show_popup_translation)

        self.setWindowTitle("Goida")

        self.setGeometry(100, 50, 100, 50)

        layout = QVBoxLayout()

        self.pushbutton = QPushButton("Exit")
        self.text = QLabel("Координаты: ")
        self.hideoverlay = QPushButton("Скрыть Оверлей")
        self.word = QLabel("увиденное слово:")
        self.translateword = QLabel("Перевод Слова: ")

        layout.addWidget(self.text)
        layout.addWidget(self.pushbutton)
        layout.addWidget(self.hideoverlay)
        layout.addWidget(self.word)
        layout.addWidget(self.translateword)

        self.setLayout(layout)

        self.overlay.cursor_moved.connect(self.change_coordinates)
        self.pushbutton.clicked.connect(QApplication.exit)
        self.hideoverlay.clicked.connect(self.hide_overlay)
        self.overlay.find_word.connect(self.change_word)
        self.overlay.translation_ready.connect(self.change_translation)


    def change_coordinates(self, x, y):
        self.text.setText(f"Курсор x = {x}, y = {y}")


    @Slot(str, str)
    def change_translation(self, word, translation):
        if word:
            self.translateword.setText(f"Перевод: {translation}")
        else:
            self.translateword.setText("Перевод: —")


    def change_word(self, word):
        if word:
            self.word.setText(f"Найденное слово: {word}")
        else:
            self.word.setText("Нечего")


    def hide_overlay(self):
        if overlay.isVisible():
            self.overlay.hide()
            self.hideoverlay.setText("Показать Оверлей")
        else:
            self.overlay.show()
            self.hideoverlay.setText("Скрыть оверлей")

    @Slot(str, str)
    def show_popup_translation(self, word, translation):

        if not word or translation in (
            "Переводится...",
            "Ошибка перевода"
        ):
            self.popup.hide()
            return

        pos = self.overlay.mapToGlobal(self.overlay.pryamo.bottomLeft())

        pos.setY(pos.y() + 8)

        self.popup.show_translation(f"{word} — {translation}",pos)

app = QApplication(sys.argv)

overlay = Overlay()
window = MainWindow(overlay)

app.aboutToQuit.connect(overlay.stop_worker)

window.show()
overlay.show()


sys.exit(app.exec())


