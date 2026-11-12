from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Slot

from translationpopup import TranslationPopup

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
        if self.overlay.isVisible():
            self.overlay.hide()
            self.hideoverlay.setText("Показать Оверлей")
        else:
            self.overlay.show()
            self.hideoverlay.setText("Скрыть Оверлей")

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
