import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomAction import CustomAction
from desktop_version.pyside6.popups.popup_group_rename import PopupGroupRename
from desktop_version.pyside6.popups.popup_tuple_part_rename import PopupTuplePartRename
from desktop_version.pyside6.popups.popup_tuple_part_set_c_object import PopupTuplePartSetCObject
from desktop_version.pyside6.popups.popup_tuple_rename import PopupTupleRename
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

    def closing_qdialog(self, qdialog):
        # for widget in self.children():
        #     if widget is qdialog:
        #         widget.reject()
        pass

    def setup_ui(self):
        self.setupUi(self)
        self.setLayout(self.verticalLayout)
        self.setStyleSheet('''
        QPushButton {
            margin-left: 2px;
            margin-right: 2px;
        }
        ''')
        # self.modelTreeManagement.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.tupleTreeManagement.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # connects TreeWidgets
        self.modelTreeManagement.itemDoubleClicked.connect(self.model_tree_double_clicked_change)
        self.modelTreeManagement.setFocusPolicy(Qt.NoFocus)

        # custom context menu mt
        self.modelTreeManagement.setContextMenuPolicy(Qt.CustomContextMenu)
        self.modelTreeManagement.customContextMenuRequested.connect(self.show_mt_objects_context_menu)

        # custom context menu tt
        self.tupleTreeManagement.setFocusPolicy(Qt.NoFocus)
        self.tupleTreeManagement.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tupleTreeManagement.customContextMenuRequested.connect(self.show_tt_tuple_context_menu)
        self.tupleTreeManagement.setColumnCount(2)
        self.tupleTreeManagement.headerItem().setText(1, 'Тип данных')
        self.tupleTreeManagement.setColumnWidth(0, 400)

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
    def show_tt_tuple_context_menu(self, position):
        TupleTreeService.show_tt_tuple_context_menu(self, position)

    def init_tuple_tree_root_items(self, tuples=None):
        TupleTreeService.init_tuple_tree_root_items(self, tuples)

    def on_create_group(self):
        TupleTreeService.on_create_group(self)

    def on_create_inner_tuple(self):
        TupleTreeService.on_create_inner_tuple(self)

    def processing_form(self, custom_action: CustomAction, current_item: CustomTreeWidgetItem):
        TupleTreeService.processing_form(self, custom_action, current_item)

    def on_rename_group_action(self):
        TupleTreeService.on_rename_group_action(self)

    def on_rename_group(self, item: CustomTreeWidgetItem, value: str, popup: PopupGroupRename):
        TupleTreeService.on_rename_group(self, item, value, popup)

    def on_remove_group(self):
        TupleTreeService.on_remove_group(self)

    # USING TupleTreeService::TupleService
    def on_create_tuple_action(self):
        TupleTreeService.on_create_tuple_action(self)

    def on_create_tuple(self, value, popup: PopupTupleCreate):
        TupleTreeService.on_create_tuple(self, value, popup)

    def on_remove_tuple(self):
        TupleTreeService.on_remove_tuple(self)

    def on_rename_tuple_action(self):
        TupleTreeService.on_rename_tuple_action(self)

    def on_rename_tuple(self, item: CustomTreeWidgetItem, value: str, popup: PopupTupleRename):
        TupleTreeService.on_rename_tuple(self, item, value, popup)

    # USING TupleTreeService::TuplePartService
    def on_remove_tuple_part(self):
        TupleTreeService.on_remove_tuple_part(self)

    def on_create_tuple_part(self):
        TupleTreeService.on_create_tuple_part(self)

    def set_c_object_action(self):
        TupleTreeService.set_c_object_action(self)

    def set_c_object(self, item: CustomTreeWidgetItem, c_object: BackendCObject, popup: PopupTuplePartSetCObject):
        TupleTreeService.set_c_object(self, item, c_object, popup)

    def on_rename_tuple_part_action(self):
        TupleTreeService.on_rename_tuple_part_action(self)

    def on_rename_tuple_part(self, item: CustomTreeWidgetItem, value: str, popup: PopupTuplePartRename):
        TupleTreeService.on_rename_tuple_part(self, item, value, popup)

    # USING ModelTreeService
    def init_model_tree_root_items(self, c_objects=None):
        ModelTreeService.init_model_tree_root_items(self, c_objects=c_objects)

    # USING ModelTreeService::MtModelService
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

    # USING ModelTreeService::MtObjectsService
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
