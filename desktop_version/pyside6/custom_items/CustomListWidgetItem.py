from PySide6.QtWidgets import *


class CustomListWidgetItem(QListWidgetItem):

    def __init__(self, icon=None, _id=None, *args, **kwargs):
        super().__init__(icon, *args, **kwargs)
        self._id = _id

    def set_id(self, _id):
        self._id = _id

    def get_id(self):
        return self._id
