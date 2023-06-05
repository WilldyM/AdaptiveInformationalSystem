import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject, BaseBackendObject
from model_srv.mongodb.CategoryService import BackendCategory


class MongoCObject(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.objects_collection))

    def insert_object(self, class_obj: 'BackendCObject', with_id=False):
        obj_dct = class_obj.serialize(with_id=with_id)
        obj_id = self.insert_document(self.db.get_collection(self.objects_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.objects_collection), query, multiple=multiple)
        return obj

    def update_object(self, find_query: dict, set_query: dict, multiple: bool = False):
        if find_query.get('_id'):
            find_query['_id'] = ObjectId(find_query['_id'])
        updated_obj = self.update_document(self.db.get_collection(self.objects_collection),
                                           find_query, set_query, multiple=multiple)
        return updated_obj

    def remove_object(self, query):
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        try:
            self.delete_document(self.db.get_collection(self.objects_collection), query)
        except Exception as err:
            print(err)
            return False
        return True


class BackendCObject(BaseBackendObject):

    def __init__(self, display_name: str, model: Union[str, ObjectId], category: str, _id: str = None):
        super().__init__(display_name, model, _id)
        self.category = category
        self.properties = dict()
        self.forms = dict()
        self.init_category_options()

    @classmethod
    @init_mongo_conn(MongoCObject)
    def get_unique_name(cls, model_id: Union[str, ObjectId], start_value: str):
        if isinstance(model_id, ObjectId):
            model_id = str(model_id)
        created_objects = cls.mongo_conn.find_object(
            {
                'model': str(model_id),
                'display_name': {'$regex': '^' + start_value}
            }
        )
        only_dn = [dn['display_name'] for dn in created_objects]
        end_value = cls.new_name(start_value, only_dn)
        return end_value

    @staticmethod
    def new_name(value, search_lst, i=0):
        start_value = value + '_' + str(i) if i != 0 else value
        end_value = start_value
        if start_value in search_lst:
            i += 1
            end_value = BackendCObject.new_name(value, search_lst, i)
        return end_value

    def get_bk_category(self):
        bk_cat = BackendCategory.init_from_mongo(self.category)
        return bk_cat

    def init_category_options(self):
        bk_cat = self.get_bk_category()
        for t in bk_cat.template:
            self.properties[t['self_name']] = {
                'self_name': t['self_name'],
                'display_name': t['self_name'],
                'value': t['default']
            }
        self.forms = bk_cat.forms

    def serialize(self, with_id=False):
        obj_dct = super().serialize(with_id=with_id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        back_obj = BackendCObject(obj_dct['display_name'], obj_dct['model'],
                                  obj_dct['category'], _id=obj_dct['_id'])
        back_obj.properties = obj_dct['properties']
        back_obj.forms = obj_dct['forms']
        return back_obj

    @init_mongo_conn(MongoCObject)
    def insert_object(self, with_id=False):
        return super().insert_object(with_id=with_id)

    @init_mongo_conn(MongoCObject)
    def update_object(self):
        return super().update_object()

    @init_mongo_conn(MongoCObject)
    def delete_object(self):
        return super().delete_object()

    @classmethod
    @init_mongo_conn(MongoCObject)
    def remove_all(cls):
        super().remove_all()

    @classmethod
    @init_mongo_conn(MongoCObject)
    def init_from_mongo(cls, _id: Union[str, ObjectId]):
        obj_dct = cls.mongo_conn.find_object({'_id': _id}, multiple=False)
        if obj_dct:
            back_obj = BackendCObject.deserialize(obj_dct)
            return back_obj
        raise Exception(f'{cls.__name__} is not defined')
