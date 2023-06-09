import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from components.Pandas.custom_forms.popups.ui_on_rename_field import Ui_OnRenameField
from desktop_version.pyside6.messages.messagebox import MessageError


class PopupRenameField(QDialog, Ui_OnRenameField):

    def __init__(self, parent=None, item=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.item = item
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Наименование столбца')
        self.pushButton.clicked.connect(self.proceed_action)

    def proceed_action(self):
        value = self.lineEdit.text()
        adf = self.parent().main_object
        try:
            new_operands = adf.edit_field_name(self.item.parent().get_id(), self.item.get_id(), value)['operands']
        except Exception as err:
            MessageError('Переименование столбца', f'Unhandled error\nTraceback:\n{err}')
            return
        self.parent().options['operands'] = new_operands
        self.parent().fill_operands()
        self.close()
