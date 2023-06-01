import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.popups.ui_mt_model_create import Ui_MtModelCreate


class MtModelCreate(QDialog, Ui_MtModelCreate):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Название модели')
        self.setWindowTitle('Создание модели')
        self.pushButton.clicked.connect(self.on_create_model)

    def on_create_model(self):
        value = self.lineEdit.text()
        self.parent().on_create_model(value, self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = MtModelCreate()
    form.show()
    sys.exit(app.exec())
