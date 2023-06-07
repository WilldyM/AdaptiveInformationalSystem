import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from bson import ObjectId

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from desktop_version.pyside6.popups.popup_object_rename import PopupObjectRename
from desktop_version.pyside6.popups.popup_tuple_create import PopupTupleCreate
from desktop_version.pyside6.popups.popup_tuple_rename import PopupTupleRename
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.TupleService import BackendTuple


class TupleService(object):

    @staticmethod
    def on_create_tuple_action(model_form):
        print('Creating tuple')
        popup = PopupTupleCreate(model_form)
        popup.show()

    @staticmethod
    def on_remove_tuple(model_form):
        bk_tuple_id = model_form.tupleTreeManagement.currentItem().get_id()
        bk_tuple = BackendTuple.init_from_mongo(bk_tuple_id)
        bk_tuple.delete_object(cascade=True)

        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        if bk_model.remove_tuple(bk_tuple):
            MessageInfo('Удаление кортежа', f'Кортеж "{bk_tuple.display_name}" удалён')
        else:
            MessageError('Удаление кортежа', f'Не удалось удалить кортеж')
        bk_model.update_model()
        model_form.update_model(bk_model)

    @staticmethod
    def on_rename_tuple_action(model_form):
        print('Renaming tuple')
        popup = PopupTupleRename(model_form, item=model_form.tupleTreeManagement.currentItem())
        popup.show()

    @staticmethod
    def on_rename_tuple(model_form, item: CustomTreeWidgetItem, value: str, popup: PopupTupleRename):
        try:
            old_value = ''.join(item.text(0).split(' (')[:-1])
            obj_id = item.get_id()
            bk_obj = BackendTuple.init_from_mongo(obj_id)
            bk_obj.display_name = value
            bk_obj.update_object()
        except Exception as err:
            MessageError('Переименование кортежа', f'Unhandled Error:\nTraceback: {err}')
        else:
            MessageInfo('Переименование кортежа', f'"{old_value}" -> "{value}"')
        finally:
            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            model_form.update_model(bk_model)
            popup.close()

    @staticmethod
    def on_create_tuple(model_form, value, popup: PopupTupleCreate):
        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        bk_tuple = BackendTuple(value, model_form.active_model)
        new_id_tuple = bk_tuple.insert_object()
        if new_id_tuple:
            MessageInfo('Создание кортежа', f'Кортеж "{value}" успешно создан')
            popup.close()
            bk_model.add_tuple(bk_tuple)
            bk_model.update_model()
            model_form.update_model(bk_model)
        else:
            MessageError('Создание кортежа', 'Ошибка при создании кортежа')

