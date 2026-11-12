from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

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
