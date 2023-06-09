import sys
from typing import List

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from components.Pandas.custom_forms.popups.ui_on_expression_add_function import Ui_OnExpressionAddFunction
from desktop_version.pyside6.messages.messagebox import MessageError


class PopupOnExpressionAddFunction(QDialog, Ui_OnExpressionAddFunction):

    def __init__(self, parent, item: CustomTreeWidgetItem, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.item = item
        self.temp_values = list(item.possible_values['Функция'].keys())
        self.comboBox.addItems(self.temp_values)
        self.pushButton_3.clicked.connect(self.set_object)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


    def set_object(self):
        adf = self.parent().main_object

        func_name = self.comboBox.currentText()
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
        try:
            res = adf.add_function_to_expression(struct, func_name)
        except Exception as err:
            MessageError('Добавление функции', f'Unhandled error\nTraceback:\n{err}')
            return

        self.parent().options['operands'] = res['operands']
        self.parent().fill_operands(item=self.parent().operands_tree.currentItem())
        self.close()
