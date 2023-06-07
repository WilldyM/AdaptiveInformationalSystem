import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo
from desktop_version.pyside6.popups.ui_tt_tuple_part_rename import Ui_TtTuplePartRename


class PopupTuplePartRename(QDialog, Ui_TtTuplePartRename):

    def __init__(self, parent, item: CustomTreeWidgetItem, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.item = item
        self.lineEdit.setPlaceholderText('Наименование операнда')
        self.pushButton.clicked.connect(self.on_rename_tuple_part)

    def on_rename_tuple_part(self):
        value = self.lineEdit.text()
        if value != '':
            self.parent().on_rename_tuple_part(item=self.item, value=value, popup=self)
        else:
            MessageInfo('Переименование операнда', 'Поле не может быть пустым')
