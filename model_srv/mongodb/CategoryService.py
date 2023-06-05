import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject, BaseBackendObject


class MongoCategory(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.categories_collection))

    def insert_object(self, class_obj: 'BackendCategory', with_id=False):
        obj_dct = class_obj.serialize(with_id=with_id)
        obj_id = self.insert_document(self.db.get_collection(self.categories_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        obj = self.find_document(self.db.get_collection(self.categories_collection), query, multiple=multiple)
        return obj

    def update_object(self, find_query: dict, set_query: dict, multiple: bool = False):
        if find_query.get('_id'):
            find_query['_id'] = ObjectId(find_query['_id'])
        updated_obj = self.update_document(self.db.get_collection(self.categories_collection),
                                           find_query, set_query, multiple=multiple)
        return updated_obj

    def remove_object(self, query):
        try:
            self.delete_document(self.db.get_collection(self.categories_collection), query)
        except Exception as err:
            print(err)
            return False
        return True


class BackendCategory(BaseBackendObject):

    def __init__(self, display_name: str, model: str, part_of: str,
                 forms: dict, template: list, cat_import: str, _id: str = None):
        super().__init__(display_name, model, _id)
        self.forms = forms
        self.template = template
        self.part_of = part_of
        self.cat_import = cat_import

    @classmethod
    @init_mongo_conn(MongoCategory)
    def get_all_categories(cls):
        categories = cls.mongo_conn.find_object({}, multiple=True)
        return categories

    def serialize(self, with_id=True):
        obj_dct = super().serialize(with_id=with_id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        back_obj = BackendCategory(**obj_dct)
        return back_obj

    @init_mongo_conn(MongoCategory)
    def insert_object(self, with_id=False):
        return super().insert_object(with_id=with_id)

    @init_mongo_conn(MongoCategory)
    def update_object(self):
        return super().update_object()

    @init_mongo_conn(MongoCategory)
    def delete_object(self):
        return super().delete_object()

    @classmethod
    @init_mongo_conn(MongoCategory)
    def remove_all(cls):
        super().remove_all()

    @classmethod
    @init_mongo_conn(MongoCategory)
    def init_from_mongo(cls, _id: str):
        obj_dct = cls.mongo_conn.find_object({'_id': _id}, multiple=False)
        if obj_dct:
            back_obj = BackendCategory.deserialize(obj_dct)
            return back_obj
        raise Exception(f'{cls.__name__} is not defined')
