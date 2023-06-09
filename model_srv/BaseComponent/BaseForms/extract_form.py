import sys
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTableViewService import CustomTableView
from model_srv.mongodb.ModelService import BackendModel


class ExtractForm(QDialog):

    def __init__(self, parent, main_object, tables: dict, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle('Загрузка данных')
        self.main_object = main_object
        self.tables = tables
        self.setup_ui()

    def setup_widget(self):
        self.tabWidget.clear()
        self.fill_tab_widget()

    def setup_ui(self):
        self.resize(800, 600)
        self.setLayout(QVBoxLayout())

        self.tabWidget = QTabWidget()
        self.fill_tab_widget()

        self.layout().addWidget(self.tabWidget)

    def fill_tab_widget(self):
        for table_name, table_prop in self.tables.items():
            table_view = CustomTableView(table_prop['data'], table_prop['columns'])
            self.tabWidget.addTab(table_view, table_name)

