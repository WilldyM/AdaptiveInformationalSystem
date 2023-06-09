import sys

from PySide6.QtWidgets import QApplication

from desktop_version.pyside6.main import MainWindow, on_start_up


if __name__ == '__main__':
    on_start_up()
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    sys.exit(app.exec())
