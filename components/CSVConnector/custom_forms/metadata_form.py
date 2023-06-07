import sys
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from model_srv.BaseComponent.BaseForms.metadata_form import MetadataForm


class CSVMetadataForm(MetadataForm):

    def __init__(self, parent, main_object, metadata: list, *args, **kwargs):
        super().__init__(parent, main_object, metadata, *args, **kwargs)
