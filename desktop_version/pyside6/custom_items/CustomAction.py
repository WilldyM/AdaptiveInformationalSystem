from PySide6.QtGui import *


class CustomAction(QAction):

    def __init__(self, text: str, _id: str = None, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self._id = str(_id)

    def set_id(self, _id: str):
        self._id = str(_id)

    def get_id(self):
        return self._id
