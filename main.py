
import sys
from PySide6.QtWidgets import QApplication

from overlay import Overlay
from mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)

    overlay = Overlay()
    window = MainWindow(overlay)

    app.aboutToQuit.connect(overlay.stop_worker)

    window.show()
    overlay.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
