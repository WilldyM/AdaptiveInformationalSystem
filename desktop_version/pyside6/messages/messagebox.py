import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class MessageInfo(QMessageBox):

    def __init__(self, title, text):
        super().__init__()
        self.resize(300, 200)
        self.setIcon(QMessageBox.Information)
        self.setWindowTitle(title)
        self.setText(text)
        self.exec()


class MessageError(QMessageBox):

    def __init__(self, title, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(300, 200)
        self.setIcon(QMessageBox.Critical)
        self.setWindowTitle(title)
        self.setText(text)
        self.exec()
