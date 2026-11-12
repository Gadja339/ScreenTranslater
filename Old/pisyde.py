import sys

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QCursor

app = QApplication(sys.argv)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Screen Translator")
        self.resize(500, 500)

        self.pryamo = QRect(0, 0, 100, 100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_cursor)
        self.timer.start(30)

    def check_cursor(self):
        pos = self.mapFromGlobal(QCursor.pos())
        self.pryamo.moveCenter(pos)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setBrush(QColor(0, 180, 255, 60))
        painter.drawRect(self.pryamo)

    

mainy = MainWindow()
mainy.show()

sys.exit(app.exec())
