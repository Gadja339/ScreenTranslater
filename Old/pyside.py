import sys

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QCursor


class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # Прямоугольник в локальных координатах окна
        self.word_rect = QRect(200, 200, 150, 40)

        self.hovered = False

        # Оверлей на основном экране
        self.setGeometry(
            QApplication.primaryScreen().geometry()
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_cursor)
        self.timer.start(30)

    def check_cursor(self):
        pos = self.mapFromGlobal(QCursor.pos())

        hovered = self.word_rect.contains(pos)
        self.word_rect.moveCenter(pos)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.hovered:
            painter.setPen(
                QPen(QColor(0, 180, 255), 2)
            )
            painter.setBrush(
                QColor(0, 180, 255, 60)
            )
        else:
            painter.setPen(
                QPen(QColor(255, 255, 255, 150), 1)
            )
            painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRect(self.word_rect)


app = QApplication(sys.argv)

overlay = Overlay()
overlay.show()

sys.exit(app.exec())