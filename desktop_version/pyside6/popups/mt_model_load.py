import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem
from desktop_version.pyside6.popups.ui_mt_model_load import Ui_MtModelLoad


class MtModelLoad(QDialog, Ui_MtModelLoad):

    def __init__(self, parent=None, items=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle('Загрузка модели')
        self.setLayout(self.verticalLayout)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.listWidget.itemDoubleClicked.connect(self.on_load_model)
        self.pushButton.clicked.connect(self.on_load_model)
        self.pushButton_3.clicked.connect(self.on_rename_model)
        self.pushButton_4.clicked.connect(self.on_delete_model)
        if items is not None:
            self.fill_list_widget(items)

    def fill_list_widget(self, items):
        for item in items:
            clw_item = CustomListWidgetItem(_id=str(item['_id']))
            clw_item.setText(item['display_name'])
            self.listWidget.addItem(clw_item)

    def on_load_model(self):
        listItem: CustomListWidgetItem = self.listWidget.currentItem()
        self.parent().on_load_model(listItem, self)

    def on_delete_model(self):
        listItem: CustomListWidgetItem = self.listWidget.currentItem()
        self.parent().on_delete_model(listItem, self)

    def on_rename_model(self):
        listItem: CustomListWidgetItem = self.listWidget.currentItem()
        self.parent().on_rename_model(listItem, self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = MtModelLoad()
    form.show()
    sys.exit(app.exec())
