import sys
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from model_srv.mongodb.ModelService import BackendModel


class MetadataForm(QDialog):

    def __init__(self, parent, main_object, metadata: list, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_object = main_object
        self.metadata = metadata
        self.setWindowTitle('Форма выбора метаданных')
        self.setup_ui()

    def setup_ui(self):
        self.resize(800, 600)
        self.setLayout(QVBoxLayout())

        self.treeWidget = QTreeWidget()
        # self.treeWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.treeWidget.setColumnCount(3)
        self.treeWidget.headerItem().setText(0, '#')
        self.treeWidget.headerItem().setText(1, 'ИмяЭлемента')
        self.treeWidget.headerItem().setText(2, 'ТипЭлемента')
        self.treeWidget.itemChanged[CustomTreeWidgetItem, int].connect(self.control_checkState)
        self.fill_metadata(self.treeWidget, self.metadata)

        self.button_ok = QPushButton('Ок')
        self.button_ok.setFixedHeight(30)
        self.button_ok.setFixedWidth(100)
        self.button_ok.clicked.connect(self.save_query_data)
        self.button_close = QPushButton('Отмена')
        self.button_close.setFixedHeight(30)
        self.button_close.setFixedWidth(100)
        self.button_close.clicked.connect(self.close)

        buttons_layout = QHBoxLayout()
        buttons_layout.insertWidget(0, self.button_ok, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        buttons_layout.insertWidget(1, self.button_close, stretch=6, alignment=Qt.AlignmentFlag.AlignLeft)

        self.layout().addWidget(self.treeWidget)
        self.layout().addLayout(buttons_layout)

    @staticmethod
    def control_checkState(item: CustomTreeWidgetItem, column):
        # MetadataForm.set_parent_checkState(item, checked_state=item.checkState(column))
        MetadataForm.set_children_checkState(item, checked_state=item.checkState(column))

    @staticmethod
    def set_parent_checkState(item: CustomTreeWidgetItem, checked_state: Qt.CheckState):
        if item.is_top_level():
            return
        item.parent().setCheckState(0, checked_state)
        MetadataForm.set_parent_checkState(item.parent(), checked_state=checked_state)

    @staticmethod
    def set_children_checkState(item: CustomTreeWidgetItem, checked_state: Qt.CheckState):
        for i in range(item.childCount()):
            item.child(i).setCheckState(0, checked_state)
            MetadataForm.set_children_checkState(item.child(i), checked_state=checked_state)

    def save_query_data(self):
        query_data = self.get_items_checked(self.treeWidget.invisibleRootItem())
        self.main_object.bk_object.properties['q_data']['value'] = query_data
        self.main_object.bk_object.update_object()
        bk_model = BackendModel.init_from_mongo(self.parent().active_model)
        self.parent().update_model(bk_model)
        self.close()

    def get_items_checked(self, parent):
        dct = dict()
        child_count = parent.childCount()
        if child_count == 0:
            return dct
        for i in range(child_count):
            item: CustomTreeWidgetItem = parent.child(i)
            if item.checkState(0) == Qt.Checked:
                dct[item.text(1)] = self.get_items_checked(item)
        return dct

    def fill_metadata(self, parent, metadata):
        for row in metadata:
            name_item = row['ИмяЭлемента']
            type_item = row['ТипЭлемента']
            item = CustomTreeWidgetItem(parent)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            item.setText(1, name_item)
            item.setText(2, type_item)

            next_row = row.get('row')
            if next_row:
                self.fill_metadata(item, next_row)


