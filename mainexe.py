import sys

from PySide6.QtWidgets import QApplication

from desktop_version.pyside6.main import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    sys.exit(app.exec())
