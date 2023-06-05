from typing import List

from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError
from desktop_version.pyside6.popups.popup_tuple_create import PopupTupleCreate
from model_srv.mongodb.ModelService import BackendModel
from model_srv.mongodb.TupleService import BackendTuple


class TupleTreeService(object):

    @staticmethod
    def init_tuple_tree_root_items(model_form, tuples: List[BackendTuple] = None):
        if not tuples:
            return
        for t in tuples:
            tuple_item = CustomTreeWidgetItem(model_form.tupleTreeManagement, _id=t._id, type_item='tt_tuple')
            tuple_item.setText(0, f'[{t.display_name}] {"()" if not t.tuple_parts else ""}')

    @staticmethod
    def on_create_tuple_action(model_form):
        print('Creating tuple')
        popup = PopupTupleCreate(model_form)
        popup.show()

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

    @staticmethod
    def tuple_tree_double_clicked_change(model_form):
        selected_item: CustomTreeWidgetItem = model_form.tupleTreeManagement.currentItem()
        if selected_item.is_top_level():
            return
        if CustomTreeWidgetItem.get_top_level_parent(selected_item).get_id() == 'mt_model':
            model_form.processing_child_mt_model(selected_item)

    @staticmethod
    def processing_child_tt_tuple(model_form, child: CustomTreeWidgetItem):
        print('Selected item on tt_tuple:', child.text(0))

