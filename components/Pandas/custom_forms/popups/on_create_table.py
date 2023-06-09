import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from components.Pandas.custom_forms.popups.ui_on_create_table import Ui_OnCreateTable
from desktop_version.pyside6.messages.messagebox import MessageError


class PopupCreateTable(QDialog, Ui_OnCreateTable):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Наименование таблицы')
        self.pushButton.clicked.connect(self.proceed_action)

    def proceed_action(self):
        value = self.lineEdit.text()
        adf = self.parent().main_object
        try:
            new_operands = adf.add_new_table(value)['operands']
        except Exception as err:
            MessageError('Добавление таблицы', f'Unhandled error\nTraceback:\n{err}')
            return
        self.parent().options['operands'] = new_operands
        self.parent().fill_operands()
        self.close()
