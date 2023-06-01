import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem
from desktop_version.pyside6.popups.mt_model_load import MtModelLoad
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.TupleService import BackendTuple
from model_srv.mongodb.TuplePartService import BackendTuplePart

from desktop_version.pyside6.model_form.ui_model_form import Ui_ModelForm
from desktop_version.pyside6.messages.messagebox import MessageError, MessageInfo
from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.popups.mt_model_create import MtModelCreate


class ModelForm(QWidget, Ui_ModelForm):
    user = None
    mongo_conn = None
    active_model = None

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.setLayout(self.horizontalLayout)

        # init deafult schema
        self.init_model_tree_root_items()

        # connects modelTreeManagement
        self.modelTreeManagement.itemDoubleClicked.connect(self.model_tree_double_clicked_change)

    def init_model_tree_root_items(self):
        modelItem = CustomTreeWidgetItem(self.modelTreeManagement, _id='mt_model')
        modelItem.setText(0, 'Модель')

        createModelItem = CustomTreeWidgetItem(modelItem, _id='mt_model_create')
        createModelItem.setText(0, 'Создать')
        loadModelItem = CustomTreeWidgetItem(modelItem, _id='mt_model_load')
        loadModelItem.setText(0, 'Загрузить')

        objectsItem = CustomTreeWidgetItem(self.modelTreeManagement, _id='mt_objects')
        objectsItem.setText(0, 'Объекты')

    def model_tree_double_clicked_change(self):
        selected_item: CustomTreeWidgetItem = self.modelTreeManagement.currentItem()
        if selected_item.is_top_level():
            return
        if CustomTreeWidgetItem.get_top_level_parent(selected_item).get_id() == 'mt_model':
            self.processing_child_mt_model(selected_item)
        elif CustomTreeWidgetItem.get_top_level_parent(selected_item).get_id() == 'mt_objects':
            self.processing_child_mt_objects(selected_item)

    def processing_child_mt_model(self, child: CustomTreeWidgetItem):
        print('Selected item on Models:', child.text(0))
        if child.get_id() == 'mt_model_create':
            self.mt_model_create_popup()
        elif child.get_id() == 'mt_model_load':
            self.mt_model_load_popup()

    def mt_model_create_popup(self):
        mt_md_cr_p = MtModelCreate(self)
        mt_md_cr_p.show()

    def on_create_model(self, value, mt_md_cr_p):
        bk_model = BackendModel(self.user['login'], value)
        new_id_model = bk_model.insert_model()
        if new_id_model:
            mt_md_cr_p.close()
            self.set_active_model(new_id_model, value)
        else:
            MessageError('Создание модели', 'Ошибка при создании модели')

    def mt_model_load_popup(self):
        models_lst = BackendModel.get_all_models({'owner': self.user['login']})
        if not models_lst:
            MessageInfo('Загрузка модели', 'У Вас нет существующих моделей')
            return
        mt_md_load_p = MtModelLoad(self, items=models_lst)
        mt_md_load_p.show()

    def on_load_model(self, list_item: CustomListWidgetItem, mt_md_load_p: MtModelLoad):
        bk_model: BackendModel = BackendModel.init_from_mongo(list_item.get_id())
        if bk_model:
            mt_md_load_p.close()
            self.set_active_model(bk_model._id, bk_model.display_name)
        else:
            MessageError('Загрузка модели', 'Ошибка при загрузке модели')

    def set_active_model(self, model_id, model_name):
        self.active_model = str(model_id)
        self.parent().setWindowTitle(f'AdaptiveIS.ModelManagement - {model_name}')
        print('Active_model:', self.active_model)

    def processing_child_mt_objects(self, child: CustomTreeWidgetItem):
        print('Selected item on Objects:', child.text(0))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ModelForm()
    form.show()
    sys.exit(app.exec())
