from PySide6.QtWidgets import *


class CustomTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent=None, _id=None, type_item=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.type_item = type_item
        self.possible_values = None
        self._id = self._id = str(_id) if _id else None

    def set_id(self, _id: str):
        self._id = str(_id)

    def get_id(self):
        return self._id

    @staticmethod
    def get_item_by_id(item, _id):
        """
        Рекурсивная функция для поиска элемента в дереве по его тексту
        """
        try:
            if item.get_id() == _id:
                return item
        except AttributeError:
            pass
        for i in range(item.childCount()):
            child = item.child(i)
            found = CustomTreeWidgetItem.get_item_by_id(child, _id)
            if found:
                return found
        return None

    @staticmethod
    def get_top_level_parent(item):
        if item.parent() is None:
            return item
        else:
            return item.get_top_level_parent(item.parent())

    @staticmethod
    def get_struct(item, previous=None):
        if previous is None:
            previous = {}
        if item.parent() is None:
            if item.get_id() is None:
                return previous
            elif item.get_id() == 'Параметры':
                return {'tree_struct': {item.get_id(): previous}}
            return {item.get_id(): previous}
        else:
            if item.get_id() is None:
                return item.get_struct(item.parent(), previous)
            elif item.get_id() == 'Параметры':
                return item.get_struct(item.parent(), {'tree_struct': {item.get_id(): previous}})
            return item.get_struct(item.parent(), {item.get_id(): previous})

    def is_top_level(self):
        if self.parent() is None:
            return True
        return False
