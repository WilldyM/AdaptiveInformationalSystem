import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from bson import ObjectId

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from desktop_version.pyside6.popups.popup_tuple_part_rename import PopupTuplePartRename
from desktop_version.pyside6.popups.popup_tuple_part_set_c_object import PopupTuplePartSetCObject
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.GroupService import BackendGroup
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.TuplePartService import BackendTuplePart
from model_srv.mongodb.TupleService import BackendTuple


class TuplePartService(object):

    @staticmethod
    def set_c_object_action(model_form):
        item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        bk_objects = [BackendCObject.init_from_mongo(obj_id) for obj_id in bk_model.c_objects]
        popup = PopupTuplePartSetCObject(model_form, item, combo_box_items=bk_objects)
        popup.show()

    @staticmethod
    def set_c_object(model_form, item: CustomTreeWidgetItem, c_object: BackendCObject, popup: PopupTuplePartSetCObject):
        bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(item.get_id())
        bk_tuple_part.set_c_object(c_object)
        bk_tuple_part.update_object()

        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        model_form.update_model(bk_model)

        popup.close()

    @staticmethod
    def on_rename_tuple_part_action(model_form):
        item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        popup = PopupTuplePartRename(model_form, item)
        popup.show()

    @staticmethod
    def on_rename_tuple_part(model_form, item: CustomTreeWidgetItem, value: str, popup: PopupTuplePartRename):
        try:
            old_value = item.text(0)
            obj_id = item.get_id()
            bk_obj = BackendTuplePart.init_from_mongo(obj_id)
            bk_obj.display_name = value
            bk_obj.update_object()
        except Exception as err:
            MessageError('Переименование операнда', f'Unhandled Error:\nTraceback: {err}')
        else:
            MessageInfo('Переименование операнда', f'"{old_value}" -> "{value}"')
        finally:
            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            model_form.update_model(bk_model)
            popup.close()

    @staticmethod
    def on_create_tuple_part(model_form):
        tuple_item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        try:
            bk_tuple = BackendTuple.init_from_mongo(tuple_item.get_id())
        except Exception as err:
            print(err)
            bk_tuple = BackendGroup.init_from_mongo(tuple_item.get_id())

        unique_dn = BackendTuplePart.get_unique_name(model_id=model_form.active_model, start_value='Операнд')
        bk_tuple_part = BackendTuplePart(unique_dn, model_form.active_model, c_object=None)
        bk_tuple_part_id = bk_tuple_part.insert_object()
        bk_tuple.add_tuple_part(bk_tuple_part_id)
        bk_tuple.update_object()

        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        model_form.update_model(bk_model)

    @staticmethod
    def on_remove_tuple_part(model_form):
        item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        bk_tuple_part_id = item.get_id()
        bk_tuple_part = BackendTuplePart.init_from_mongo(bk_tuple_part_id)
        bk_tuple_part.delete_object()

        bk_tuple: BackendTuple = BackendTuple.init_from_mongo(item.parent().get_id())
        if bk_tuple.remove_tuple_part(bk_tuple_part):
            MessageInfo('Удаление операнда', f'Операнд "{bk_tuple_part.display_name}" удалён')
            bk_tuple.update_object()

            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            model_form.update_model(bk_model)
        else:
            MessageError('Удаление операнда', f'Не удалось удалить операнд')
