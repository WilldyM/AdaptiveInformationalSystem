import sys

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem


class OperandsForm(QDialog):

    def __init__(self, parent=None, main_object=None, options: dict = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_object = main_object
        self.options = options
        self.setup_ui()

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

        self.operands_tree.itemClicked.connect(lambda item: self.update_expression(item))
        self.functions_tree.itemDoubleClicked.connect(lambda item: self.add_function_to_expression(item))

        self.operands_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.operands_tree.customContextMenuRequested.connect(self.show_operand_context)

        self.fill_operands()
        self.fill_functions()

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

    def on_create_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_refresh_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_create_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_rename_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_remove_table(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_rename_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def on_remove_field(self):
        item: CustomTreeWidgetItem = self.operands_tree.currentItem()
        print(item.get_id())

    def fill_operands(self):
        root_operand = CustomTreeWidgetItem(self.operands_tree, _id='root_operand', type_item='root_operand')
        root_operand.setText(0, 'Таблицы')
        root_operand.setExpanded(True)
        for table_id, table_opt in self.options['operands']['tables'].items():
            table_id_item = CustomTreeWidgetItem(root_operand, _id=table_id, type_item='table_id')
            table_id_item.setText(0, table_opt['display_name'])
            for col_id, col_opt in table_opt['fields'].items():
                col_id_item = CustomTreeWidgetItem(table_id_item, _id=col_id, type_item='col_id')
                col_id_item.setText(0, col_opt['display_name'])

    def fill_functions(self):
        for func_type, func_tree in self.options['functions'].items():
            func_type_item = CustomTreeWidgetItem(self.functions_tree, _id=func_type, type_item='func_type')
            func_type_item.setText(0, func_type)
            for func_id, func_opt in func_tree.items():
                func_id_item = CustomTreeWidgetItem(func_type_item, _id=func_id, type_item='func_id')
                func_id_item.setText(0, func_id)

    def update_expression(self, item: CustomTreeWidgetItem):
        self.expression_tree.clear()
        if item.type_item == 'table_id':
            label_item = CustomTreeWidgetItem(self.expression_tree, _id=None, type_item='table_label')
            expression = self.options['operands']['tables'][item.get_id()]['expression']
        else:
            label_item = CustomTreeWidgetItem(self.expression_tree, _id=None, type_item='column_label')
            parent_id = item.parent().get_id()
            expression = self.options['operands']['tables'][parent_id]['fields'][item.get_id()]['expression']
        label_item.setText(0, item.text(0))
        self.fill_expression(label_item, expression)

    def fill_expression(self, parent, expression):
        print(expression)

    def add_function_to_expression(self, item: CustomTreeWidgetItem):
        if item.type_item == 'func_id':
            print(item.get_id())


if __name__ == '__main__':
    import json
    _json = '''
    {
  "operands": {
    "main_mapper": {
      "647fed00ff02460c2b3f2e59": {
        "source_self_name": "647fed00ff02460c2b3f2e59",
        "current_self_name": "Excel_Table_1",
        "fields": {
          "Производственный_цикл": {
            "source_self_name": "Производственный_цикл",
            "current_self_name": "Производственный_цикл",
            "display_name": "Excel_Table_1.Производственный_цикл"
          },
          "Стадия": {
            "source_self_name": "Стадия",
            "current_self_name": "Стадия",
            "display_name": "Excel_Table_1.Стадия"
          },
          "Группа_животных": {
            "source_self_name": "Группа_животных",
            "current_self_name": "Группа_животных",
            "display_name": "Excel_Table_1.Группа_животных"
          },
          "Длительность_стадии": {
            "source_self_name": "Длительность_стадии",
            "current_self_name": "Длительность_стадии",
            "display_name": "Excel_Table_1.Длительность_стадии"
          }
        },
        "display_name": "Excel_Table_1"
      },
      "647ff14dacf26f19a348bf8e": {
        "source_self_name": "647ff14dacf26f19a348bf8e",
        "current_self_name": "Excel_Table_2",
        "fields": {
          "Производственный_цикл_1": {
            "source_self_name": "Производственный_цикл_1",
            "current_self_name": "Производственный_цикл_1",
            "display_name": "Excel_Table_2.Производственный_цикл_1"
          },
          "Стадия_1": {
            "source_self_name": "Стадия_1",
            "current_self_name": "Стадия_1",
            "display_name": "Excel_Table_2.Стадия_1"
          },
          "Группа_животных_1": {
            "source_self_name": "Группа_животных_1",
            "current_self_name": "Группа_животных_1",
            "display_name": "Excel_Table_2.Группа_животных_1"
          },
          "Длительность_стадии_1": {
            "source_self_name": "Длительность_стадии_1",
            "current_self_name": "Длительность_стадии_1",
            "display_name": "Excel_Table_2.Длительность_стадии_1"
          },
          "Процент_осеменения": {
            "source_self_name": "Процент_осеменения",
            "current_self_name": "Процент_осеменения",
            "display_name": "Excel_Table_2.Процент_осеменения"
          },
          "Выход_поросят": {
            "source_self_name": "Выход_поросят",
            "current_self_name": "Выход_поросят",
            "display_name": "Excel_Table_2.Выход_поросят"
          },
          "Вес_поросёнка": {
            "source_self_name": "Вес_поросёнка",
            "current_self_name": "Вес_поросёнка",
            "display_name": "Excel_Table_2.Вес_поросёнка"
          },
          "Процент_оплодотворения": {
            "source_self_name": "Процент_оплодотворения",
            "current_self_name": "Процент_оплодотворения",
            "display_name": "Excel_Table_2.Процент_оплодотворения"
          }
        },
        "display_name": "Excel_Table_2"
      }
    },
    "tables": {
      "Excel_Table_1": {
        "fields": {
          "Производственный_цикл": {
            "self_name": "Производственный_цикл",
            "display_name": "Excel_Table_1.Производственный_цикл",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Стадия": {
            "self_name": "Стадия",
            "display_name": "Excel_Table_1.Стадия",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Группа_животных": {
            "self_name": "Группа_животных",
            "display_name": "Excel_Table_1.Группа_животных",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Длительность_стадии": {
            "self_name": "Длительность_стадии",
            "display_name": "Excel_Table_1.Длительность_стадии",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          }
        },
        "self_name": "Excel_Table_1",
        "display_name": "Excel_Table_1",
        "type": "Таблица",
        "is_in": true,
        "expression": {}
      },
      "Excel_Table_2": {
        "fields": {
          "Производственный_цикл_1": {
            "self_name": "Производственный_цикл_1",
            "display_name": "Excel_Table_2.Производственный_цикл_1",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Стадия_1": {
            "self_name": "Стадия_1",
            "display_name": "Excel_Table_2.Стадия_1",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Группа_животных_1": {
            "self_name": "Группа_животных_1",
            "display_name": "Excel_Table_2.Группа_животных_1",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Длительность_стадии_1": {
            "self_name": "Длительность_стадии_1",
            "display_name": "Excel_Table_2.Длительность_стадии_1",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Процент_осеменения": {
            "self_name": "Процент_осеменения",
            "display_name": "Excel_Table_2.Процент_осеменения",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Выход_поросят": {
            "self_name": "Выход_поросят",
            "display_name": "Excel_Table_2.Выход_поросят",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Вес_поросёнка": {
            "self_name": "Вес_поросёнка",
            "display_name": "Excel_Table_2.Вес_поросёнка",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          },
          "Процент_оплодотворения": {
            "self_name": "Процент_оплодотворения",
            "display_name": "Excel_Table_2.Процент_оплодотворения",
            "type": "Поле",
            "is_in": true,
            "expression": {}
          }
        },
        "self_name": "Excel_Table_2",
        "display_name": "Excel_Table_2",
        "type": "Таблица",
        "is_in": true,
        "expression": {}
      }
    }
  },
  "functions": {
    "Функции_агрегирования": {
      "Медиана": {
        "type": "Функция",
        "backend_method": "_f_agr_median",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Среднее": {
        "type": "Функция",
        "backend_method": "_f_agr_avg",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "АГР_Сумма": {
        "type": "Функция",
        "backend_method": "_f_agr_sum",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Количество": {
        "type": "Функция",
        "backend_method": "_f_agr_count",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Количество_уникальных": {
        "type": "Функция",
        "backend_method": "_f_agr_nunique",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Минимум": {
        "type": "Функция",
        "backend_method": "_f_agr_min",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Максимум": {
        "type": "Функция",
        "backend_method": "_f_agr_max",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Кумулятивная_сумма": {
        "type": "Функция",
        "backend_method": "_f_agr_cumsum",
        "return_type": [
          "Поле",
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Агрегируемый_показатель": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      }
    },
    "Анализ_данных": {
      "Корреляция": {
        "type": "Функция",
        "backend_method": "_f_ad_corr",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица",
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Ранговая_корреляция": {
        "type": "Функция",
        "backend_method": "_f_ad_rang_corr",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Частичная_корреляция": {
        "type": "Функция",
        "backend_method": "_f_ad_partial_corr",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Контролируемая_переменная": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      }
    },
    "Арифметические_операции": {
      "Сумма": {
        "type": "Функция",
        "backend_method": "_f_ao_sum",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Разность": {
        "type": "Функция",
        "backend_method": "_f_ao_difference",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Произведение": {
        "type": "Функция",
        "backend_method": "_f_ao_composition",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Частное": {
        "type": "Функция",
        "backend_method": "_f_ao_quotient",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Неполное_частное": {
        "type": "Функция",
        "backend_method": "_f_ao_partial_quotient",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Остаток_частного": {
        "type": "Функция",
        "backend_method": "_f_ao_remainder_quotient",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Модуль[abs]": {
        "type": "Функция",
        "backend_method": "_f_ao_abs",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Округление": {
        "type": "Функция",
        "backend_method": "_f_ao_round",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      }
    },
    "Преобразование_типов": {
      "int64": {
        "type": "Функция",
        "backend_method": "_f_pt_int64",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "float64": {
        "type": "Функция",
        "backend_method": "_f_pt_float64",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "datetime64[ns]": {
        "type": "Функция",
        "backend_method": "_f_pt_datetime64",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "str": {
        "type": "Функция",
        "backend_method": "_f_pt_str",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      }
    },
    "Логические_операторы": {
      "Оператор_И": {
        "type": "Функция",
        "backend_method": "_f_lo_and",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Функция": {}
              }
            }
          }
        }
      },
      "Оператор_ИЛИ": {
        "type": "Функция",
        "backend_method": "_f_lo_or",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Функция": {}
              }
            }
          }
        }
      }
    },
    "Операторы_сравнения": {
      "[ОД]_Оператор_>": {
        "type": "Функция",
        "backend_method": "_f_os_bolshe",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Оператор_>=": {
        "type": "Функция",
        "backend_method": "_f_os_bolshe_libo_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Оператор_<": {
        "type": "Функция",
        "backend_method": "_f_os_menshe",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Оператор_<=": {
        "type": "Функция",
        "backend_method": "_f_os_menshe_libo_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Оператор_==": {
        "type": "Функция",
        "backend_method": "_f_os_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Оператор_!=": {
        "type": "Функция",
        "backend_method": "_f_os_ne_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "[ОД]_Промежуток": {
        "type": "Функция",
        "backend_method": "_f_os_between",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Начало": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {}
              }
            },
            "Конец": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_>": {
        "type": "Функция",
        "backend_method": "_f_os_bolshe",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_>=": {
        "type": "Функция",
        "backend_method": "_f_os_bolshe_libo_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_<": {
        "type": "Функция",
        "backend_method": "_f_os_menshe",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_<=": {
        "type": "Функция",
        "backend_method": "_f_os_menshe_libo_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_==": {
        "type": "Функция",
        "backend_method": "_f_os_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Оператор_!=": {
        "type": "Функция",
        "backend_method": "_f_os_ne_ravno",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Левый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Правый_операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Промежуток": {
        "type": "Функция",
        "backend_method": "_f_os_between",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Операнд": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            },
            "Начало": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {}
              }
            },
            "Конец": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Значение": {}
              }
            },
            "Если_верно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Если_ложно": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      }
    },
    "Реляционная_алгебра": {
      "Соединение": {
        "type": "Функция",
        "backend_method": "_f_ra_concatenation",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица_1": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Таблица_2": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Объединить_по_столбцу_слева": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Объединить_по_столбцу_справа": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Соединение[LEFT]": {
        "type": "Функция",
        "backend_method": "_f_ra_concatenation_left",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица_1": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Таблица_2": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Объединить_по_столбцу_слева": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Объединить_по_столбцу_справа": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Соединение[RIGHT]": {
        "type": "Функция",
        "backend_method": "_f_ra_concatenation_right",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица_1": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Таблица_2": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Объединить_по_столбцу_слева": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Объединить_по_столбцу_справа": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Соединение[OUTER]": {
        "type": "Функция",
        "backend_method": "_f_ra_concatenation_outer",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица_1": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Таблица_2": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Объединить_по_столбцу_слева": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Объединить_по_столбцу_справа": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Объединение": {
        "type": "Функция",
        "backend_method": "_f_ra_union",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица_1": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Таблица_2": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Объединить_по_столбцу_слева": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Объединить_по_столбцу_справа": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Отбор_данных": {
        "type": "Функция",
        "backend_method": "_f_ra_data_selection",
        "return_type": [
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Функция_сравнения": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Функция": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Сортировка_восходящая": {
        "type": "Функция",
        "backend_method": "_f_ra_sort_increase",
        "return_type": [
          "Поле",
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Сортировка_нисходящая": {
        "type": "Функция",
        "backend_method": "_f_ra_sort_decrease",
        "return_type": [
          "Поле",
          "Таблица"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Измерения": {
              "values": {},
              "if_return_type": [
                "Поле",
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      },
      "Копия": {
        "type": "Функция",
        "backend_method": "_f_ra_copy",
        "return_type": [
          "Таблица",
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Таблица": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Таблица": {},
                "Функция": {}
              }
            },
            "Поле": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            },
            "Результирующие_поля": {
              "values": {},
              "if_return_type": [
                "Таблица"
              ],
              "__possible_values__": {
                "Поле": {}
              }
            }
          }
        }
      }
    },
    "Работа_с_датой": {
      "Начало_дня": {
        "type": "Функция",
        "backend_method": "_f_rsd_start_day",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Начало_недели": {
        "type": "Функция",
        "backend_method": "_f_rsd_start_week",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Начало_месяца": {
        "type": "Функция",
        "backend_method": "_f_rsd_start_month",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Начало_года": {
        "type": "Функция",
        "backend_method": "_f_rsd_start_year",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Сбор_даты_и_времени": {
        "type": "Функция",
        "backend_method": "_f_rsd_set_datetime_from_parts",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Год": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Месяц": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "День": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Час": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Минута": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Секунда": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Сбор_даты": {
        "type": "Функция",
        "backend_method": "_f_rsd_set_date_from_parts",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Год": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "Месяц": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            },
            "День": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {},
                "Значение": {}
              }
            }
          }
        }
      },
      "Получить_Год": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_year_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Получить_Месяц": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_month_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Получить_День": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_day_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Получить_Час": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_hour_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Получить_Минуту": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_minute_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      },
      "Получить_Секунду": {
        "type": "Функция",
        "backend_method": "_f_rsd_get_second_from_date",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Измерение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Поле": {},
                "Функция": {}
              }
            }
          }
        }
      }
    },
    "Прочее": {
      "Значение": {
        "type": "Функция",
        "backend_method": "_f_pr_value",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {
            "Значение": {
              "values": {},
              "if_return_type": [
                "Поле"
              ],
              "__possible_values__": {
                "Значение": {}
              }
            }
          }
        }
      },
      "NaN": {
        "type": "Функция",
        "backend_method": "_f_pr_nan",
        "return_type": [
          "Поле"
        ],
        "tree_struct": {
          "Параметры": {}
        }
      }
    }
  }
}
    '''
    _options = json.loads(_json)

    app = QApplication(sys.argv)
    form = OperandsForm(options=_options)
    form.show()
    sys.exit(app.exec())
