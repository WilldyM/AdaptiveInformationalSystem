import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo
from desktop_version.pyside6.popups.ui_mt_object_rename import Ui_MtObjectRename


class PopupObjectRename(QDialog, Ui_MtObjectRename):

    def __init__(self, parent, item: CustomTreeWidgetItem, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Наименование объекта')
        self.pushButton.clicked.connect(lambda: self.on_rename_object(item))

    def on_rename_object(self, item: CustomTreeWidgetItem):
        value = self.lineEdit.text()
        if value != '':
            self.parent().on_rename_object(item=item, value=value, popup=self)
        else:
            MessageInfo('Переименование объекта', 'Поле не может быть пустым')
