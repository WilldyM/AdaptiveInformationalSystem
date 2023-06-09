import sys
from typing import List

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from components.Pandas.custom_forms.popups.ui_on_expression_add_value import Ui_OnExpressionAddValue
from desktop_version.pyside6.messages.messagebox import MessageError


class PopupOnExpressionAddValue(QDialog, Ui_OnExpressionAddValue):

    def __init__(self, parent=None, item=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.item = item
        self.setupUi(self)
        self.lineEdit.setPlaceholderText('Значение')
        self.pushButton.clicked.connect(self.proceed_action)

    def proceed_action(self):
        adf = self.parent().main_object

        struct = CustomTreeWidgetItem.get_struct(self.item)
        current_operand = self.parent().operands_tree.currentItem()
        if current_operand.type_item == 'table_id':
            struct = {'tables': {current_operand.get_id(): {'expression': struct}}}
        elif current_operand.type_item == 'col_id':
            struct = {
                'tables': {
                    current_operand.parent().get_id(): {
                        'fields': {
                            current_operand.get_id(): {
                                'expression': struct
                            }
                        }
                    }
                }
            }
        else:
            return
        value = self.lineEdit.text()
        try:
            res = adf.add_value_to_expression(struct, value)
        except Exception as err:
            MessageError('Добавление значения', f'Unhandled error\nTraceback:\n{err}')
            return
        self.parent().options['operands'] = res['operands']
        self.parent().fill_operands()
        self.close()
