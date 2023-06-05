import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem
from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from desktop_version.pyside6.popups.mt_model_create import MtModelCreate
from desktop_version.pyside6.popups.mt_model_load import MtModelLoad
from model_srv.mongodb.ModelService import BackendModel


class MtModelService(object):

    @staticmethod
    def set_active_model(model_form, model_id, model_name):
        model_form.active_model = str(model_id)
        model_form.parent().setWindowTitle(f'AdaptiveIS.ModelManagement - {model_name}')

        model_form.header_label.setText(model_name)
        if not model_form.header_enabled:
            model_form.verticalLayout.insertWidget(0, model_form.header_label, alignment=Qt.AlignmentFlag.AlignCenter)
            model_form.header_label.setFixedHeight(30)
            model_form.header_label.setStyleSheet('font-size: 20px;')
            model_form.header_enabled = True

        model_form.create_menu_bar()
        print('Active_model:', model_form.active_model)

    @staticmethod
    def update_model(model_form, bk_model: BackendModel):
        model_metadata = bk_model.get_model_metadata()
        model_form.modelTreeManagement.clear()
        model_form.tupleTreeManagement.clear()
        model_form.init_model_tree_root_items(c_objects=model_metadata['c_objects'])
        model_form.init_tuple_tree_root_items(tuples=model_metadata['tuples'])

    @staticmethod
    def model_tree_double_clicked_change(model_form):
        selected_item: CustomTreeWidgetItem = model_form.modelTreeManagement.currentItem()
        if selected_item.is_top_level():
            return
        if CustomTreeWidgetItem.get_top_level_parent(selected_item).get_id() == 'mt_model':
            model_form.processing_child_mt_model(selected_item)
        elif CustomTreeWidgetItem.get_top_level_parent(selected_item).get_id() == 'mt_objects' and \
                selected_item.type_item == 'c_object':
            model_form.processing_child_mt_objects(selected_item)

    @staticmethod
    def processing_child_mt_model(model_form, child: CustomTreeWidgetItem):
        print('Selected item on Models:', child.text(0))
        if child.get_id() == 'mt_model_create':
            model_form.mt_model_create_popup()
        elif child.get_id() == 'mt_model_load':
            model_form.mt_model_load_popup()

    @staticmethod
    def mt_model_create_popup(model_form):
        mt_md_cr_p = MtModelCreate(model_form)
        mt_md_cr_p.show()

    @staticmethod
    def on_create_model(model_form, value, mt_md_cr_p):
        bk_model = BackendModel(model_form.user['login'], value)
        new_id_model = bk_model.insert_model()
        if new_id_model:
            MessageInfo('Создание модели', f'Модель {value} успешно создана')
            mt_md_cr_p.close()
            model_form.set_active_model(new_id_model, value)
            model_form.update_model(bk_model)
        else:
            MessageError('Создание модели', 'Ошибка при создании модели')

    @staticmethod
    def mt_model_load_popup(model_form):
        models_lst = BackendModel.get_all_models({'owner': model_form.user['login']})
        if not models_lst:
            MessageInfo('Загрузка модели', 'У Вас нет существующих моделей')
            return
        mt_md_load_p = MtModelLoad(model_form, items=models_lst)
        mt_md_load_p.show()

    @staticmethod
    def on_load_model(model_form, list_item: CustomListWidgetItem, mt_md_load_p: MtModelLoad):
        bk_model: BackendModel = BackendModel.init_from_mongo(list_item.get_id())
        if bk_model:
            mt_md_load_p.close()
            model_form.set_active_model(bk_model._id, bk_model.display_name)
            model_form.update_model(bk_model)
        else:
            MessageError('Загрузка модели', 'Ошибка при загрузке модели')

    @staticmethod
    def on_delete_model(model_form, list_item: CustomListWidgetItem, mt_md_load_p: MtModelLoad):
        bk_model: BackendModel = BackendModel.init_from_mongo(list_item.get_id())
        if bk_model:
            is_deleted = bk_model.delete_model(cascade=True)
            if is_deleted:
                MessageInfo('Удаление модели', f'Модель {bk_model.display_name} удалена')
            else:
                MessageError('Удаление модели', 'Ошибка при удалении модели')
        else:
            MessageError('Удаление модели', 'Модель не найдена')
        mt_md_load_p.listWidget.clear()
        items = BackendModel.get_all_models({'owner': model_form.user['login']})
        mt_md_load_p.fill_list_widget(items)