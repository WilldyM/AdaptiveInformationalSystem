import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject, BaseBackendObject


class MongoTuplePart(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.tuple_parts_collection))

    def insert_object(self, class_obj: 'BackendTuplePart', with_id=False):
        obj_dct = class_obj.serialize(with_id=with_id)
        obj_id = self.insert_document(self.db.get_collection(self.tuple_parts_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.tuple_parts_collection), query, multiple=multiple)
        return obj

    def update_object(self, find_query: dict, set_query: dict, multiple: bool = False):
        if find_query.get('_id'):
            find_query['_id'] = ObjectId(find_query['_id'])
        updated_obj = self.update_document(self.db.get_collection(self.tuple_parts_collection),
                                           find_query, set_query, multiple=multiple)
        return updated_obj

    def remove_object(self, query):
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        try:
            self.delete_document(self.db.get_collection(self.tuple_parts_collection), query)
        except Exception as err:
            print(err)
            return False
        return True


class BackendTuplePart(BaseBackendObject):

    def __init__(self, display_name: str, model: str, c_object: str, _id: str = None):
        super().__init__(display_name, model, _id)
        self.c_object = c_object
        self.inputs = dict()
        self.outputs = dict()

    def serialize(self, with_id=False):
        obj_dct = super().serialize(with_id=with_id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        back_obj = BackendTuplePart(obj_dct['display_name'], obj_dct['model'],
                                    obj_dct['c_object'], _id=obj_dct['_id'])
        back_obj.inputs = obj_dct['inputs']
        back_obj.outputs = obj_dct['outputs']
        return back_obj

    @init_mongo_conn(MongoTuplePart)
    def insert_object(self, with_id=False):
        return super().insert_object(with_id=with_id)

    @init_mongo_conn(MongoTuplePart)
    def update_object(self):
        return super().update_object()

    @init_mongo_conn(MongoTuplePart)
    def delete_object(self):
        return super().delete_object()

    @classmethod
    @init_mongo_conn(MongoTuplePart)
    def remove_all(cls):
        super().remove_all()

    @classmethod
    @init_mongo_conn(MongoTuplePart)
    def init_from_mongo(cls, _id: Union[str, ObjectId]):
        obj_dct = cls.mongo_conn.find_object({'_id': _id}, multiple=False)
        if obj_dct:
            back_obj = BackendTuplePart.deserialize(obj_dct)
            return back_obj
        raise Exception(f'{cls.__name__} is not defined')
