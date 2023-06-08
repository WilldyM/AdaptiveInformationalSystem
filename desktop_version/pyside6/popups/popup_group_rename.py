import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo
from desktop_version.pyside6.popups.ui_tt_group_rename import Ui_TtGroupRename


class PopupGroupRename(QDialog, Ui_TtGroupRename):

    def __init__(self, parent, item: CustomTreeWidgetItem, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.item = item
        self.lineEdit.setPlaceholderText('Наименование группы')
        self.pushButton.clicked.connect(self.on_rename_group)

    def on_rename_group(self):
        value = self.lineEdit.text()
        if value != '':
            self.parent().on_rename_group(item=self.item, value=value, popup=self)
        else:
            MessageInfo('Переименование группы', 'Поле не может быть пустым')
