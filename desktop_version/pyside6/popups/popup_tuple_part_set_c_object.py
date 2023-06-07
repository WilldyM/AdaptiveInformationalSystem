import sys
from typing import List

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo
from desktop_version.pyside6.popups.ui_tt_tuple_part_set_c_object import Ui_TtTuplePartSetCObject
from model_srv.mongodb.CObjectService import BackendCObject


class PopupTuplePartSetCObject(QDialog, Ui_TtTuplePartSetCObject):

    def __init__(self, parent, item: CustomTreeWidgetItem, combo_box_items: List[BackendCObject], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.item = item
        self.c_objects = combo_box_items
        self.comboBox.addItems([obj.display_name for obj in combo_box_items])
        self.pushButton_3.clicked.connect(self.set_c_object)

    def set_c_object(self):
        c_object_index = self.comboBox.currentIndex()
        c_object = self.c_objects[c_object_index]
        self.parent().set_c_object(item=self.item, c_object=c_object, popup=self)
