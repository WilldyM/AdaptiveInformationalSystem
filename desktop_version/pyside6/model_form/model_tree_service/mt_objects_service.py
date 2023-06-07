from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.custom_items.CustomListWidgetItem import CustomListWidgetItem
from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageError, MessageInfo
from desktop_version.pyside6.popups.popup_object_create import PopupObjectCreate
from desktop_version.pyside6.popups.popup_object_rename import PopupObjectRename
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.TuplePartService import BackendTuplePart


class MtObjectsService(object):

    @staticmethod
    def show_mt_objects_context_menu(model_form, position):
        current_item: CustomTreeWidgetItem = model_form.modelTreeManagement.currentItem()
        if current_item.get_id() == 'mt_objects':
            display_action1 = QAction('Создать объект')
            display_action1.triggered.connect(model_form.on_create_object_action)
            menu = QMenu(model_form.modelTreeManagement)
            menu.addAction(display_action1)

            menu.exec_(model_form.modelTreeManagement.mapToGlobal(position))
        elif CustomTreeWidgetItem.get_top_level_parent(current_item).get_id() == 'mt_objects' and \
                current_item.is_top_level() is False and current_item.type_item == 'c_object':
            remove_action = QAction('Удалить объект')
            remove_action.triggered.connect(model_form.on_delete_object)
            rename_action = QAction('Переименовать объект')
            rename_action.triggered.connect(model_form.on_rename_object_action)
            menu = QMenu(model_form.modelTreeManagement)
            menu.addActions([remove_action, rename_action])

            menu.exec_(model_form.modelTreeManagement.mapToGlobal(position))

    @staticmethod
    def on_rename_object_action(model_form):
        print('Renaming object')
        popup = PopupObjectRename(model_form, item=model_form.modelTreeManagement.currentItem())
        popup.show()

    @staticmethod
    def on_rename_object(model_form, item: CustomTreeWidgetItem, value: str, popup: PopupObjectRename):
        try:
            old_value = item.text(0)
            obj_id = item.get_id()
            bk_obj = BackendCObject.init_from_mongo(obj_id)
            bk_obj.display_name = value
            bk_obj.update_object()
        except Exception as err:
            MessageError('Переимнование объекта', f'Unhandled Error:\nTraceback: {err}')
        else:
            MessageInfo('Переимнование объекта', f'"{old_value}" -> "{value}"')
        finally:
            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            model_form.update_model(bk_model)
            popup.close()

    @staticmethod
    def on_delete_object(model_form):
        try:
            obj_id = model_form.modelTreeManagement.currentItem().get_id()
            bk_obj = BackendCObject.init_from_mongo(obj_id)

            bk_tuple_parts = BackendTuplePart.get_all_tuple_parts(model_id=bk_obj.model)
            for bk_tp in bk_tuple_parts:
                if str(bk_tp.c_object) == str(bk_obj._id):
                    bk_tp.c_object = None
                    bk_tp.update_object()

            bk_obj.delete_object()

            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            bk_model.c_objects.remove(str(obj_id))
            bk_model.update_model()
            model_form.update_model(bk_model)
        except Exception as err:
            MessageError('Удаление объекта', f'Unhandled Error:\nTraceback: {err}')
        else:
            MessageInfo('Удаление объекта', f'Объект "{bk_obj.display_name}" удалён')

    @staticmethod
    def on_create_object_action(model_form):
        print('Creating object')
        bk_cat = BackendCategory.get_all_categories()
        mt_md_cr_p = PopupObjectCreate(model_form, items=bk_cat)
        mt_md_cr_p.show()

    @staticmethod
    def on_create_object(model_form, list_item: CustomListWidgetItem, popup: PopupObjectCreate):
        print('category_id: ', list_item.get_id())
        try:
            bk_model: BackendModel = BackendModel.init_from_mongo(model_form.active_model)

            dn = BackendCObject.get_unique_name(bk_model._id, list_item.text())
            bk_object = BackendCObject(display_name=dn, model=model_form.active_model,
                                       category=list_item.get_id())
            bk_object_id = bk_object.insert_object()
            is_added = bk_model.add_c_object(bk_object_id)
            bk_model.update_model()
            model_form.update_model(bk_model)
        except Exception as err:
            MessageError('Создание объекта', f'Создать объект не удалось\nTraceback:\n{err}')
        else:
            MessageInfo('Создание объекта', f'Объект {dn} успешно создан')
        finally:
            popup.close()

    @staticmethod
    def processing_child_mt_objects(model_form, child: CustomTreeWidgetItem):
        print('Selected item on Objects:', child.text(0))
