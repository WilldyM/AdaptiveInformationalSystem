from PySide6.QtWidgets import *


class CustomListWidgetItem(QListWidgetItem):

    def __init__(self, icon=None, _id=None, *args, **kwargs):
        super().__init__(icon, *args, **kwargs)
        self._id = str(_id) if _id else None

    def set_id(self, _id: str):
        self._id = str(_id)

    def get_id(self):
        return self._id
