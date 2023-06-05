import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem
from desktop_version.pyside6.custom_items.CustomTabWidget import TabWidget


class PopupObjectCreate(QDialog):

    def __init__(self, parent=None, items=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi()
        if items:
            self.set_categories_parts(items)

    def setupUi(self):
        self.resize(400, 300)
        self.setWindowTitle('Создание объекта')
        self.setLayout(QVBoxLayout(self))
        self.tabWidget = TabWidget(self)
        self.button_ok = QPushButton('Создать', self)
        self.button_close = QPushButton('Отмена', self)
        buttons_layout = QHBoxLayout(self)
        buttons_layout.insertWidget(0, self.button_ok)
        buttons_layout.insertWidget(1, self.button_close)
        buttons_layout_widget = QWidget(self)
        buttons_layout_widget.setLayout(buttons_layout)

        self.layout().insertWidget(0, self.tabWidget)
        self.layout().insertWidget(1, buttons_layout_widget)

        self.button_ok.clicked.connect(self.on_create_object_from_button)
        self.button_close.clicked.connect(self.close)

    def set_categories_parts(self, bk_cat):
        all_part_of = {i['part_of']: [] for i in bk_cat}
        for cat in bk_cat:
            all_part_of[cat['part_of']].append({'_id': cat['_id'], 'display_name': cat['display_name']})

        for part_of, categories in all_part_of.items():
            listWidget = QListWidget()
            self.fill_list_widget(listWidget, categories)
            self.tabWidget.addTab(listWidget, part_of)
            listWidget.itemDoubleClicked.connect(self.on_create_object_from_button)
            # listWidget.itemDoubleClicked.connect(lambda lwItem: self.on_create_object_from_lw(lwItem))

    def fill_list_widget(self, list_widget, items):
        for item in items:
            clw_item = CustomListWidgetItem(_id=str(item['_id']))
            clw_item.setText(item['display_name'])
            list_widget.addItem(clw_item)

    # def on_create_object_from_lw(self, list_item: CustomListWidgetItem):
    #     self.parent().on_create_object(list_item, self)

    def on_create_object_from_button(self):
        list_widget = self.tabWidget.currentWidget()
        list_item: CustomListWidgetItem = list_widget.currentItem()
        self.parent().on_create_object(list_item, self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = PopupObjectCreate()
    form.show()
    sys.exit(app.exec())
