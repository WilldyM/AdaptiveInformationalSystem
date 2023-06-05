from PySide6.QtWidgets import *


class CustomTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent=None, _id=None, type_item=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.type_item = type_item
        self._id = _id

    def set_id(self, _id):
        self._id = _id

    def get_id(self):
        return self._id

    @staticmethod
    def get_top_level_parent(item):
        if item.parent() is None:
            return item
        else:
            return item.get_top_level_parent(item.parent())

    def is_top_level(self):
        if self.parent() is None:
            return True
        return False
