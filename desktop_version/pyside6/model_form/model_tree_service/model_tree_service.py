from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem

from desktop_version.pyside6.model_form.model_tree_service.mt_model_service import MtModelService
from desktop_version.pyside6.model_form.model_tree_service.mt_objects_service import MtObjectsService


class ModelTreeService(MtModelService, MtObjectsService):

    @staticmethod
    def init_model_tree_root_items(model_form, c_objects=None):
        modelItem = CustomTreeWidgetItem(model_form.modelTreeManagement, _id='mt_model')
        modelItem.setText(0, 'Модель')

        createModelItem = CustomTreeWidgetItem(modelItem, _id='mt_model_create')
        createModelItem.setText(0, 'Создать')
        loadModelItem = CustomTreeWidgetItem(modelItem, _id='mt_model_load')
        loadModelItem.setText(0, 'Загрузить')

        objectsItem = CustomTreeWidgetItem(model_form.modelTreeManagement, _id='mt_objects')
        objectsItem.setText(0, 'Объекты')

        if c_objects:
            used_categories = dict()
            for c_obj in c_objects:
                bk_cat = c_obj.get_bk_category()
                catItem = used_categories.get(bk_cat._id)
                if not catItem:
                    catItem = CustomTreeWidgetItem(objectsItem, _id=bk_cat._id, type_item='category')
                    catItem.setText(0, f'[{bk_cat.display_name}]')
                    used_categories[bk_cat._id] = catItem

                obj_item = CustomTreeWidgetItem(catItem, _id=c_obj._id, type_item='c_object')
                obj_item.setText(0, c_obj.display_name)
