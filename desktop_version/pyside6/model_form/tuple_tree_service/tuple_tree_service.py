import json
import time
from typing import List
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from bson import ObjectId

from desktop_version.pyside6.custom_items.CustomAction import CustomAction
from desktop_version.pyside6.custom_items.CustomAnimation import ArcWidget
from desktop_version.pyside6.model_form.tuple_tree_service.tuple_part_service import TuplePartService
from desktop_version.pyside6.model_form.tuple_tree_service.tuple_service import TupleService

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from desktop_version.pyside6.popups.popup_group_rename import PopupGroupRename
from desktop_version.pyside6.popups.popup_tuple_create import PopupTupleCreate
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.GroupService import BackendGroup
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.TuplePartService import BackendTuplePart
from model_srv.mongodb.TupleService import BackendTuple


class TupleTreeService(TupleService, TuplePartService):

    @staticmethod
    def processing_form(model_form, custom_action: CustomAction, current_item: CustomTreeWidgetItem):
        print('processing form')
        parent_item: CustomTreeWidgetItem = current_item.parent()
        if parent_item.type_item == 'tt_tuple' or parent_item.type_item == 'tt_group':
            bk_group = None
            present_index_from_group = False
            if parent_item.type_item == 'tt_group':
                bk_group: BackendGroup = BackendGroup.init_from_mongo(parent_item.get_id())
                parent_item = parent_item.parent()
                present_index_from_group = True
            bk_tuple: BackendTuple = BackendTuple.init_from_mongo(parent_item.get_id())
            main_bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(current_item.get_id())

            if present_index_from_group:
                present_tuple_part_index = bk_tuple.tuple_parts.index([str(bk_group._id)])
            else:
                present_tuple_part_index = bk_tuple.tuple_parts.index(str(main_bk_tuple_part._id))
            previous = None
            _bk_tuple_part = None
            for operand in bk_tuple.tuple_parts[:present_tuple_part_index]:
                try:
                    if isinstance(operand, str):  # проверка на обычный TuplePart
                        _bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(operand)
                        _bk_object = _bk_tuple_part.get_c_object()
                        previous = _bk_object.get_projection(previous)
                    elif isinstance(operand, tuple):  # проверка на вложенный кортеж
                        pass
                    elif isinstance(operand, list):  # проверка на группировку
                        _bk_group = BackendGroup.init_from_mongo(operand[0])
                        _previous = list()
                        for _tp in _bk_group.tuple_parts:
                            _bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(_tp)
                            _bk_object = _bk_tuple_part.get_c_object()
                            _previous.append(_bk_object.get_projection(previous))
                        previous = _previous
                except Exception as err:
                    if isinstance(_bk_tuple_part, BackendTuplePart):
                        dn = _bk_tuple_part.display_name
                    else:
                        dn = current_item.text(0)
                    err_text = f'Ошибка при выполнении {dn}\nTraceback:\n{err}'
                    MessageError('Ошибка выполнения части кортежа', err_text)
            # предполагается что здесь обрабатывается последний TuplePart
            if present_index_from_group:
                present_tuple_part_index = bk_group.tuple_parts.index(str(main_bk_tuple_part._id))
                for operand in bk_group.tuple_parts[:present_tuple_part_index]:
                    try:
                        _bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(operand)
                        _bk_object = _bk_tuple_part.get_c_object()
                        _bk_object.get_projection(previous)
                    except Exception as err:
                        if isinstance(_bk_tuple_part, BackendTuplePart):
                            dn = _bk_tuple_part.display_name
                        else:
                            dn = current_item.text(0)
                        err_text = f'Ошибка при выполнении {dn}\nTraceback:\n{err}'
                        MessageError('Ошибка выполнения части кортежа', err_text)
                main_bk_object = main_bk_tuple_part.get_c_object()
                main_bk_object.call_form(model_form, custom_action._id, previous=previous)
            else:
                main_bk_object = main_bk_tuple_part.get_c_object()
                main_bk_object.call_form(model_form, custom_action._id, previous=previous)

    @staticmethod
    def show_tt_tuple_context_menu(model_form, position):
        current_item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        menu = QMenu(model_form.tupleTreeManagement)
        actions = list()
        if current_item.type_item == 'tt_tuple':
            add_operand = QAction('Добавить операнд')
            add_operand.triggered.connect(model_form.on_create_tuple_part)
            actions.append(add_operand)

            add_grouping = QAction('Добавить группу')
            add_grouping.triggered.connect(model_form.on_create_group)
            actions.append(add_grouping)

            add_inner_tuple = QAction('Добавить существующий кортеж')
            add_inner_tuple.triggered.connect(model_form.on_create_inner_tuple)  # todo
            actions.append(add_inner_tuple)

            rename_tuple = QAction('Переименовать кортеж')
            rename_tuple.triggered.connect(model_form.on_rename_tuple_action)
            actions.append(rename_tuple)

            remove_tuple = QAction('Удалить кортеж')
            remove_tuple.triggered.connect(model_form.on_remove_tuple)
            actions.append(remove_tuple)

        elif current_item.type_item == 'tt_tuple_part':
            # bk_tuple: BackendTuple = BackendTuple.init_from_mongo(current_item.parent().get_id())
            bk_tuple_part: BackendTuplePart = BackendTuplePart.init_from_mongo(current_item.get_id())
            if bk_tuple_part.c_object:
                bk_c_object = BackendCObject.init_from_mongo(bk_tuple_part.c_object)
                # form_views = QAction('Формы')
                sub_menu = menu.addMenu('Формы')
                sub_actions = list()
                for form_id, form_prop in bk_c_object.forms.items():
                    form_action = CustomAction(form_prop['form_name'], _id=form_id)
                    form_action.triggered.connect(partial(model_form.processing_form, form_action, current_item))
                    sub_actions.append(form_action)
                sub_menu.addActions(sub_actions)

            set_c_object = QAction('Установить объект')
            set_c_object.triggered.connect(model_form.set_c_object_action)
            actions.append(set_c_object)

            rename_tuple_part = QAction('Переименовать операнд')
            rename_tuple_part.triggered.connect(model_form.on_rename_tuple_part_action)
            actions.append(rename_tuple_part)

            remove_tuple_part = QAction('Удалить операнд')
            remove_tuple_part.triggered.connect(model_form.on_remove_tuple_part)
            actions.append(remove_tuple_part)
        elif current_item.type_item == 'tt_group':
            add_operand = QAction('Добавить операнд')
            add_operand.triggered.connect(model_form.on_create_tuple_part)
            actions.append(add_operand)

            add_inner_tuple = QAction('Добавить существующий кортеж')
            add_inner_tuple.triggered.connect(model_form.on_create_inner_tuple)
            actions.append(add_inner_tuple)

            rename_group = QAction('Переименовать группу')
            rename_group.triggered.connect(model_form.on_rename_group_action)
            actions.append(rename_group)

            remove_group = QAction('Удалить группу')
            remove_group.triggered.connect(model_form.on_remove_group)
            actions.append(remove_group)
        else:
            return

        menu.addActions(actions)
        menu.exec(model_form.tupleTreeManagement.mapToGlobal(position))

    @staticmethod
    def init_tuple_tree_root_items(model_form, tuples: List[BackendTuple] = None):
        if not tuples:
            return
        for bk_tuple in tuples:
            tuple_item = CustomTreeWidgetItem(model_form.tupleTreeManagement, _id=bk_tuple._id, type_item='tt_tuple')
            tuple_item.setText(0, f'{bk_tuple.display_name}')
            tuple_item.setText(1, '[Кортеж]')
            metadata_tuple_parts = list()
            for tp_id in bk_tuple.tuple_parts:
                if isinstance(tp_id, (str, ObjectId)):
                    metadata_tuple_parts.append(TupleTreeService._show_tuple_part(tuple_item, tp_id))
                elif isinstance(tp_id, list):
                    metadata_tuple_parts.append(TupleTreeService._show_grouping(tuple_item, tp_id))
                elif isinstance(tp_id, tuple):
                    metadata_tuple_parts.append(TupleTreeService._show_inner_tuple(tuple_item, tp_id))

            if metadata_tuple_parts:
                perspective_lst = list()
                for obj in metadata_tuple_parts:
                    if isinstance(obj, BackendTuplePart):
                        perspective_lst.append(obj.display_name)
                    elif isinstance(obj, BackendGroup):
                        bg_lst = list()
                        for tp in obj.tuple_parts:
                            _bk_tp = BackendTuplePart.init_from_mongo(tp)
                            bg_lst.append(_bk_tp.display_name)
                        perspective_lst.append(json.dumps(bg_lst, ensure_ascii=False))
                    elif isinstance(obj, BackendTuple):
                        t_lst = list()
                        for tp in obj.tuple_parts:
                            _bk_tp = BackendTuplePart.init_from_mongo(tp)
                            t_lst.append(_bk_tp.display_name)
                        t_lst = tuple(t_lst)
                        perspective_lst.append(json.dumps(t_lst))

                perspective = '->'.join(perspective_lst) + '->'
                tuple_item.setText(0, f'{bk_tuple.display_name} ({perspective})')

    @staticmethod
    def _show_tuple_part(parent, tp_id):
        try:
            bk_tuple_part = BackendTuplePart.init_from_mongo(tp_id)
        except Exception as err:
            print(err)
            if parent.type_item == 'tt_group':
                bk_group = BackendGroup.init_from_mongo(parent.get_id())
                bk_group.remove_tuple_part(tp_id)
                bk_group.update_object()
            return
        tuple_part_item = CustomTreeWidgetItem(parent, _id=tp_id, type_item='tt_tuple_part')
        tuple_part_item.setText(0, bk_tuple_part.display_name)
        tuple_part_item.setText(1, '[Операнд]')
        bk_c_object = bk_tuple_part.get_c_object()
        if bk_c_object is not None:
            TupleTreeService._show_c_object_from_tuple_part(tuple_part_item, bk_c_object)
        return bk_tuple_part

    @staticmethod
    def _show_c_object_from_tuple_part(parent, bk_c_object: BackendCObject):
        wrapper_item = CustomTreeWidgetItem(parent, _id=parent, type_item='tt_wrapper_c_object')
        wrapper_item.setText(0, 'Объект')
        obj_item = CustomTreeWidgetItem(wrapper_item, _id=bk_c_object._id, type_item='tt_c_object')
        obj_item.setText(0, bk_c_object.display_name)
        bk_category = bk_c_object.get_bk_category()
        obj_item.setText(1, f'[{bk_category.display_name}]')

    @staticmethod
    def _show_inner_tuple(parent, inner_tuple: tuple):
        pass  # todo

    @staticmethod
    def on_create_inner_tuple(model_form):
        pass

    @staticmethod
    def _show_grouping(parent, group: list):
        group_id = group[0]
        bk_group = BackendGroup.init_from_mongo(group_id)
        group_item = CustomTreeWidgetItem(parent, _id=group_id, type_item='tt_group')
        group_item.setText(0, bk_group.display_name)
        group_item.setText(1, '[Группа]')
        for tp_id in bk_group.tuple_parts:
            TupleTreeService._show_tuple_part(group_item, tp_id)
        return bk_group

    @staticmethod
    def on_create_group(model_form):
        tuple_item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        bk_tuple = BackendTuple.init_from_mongo(tuple_item.get_id())
        unique_dn = BackendGroup.get_unique_name(model_form.active_model, 'Группа')
        bk_group = BackendGroup(display_name=unique_dn, model=model_form.active_model)
        bk_group.insert_object()

        bk_tuple.add_tuple_part([str(bk_group._id)])
        bk_tuple.update_object()
        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        model_form.update_model(bk_model)

    @staticmethod
    def on_rename_group_action(model_form):
        print('Renaming group')
        popup = PopupGroupRename(model_form, item=model_form.tupleTreeManagement.currentItem())
        popup.show()

    @staticmethod
    def on_rename_group(model_form, item: CustomTreeWidgetItem, value: str, popup: PopupGroupRename):
        try:
            old_value = item.text(0)
            obj_id = item.get_id()
            bk_obj = BackendGroup.init_from_mongo(obj_id)
            bk_obj.display_name = value
            bk_obj.update_object()
        except Exception as err:
            MessageError('Переименование группы', f'Unhandled Error:\nTraceback: {err}')
        else:
            MessageInfo('Переименование группы', f'"{old_value}" -> "{value}"')
        finally:
            bk_model = BackendModel.init_from_mongo(model_form.active_model)
            model_form.update_model(bk_model)
            popup.close()

    @staticmethod
    def on_remove_group(model_form):
        item = model_form.tupleTreeManagement.currentItem()
        bk_group_id = item.get_id()
        bk_group = BackendGroup.init_from_mongo(bk_group_id)
        bk_group.delete_object(cascade=True)

        bk_model = BackendModel.init_from_mongo(model_form.active_model)
        bk_tuple = BackendTuple.init_from_mongo(item.parent().get_id())
        bk_tuple.remove_group(bk_group)
        bk_tuple.update_object()
        MessageInfo('Удаление группы', f'Кортеж "{bk_group.display_name}" удалён')
        bk_model.update_model()
        model_form.update_model(bk_model)
