import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject, BaseBackendObject


class MongoCObject(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.objects_collection))

    def insert_object(self, class_obj: 'BackendCObject'):
        obj_dct = class_obj.serialize()
        obj_id = self.insert_document(self.db.get_collection(self.objects_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.objects_collection), query, multiple=multiple)
        return obj

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

    def __init__(self, display_name: str, model: str, category: str, _id: str = None):
        super().__init__(display_name, model, _id)
        self.category = category
        self.properties = dict()
        self.methods = dict()

    def serialize(self, with_id=True):
        obj_dct = super().serialize(with_id=with_id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        back_obj = BackendCObject(obj_dct['display_name'], obj_dct['model'],
                                  obj_dct['category'], _id=obj_dct['_id'])
        back_obj.properties = obj_dct['properties']
        back_obj.methods = obj_dct['methods']
        return back_obj

    @init_mongo_conn(MongoCObject)
    def insert_object(self):
        return super().insert_object(self)

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
        obj_dct = cls.mongo_conn.find_object(_id)
        if obj_dct:
            back_obj = BackendCObject.deserialize(obj_dct)
            return back_obj
        raise Exception(f'{cls.__name__} is not defined')
