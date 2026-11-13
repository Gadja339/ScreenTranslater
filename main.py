
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


from overlay import Overlay
from mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("icon.png"))

    overlay = Overlay()
    window = MainWindow(overlay)

    app.aboutToQuit.connect(overlay.stop_worker)

    window.show()
    overlay.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
