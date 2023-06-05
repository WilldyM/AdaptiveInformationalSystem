import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.popups.ui_tt_tuple_create import Ui_TtTupleCreate


class PopupTupleCreate(QDialog, Ui_TtTupleCreate):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Наименование кортежа')
        self.setWindowTitle('Создание кортежа')
        self.pushButton.clicked.connect(self.on_create_tuple)

    def on_create_tuple(self):
        value = self.lineEdit.text()
        self.parent().on_create_tuple(value, self)

