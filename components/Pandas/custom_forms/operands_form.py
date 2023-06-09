import sys

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from components.Pandas.custom_forms.popups.on_create_field import PopupCreateField
from components.Pandas.custom_forms.popups.on_create_table import PopupCreateTable
from components.Pandas.custom_forms.popups.on_expression_add_field import PopupOnExpressionAddField
from components.Pandas.custom_forms.popups.on_expression_add_function import PopupOnExpressionAddFunction
from components.Pandas.custom_forms.popups.on_expression_add_table import PopupOnExpressionAddTable
from components.Pandas.custom_forms.popups.on_expression_add_value import PopupOnExpressionAddValue
from components.Pandas.custom_forms.popups.on_rename_field import PopupRenameField
from components.Pandas.custom_forms.popups.on_rename_table import PopupRenameTable
from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from model_srv.BaseComponent.BaseForms.extract_form import ExtractForm


class OperandsForm(QDialog):

    def __init__(self, parent=None, main_object=None, options: dict = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_object = main_object
        self.options = options
        self.setup_ui()

    def setup_widget(self):
        self.fill_operands()
        self.fill_functions()

    def setup_ui(self):
        font_style = 'font-size: 15px; color: #444444;'

        self.resize(800, 600)
        self.setWindowTitle('Управление данными')
        self.setLayout(QHBoxLayout())

        operands_layout = QVBoxLayout()
        operands_layout.setContentsMargins(1, 1, 0, 0)
        operands_label = QLabel()
        operands_label.setText('Операнды')
        operands_label.setStyleSheet(font_style)
        operands_label.setFixedHeight(20)
        self.operands_tree = QTreeWidget()
        self.operands_tree.setHeaderHidden(True)
        operands_layout.insertWidget(0, operands_label, alignment=Qt.AlignmentFlag.AlignCenter)
        operands_layout.insertWidget(1, self.operands_tree)

        functions_layout = QVBoxLayout()
        functions_layout.setContentsMargins(1, 0, 0, 1)
        functions_label = QLabel()
        functions_label.setText('Функции')
        functions_label.setStyleSheet(font_style)
        functions_label.setFixedHeight(20)
        self.functions_tree = QTreeWidget()
        self.functions_tree.setHeaderHidden(True)
        functions_layout.insertWidget(0, functions_label, alignment=Qt.AlignmentFlag.AlignCenter)
        functions_layout.insertWidget(1, self.functions_tree)

        operands_functions_layout = QVBoxLayout()
        operands_functions_layout.setContentsMargins(0, 0, 3, 0)
        operands_functions_layout.insertLayout(0, operands_layout)
        operands_functions_layout.insertLayout(1, functions_layout)

        expression_layout = QVBoxLayout()
        expression_layout.setContentsMargins(3, 1, 1, 1)
        expression_label = QLabel()
        expression_label.setText('Выражение')
        expression_label.setStyleSheet(font_style)
        expression_label.setFixedHeight(20)
        self.expression_tree = QTreeWidget()
        self.expression_tree.setHeaderHidden(True)
        expression_layout.insertWidget(0, expression_label, alignment=Qt.AlignmentFlag.AlignCenter)
        expression_layout.insertWidget(1, self.expression_tree)

        splitter = QSplitter()
        left_widgets = QWidget()
        left_widgets.setLayout(operands_functions_layout)
        right_widgets = QWidget()
        right_widgets.setLayout(expression_layout)
        splitter.addWidget(left_widgets)
        splitter.addWidget(right_widgets)

        # Устанавливаем ширину разделителя
        splitter.setHandleWidth(2)

        # Получаем объект разделителя и устанавливаем цвет черты
        handle = splitter.handle(1)
        handle.setStyleSheet("background-color: gray;")

        self.layout().addWidget(splitter)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.operands_tree.itemClicked.connect(lambda item: self.update_expression(self.operands_tree.currentItem()))
        self.functions_tree.itemDoubleClicked.connect(lambda item: self.add_function_to_root_expression(self.functions_tree.currentItem()))

        self.operands_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.operands_tree.customContextMenuRequested.connect(self.show_operand_context)

        self.functions_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.functions_tree.customContextMenuRequested.connect(self.show_function_context)

        self.expression_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.expression_tree.customContextMenuRequested.connect(self.show_expression_context)

        self.fill_operands()
        self.fill_functions()

    def show_expression_context(self, position):
        current_item: CustomTreeWidgetItem = self.expression_tree.currentItem()
        actions = list()
        if current_item:
            if current_item.type_item == 'param_label' and isinstance(current_item.possible_values, dict):
                if current_item.possible_values.get('Таблица'):
                    display_action1 = QAction('Добавить таблицу')
                    display_action1.triggered.connect(lambda: self.on_expression_add_table(self.expression_tree.currentItem()))
                    actions.append(display_action1)

                if current_item.possible_values.get('Поле'):
                    display_action2 = QAction('Добавить столбец')
                    display_action2.triggered.connect(lambda: self.on_expression_add_field(self.expression_tree.currentItem()))
                    actions.append(display_action2)

                if current_item.possible_values.get('Функция'):
                    display_action3 = QAction('Добавить функцию')
                    display_action3.triggered.connect(lambda: self.on_expression_add_function(self.expression_tree.currentItem()))
                    actions.append(display_action3)

                if current_item.possible_values.get('Значение', None) is not None:
                    display_action4 = QAction('Добавить значение')
                    display_action4.triggered.connect(lambda: self.on_expression_add_value(self.expression_tree.currentItem()))
                    actions.append(display_action4)
            elif current_item.type_item in ['col_label', 'table_label', 'value_label', 'func_label']:
                display_action4 = QAction('Удалить из выражения')
                display_action4.triggered.connect(lambda: self.on_expression_remove_label(self.expression_tree.currentItem()))
                actions.append(display_action4)
            if not actions:
                return
            menu = QMenu(self.expression_tree)
            menu.addActions(actions)
            menu.exec(self.expression_tree.mapToGlobal(position))

    def show_function_context(self, position):
        current_item: CustomTreeWidgetItem = self.functions_tree.currentItem()
        if current_item.type_item == 'func_id':
            display_action1 = QAction('Добавить в выражение')
            current_operand: CustomTreeWidgetItem = self.operands_tree.currentItem()
            display_action1.triggered.connect(lambda: self.add_function_to_root_expression(self.operands_tree.currentItem()))
            menu = QMenu(self.functions_tree)
            menu.addAction(display_action1)
            menu.exec(self.functions_tree.mapToGlobal(position))

    def show_operand_context(self, position):
        current_item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        actions = list()
        if current_item.type_item == 'root_operand':
            display_action1 = QAction('Добавить таблицу')
            display_action1.triggered.connect(self.on_create_table)
            actions.append(display_action1)
        elif current_item.type_item == 'table_id':
            display_action3 = QAction('Обновить')
            display_action3.triggered.connect(self.on_refresh_table)
            actions.append(display_action3)

            display_action1 = QAction('Добавить столбец')
            display_action1.triggered.connect(self.on_create_field)
            actions.append(display_action1)

            display_action2 = QAction('Переименовать')
            display_action2.triggered.connect(self.on_rename_table)
            actions.append(display_action2)

            display_action5 = QAction('Отобразить таблицу')
            display_action5.triggered.connect(self.on_rename_table)
            actions.append(display_action5)

            if self.options['operands']['tables'][current_item.get_id()]['is_in'] is False:
                display_action4 = QAction('Удалить')
                display_action4.triggered.connect(self.on_remove_table)
                actions.append(display_action4)
        elif current_item.type_item == 'col_id':
            display_action1 = QAction('Переименовать')
            display_action1.triggered.connect(self.on_rename_field)
            actions.append(display_action1)

            parent_id = current_item.parent().get_id()
            if self.options['operands']['tables'][parent_id]['fields'][current_item.get_id()]['is_in'] is False:
                display_action2 = QAction('Удалить')
                display_action2.triggered.connect(self.on_remove_field)
                actions.append(display_action2)

        menu = QMenu(self.operands_tree)
        menu.addActions(actions)
        menu.exec(self.operands_tree.mapToGlobal(position))

    def on_expression_remove_label(self, item):
        print(item.get_id())
        if item.parent().get_id is None or item.parent().type_item in ['root_table_label', 'root_column_label']:
            is_piece_of_values = False
        else:
            is_piece_of_values = True

        struct = CustomTreeWidgetItem.get_struct(item.parent())
        current_operand = self.operands_tree.currentItem()
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
            res = self.main_object.remove_from_struct(struct, item.get_id(), is_piece_of_values=is_piece_of_values)
        except Exception as err:
            MessageError('ADF', f'Unhandled error\nTraceback:{err}')
            return
        self.options['operands'] = res['operands']
        self.fill_operands(current_operand)

    def on_expression_add_field(self, item):
        _form = PopupOnExpressionAddField(self, item)
        _form.show()

    def on_expression_add_function(self, item):
        _form = PopupOnExpressionAddFunction(self, item)
        _form.show()

    def on_expression_add_table(self, item):
        _form = PopupOnExpressionAddTable(self, item)
        _form.show()

    def on_expression_add_value(self, item):
        _form = PopupOnExpressionAddValue(self, item)
        _form.show()

    def on_refresh_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        res = self.main_object.refresh_data(None, item.get_id())
        table_data = {item.text(0): {'columns': res['columns'], 'data': res['data']}}
        self.options['operands'] = res['operands']
        self.fill_operands()
        new_item = CustomTreeWidgetItem.get_item_by_id(self.operands_tree.invisibleRootItem(), item.get_id())
        if new_item:
            self.operands_tree.setCurrentItem(new_item)
            self.update_expression(new_item)
        _form = ExtractForm(self, None, table_data)
        _form.show()

    def on_create_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        popup = PopupCreateTable(self)
        popup.show()

    def on_rename_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        popup = PopupRenameTable(self, item)
        popup.show()

    def on_remove_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        struct = {'tables': {}}
        res = self.main_object.remove_from_struct(struct, item.get_id(), is_piece_of_values=False)
        MessageInfo('Удаление таблицы', f'Таблица {item.text(0)} успешно удалена')
        self.options['operands'] = res['operands']
        self.fill_operands()

    def on_create_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        popup = PopupCreateField(self, item)
        popup.show()

    def on_rename_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        popup = PopupRenameField(self, item)
        popup.show()

    def on_remove_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())
        struct = {'tables': {item.parent().get_id(): {'fields': {}}}}
        res = self.main_object.remove_from_struct(struct, item.get_id(), is_piece_of_values=False)
        MessageInfo('Удаление столбца', f'Столбец {item.text(0)} успешно удалён')
        self.options['operands'] = res['operands']
        self.fill_operands()

    def add_function_to_root_expression(self, item: CustomTreeWidgetItem):
        if item.type_item == 'func_id':
            print(item.get_id())

            operand_item: CustomTreeWidgetItem = self.operands_tree.currentItem()
            func_name = item.get_id()
            if operand_item.type_item == 'table_id':
                res = self.main_object.add_function_to_table(operand_item.get_id(), func_name)
                self.options['operands'] = res['operands']
            elif operand_item.type_item == 'col_id':
                struct = {
                    'tables': {
                        operand_item.parent().get_id(): {
                            'fields': {
                                operand_item.get_id(): {
                                    'expression': {}
                                }
                            }
                        }
                    }
                }
                res = self.main_object.add_function_to_expression(struct, func_name)
                self.options['operands'] = res['operands']
            else:
                MessageInfo('Добавление фукнции', 'Для добавления функции необходимо \nвыбрать таблицу или столбец')
                return
            self.fill_operands()

    def fill_operands(self, item: CustomTreeWidgetItem = None):
        self.operands_tree.clear()
        root_operand = CustomTreeWidgetItem(self.operands_tree, _id='root_operand', type_item='root_operand')
        root_operand.setText(0, 'Таблицы')
        root_operand.setExpanded(True)
        for table_id, table_opt in self.options['operands']['tables'].items():
            table_id_item = CustomTreeWidgetItem(root_operand, _id=table_id, type_item='table_id')
            table_id_item.setText(0, table_opt['display_name'])
            for col_id, col_opt in table_opt['fields'].items():
                col_id_item = CustomTreeWidgetItem(table_id_item, _id=col_id, type_item='col_id')
                col_id_item.setText(0, col_opt['display_name'])

        if item:
            new_item = CustomTreeWidgetItem.get_item_by_id(self.operands_tree.invisibleRootItem(), item.get_id())
            if new_item:
                self.operands_tree.setCurrentItem(new_item)
                self.update_expression(new_item)

    def fill_functions(self):
        self.functions_tree.clear()
        for func_type, func_tree in self.options['functions'].items():
            func_type_item = CustomTreeWidgetItem(self.functions_tree, _id=func_type, type_item='func_type')
            func_type_item.setText(0, func_type)
            for func_id, func_opt in func_tree.items():
                func_id_item = CustomTreeWidgetItem(func_type_item, _id=func_id, type_item='func_id')
                func_id_item.setText(0, func_id)

    def update_expression(self, item: CustomTreeWidgetItem):
        self.expression_tree.clear()
        try:
            if item.type_item == 'table_id':
                label_item = CustomTreeWidgetItem(self.expression_tree, _id=None, type_item='root_table_label')
                expression = self.options['operands']['tables'][item.get_id()]['expression']
            else:
                label_item = CustomTreeWidgetItem(self.expression_tree, _id=None, type_item='root_column_label')
                parent_id = item.parent().get_id()
                expression = self.options['operands']['tables'][parent_id]['fields'][item.get_id()]['expression']
            label_item.setText(0, item.text(0))
            self.fill_expression(label_item, expression)
            label_item.setExpanded(True)
        except Exception as err:
            print(err)

    @staticmethod
    def fill_expression(parent, expression):
        for item, item_prop in expression.items():
            if item_prop['type'] == 'Поле':
                OperandsForm.build_field_tree(parent, item_prop)
            elif item_prop['type'] == 'Таблица':
                OperandsForm.build_table_tree(parent, item_prop)
            elif item_prop['type'] == 'Значение':
                OperandsForm.build_value_tree(parent, item_prop)
            elif item_prop['type'] == 'Функция':
                OperandsForm.build_func_tree(parent, item, item_prop)

    @staticmethod
    def build_field_tree(parent, item_prop):
        col_label = CustomTreeWidgetItem(parent, _id=item_prop['self_name'], type_item='col_label')
        col_label.setText(0, item_prop['display_name'])

    @staticmethod
    def build_table_tree(parent, item_prop):
        table_label = CustomTreeWidgetItem(parent, _id=item_prop['self_name'], type_item='table_label')
        table_label.setText(0, item_prop['display_name'])

    @staticmethod
    def build_value_tree(parent, item_prop):
        value_label = CustomTreeWidgetItem(parent, _id=item_prop['self_name'], type_item='value_label')
        value_label.setText(0, item_prop['display_name'])
        _val = CustomTreeWidgetItem(value_label, _id='value', type_item='_val')
        _val.setText(0, 'value')
        _true_value = list(item_prop['tree_struct']['value'].values())[0]['self_name']
        true_value = CustomTreeWidgetItem(_val, _id=_true_value, type_item='true_value')
        true_value.setText(0, str(_true_value))

    @staticmethod
    def build_func_tree(parent, func_name, func_prop):
        func_label = CustomTreeWidgetItem(parent, _id=func_name, type_item='func_label')
        func_label.setText(0, func_name)
        parameters_label = CustomTreeWidgetItem(func_label, _id='Параметры', type_item='parameters_label')
        parameters_label.setText(0, 'Параметры')
        for param, param_prop in func_prop['tree_struct']['Параметры'].items():
            param_label = CustomTreeWidgetItem(parameters_label, _id=param, type_item='param_label')
            param_label.setText(0, f'[+] {param}')
            param_label.possible_values = param_prop['__possible_values__']
            OperandsForm.fill_expression(param_label, param_prop['values'])

