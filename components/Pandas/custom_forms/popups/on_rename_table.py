import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from components.Pandas.custom_forms.popups.ui_on_rename_table import Ui_OnRenameTable


class PopupRenameTable(QDialog, Ui_OnRenameTable):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Наименование таблицы')
        self.pushButton.clicked.connect(self.proceed_action)

    def proceed_action(self):
        value = self.lineEdit.text()
        self.parent().on_create_tuple(value, self)