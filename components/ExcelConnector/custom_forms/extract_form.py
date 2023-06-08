import sys
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from model_srv.BaseComponent.BaseForms.extract_form import ExtractForm
from model_srv.mongodb.ModelService import BackendModel


class ExcelExtractForm(ExtractForm):

    def __init__(self, parent, main_object, tables: dict, *args, **kwargs):
        super().__init__(parent, main_object, tables, *args, **kwargs)