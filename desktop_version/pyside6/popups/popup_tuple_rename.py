import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo
from desktop_version.pyside6.popups.ui_tt_tuple_rename import Ui_TtTupleRename


class PopupTupleRename(QDialog, Ui_TtTupleRename):

    def __init__(self, parent, item: CustomTreeWidgetItem, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.item = item
        self.lineEdit.setPlaceholderText('Наименование кортежа')
        self.pushButton.clicked.connect(self.on_rename_tuple)

    def on_rename_tuple(self):
        value = self.lineEdit.text()
        if value != '':
            self.parent().on_rename_tuple(item=self.item, value=value, popup=self)
        else:
            MessageInfo('Переименование объекта', 'Поле не может быть пустым')
