import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.TupleService import BackendTuple
from model_srv.mongodb.TuplePartService import BackendTuplePart

from desktop_version.pyside6.model_form.ui_model_form import Ui_ModelForm
from desktop_version.pyside6.model_form.model_tree_service.model_tree_service import ModelTreeService
from desktop_version.pyside6.model_form.tuple_tree_service.tuple_tree_service import TupleTreeService

from desktop_version.pyside6.messages.messagebox import MessageError, MessageInfo

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem

from desktop_version.pyside6.popups.mt_model_load import MtModelLoad
from desktop_version.pyside6.popups.mt_model_create import MtModelCreate
from desktop_version.pyside6.popups.popup_object_create import PopupObjectCreate
from desktop_version.pyside6.popups.popup_object_rename import PopupObjectRename
from desktop_version.pyside6.popups.popup_tuple_create import PopupTupleCreate


class ModelForm(QWidget, Ui_ModelForm):
    user = None
    mongo_conn = None
    active_model = None

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_ui()
        # init default schema
        self.init_model_tree_root_items()

    def setup_ui(self):
        self.setupUi(self)
        self.setLayout(self.verticalLayout)
        self.modelTreeManagement.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tupleTreeManagement.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # connects TreeWidgets
        self.modelTreeManagement.itemDoubleClicked.connect(self.model_tree_double_clicked_change)
        self.tupleTreeManagement.itemDoubleClicked.connect(self.tuple_tree_double_clicked_change)
        self.modelTreeManagement.setContextMenuPolicy(Qt.CustomContextMenu)
        self.modelTreeManagement.customContextMenuRequested.connect(self.show_mt_objects_context_menu)

        self.header_label = QLabel()
        self.header_enabled = False

    def create_menu_bar(self):
        menu_bar = QMenuBar(self.parent())
        menu = QMenu(self.parent())
        menu.setTitle('Создать')
        create_object_action = QAction('Создать объект', self.parent())
        create_tuple_action = QAction('Создать кортеж', self.parent())
        menu.addActions([create_object_action, create_tuple_action])
        menu_bar.addMenu(menu)

        self.parent().setMenuBar(menu_bar)

        # connects
        create_object_action.triggered.connect(self.on_create_object_action)
        create_tuple_action.triggered.connect(self.on_create_tuple_action)

    # USING TupleTreeService
    def init_tuple_tree_root_items(self, tuples=None):
        TupleTreeService.init_tuple_tree_root_items(self, tuples)

    def on_create_tuple_action(self):
        TupleTreeService.on_create_tuple_action(self)

    def on_create_tuple(self, value, popup: PopupTupleCreate):
        TupleTreeService.on_create_tuple(self, value, popup)

    def tuple_tree_double_clicked_change(self):
        TupleTreeService.tuple_tree_double_clicked_change(self)

    def processing_child_tt_tuple(self, child: CustomTreeWidgetItem):
        TupleTreeService.processing_child_tt_tuple(self, child)

    # USING ModelTreeService
    def init_model_tree_root_items(self, c_objects=None):
        ModelTreeService.init_model_tree_root_items(self, c_objects=c_objects)

    # USING MtModelService
    def set_active_model(self, model_id, model_name):
        ModelTreeService.set_active_model(self, model_id, model_name)

    def update_model(self, bk_model: BackendModel):
        ModelTreeService.update_model(self, bk_model)

    def model_tree_double_clicked_change(self):
        ModelTreeService.model_tree_double_clicked_change(self)

    def processing_child_mt_model(self, child: CustomTreeWidgetItem):
        ModelTreeService.processing_child_mt_model(self, child)

    def mt_model_create_popup(self):
        ModelTreeService.mt_model_create_popup(self)

    def on_create_model(self, value, mt_md_cr_p):
        ModelTreeService.on_create_model(self, value, mt_md_cr_p)

    def mt_model_load_popup(self):
        ModelTreeService.mt_model_load_popup(self)

    def on_load_model(self, list_item: CustomListWidgetItem, mt_md_load_p: MtModelLoad):
        ModelTreeService.on_load_model(self, list_item, mt_md_load_p)

    def on_delete_model(self, list_item: CustomListWidgetItem, mt_md_load_p: MtModelLoad):
        ModelTreeService.on_delete_model(self, list_item, mt_md_load_p)

    # USING ModelTreeService.MtObjectsService
    def show_mt_objects_context_menu(self, position):
        ModelTreeService.show_mt_objects_context_menu(self, position)

    def on_delete_object(self):
        ModelTreeService.on_delete_object(self)

    def on_rename_object_action(self):
        ModelTreeService.on_rename_object_action(self)

    def on_rename_object(self, item: CustomTreeWidgetItem, value: str, popup: PopupObjectRename):
        ModelTreeService.on_rename_object(self, item, value, popup)

    def on_create_object_action(self):
        ModelTreeService.on_create_object_action(self)

    def on_create_object(self, list_item: CustomListWidgetItem, popup: PopupObjectCreate):
        ModelTreeService.on_create_object(self, list_item, popup)

    def processing_child_mt_objects(self, child: CustomTreeWidgetItem):
        ModelTreeService.processing_child_mt_objects(self, child)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ModelForm()
    form.show()
    sys.exit(app.exec())
