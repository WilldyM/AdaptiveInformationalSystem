import sys
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from model_srv.BaseComponent.BaseForms.init_form import InitForm
from model_srv.mongodb.ModelService import BackendModel


class SQLInitForm(InitForm):

    def __init__(self, parent_widget, main_object, *args, **kwargs):
        super().__init__(parent_widget, main_object, *args, **kwargs)
        self.setWindowTitle('Форма подключения')


