import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.TupleService import BackendTuple


class MongoModel(BaseMongoObject):

    def __init__(self):
        super().__init__()

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.models_collection))

    def insert_object(self, model_obj: 'BackendModel'):
        model_dct = model_obj.serialize()
        model_id = self.insert_document(self.db.get_collection(self.models_collection), model_dct)
        return model_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.models_collection), query, multiple=multiple)
        return obj

    def remove_object(self, query):
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        try:
            self.delete_document(self.db.get_collection(self.models_collection), query)
        except Exception as err:
            print(err)
            return False
        return True


class BackendModel(object):
    mongo_conn = None

    def __init__(self, owner, display_name, _id=None):
        self._id = _id
        self.owner = owner
        self.display_name = display_name

        self.categories = list()
        self.c_objects = list()
        self.tuples = list()

        self._init_categories()

    @classmethod
    @init_mongo_conn(MongoModel)
    def get_all_models(cls, query):
        obj_lst = cls.mongo_conn.find_object(query, multiple=True)
        return obj_lst

    def serialize(self, with_id=False):
        model_dct = self.__dict__.copy()
        model_dct.pop('mongo_conn')
        model_dct.pop('categories')
        if with_id is False:
            model_dct.pop('_id')
        return model_dct

    @staticmethod
    def deserialize(model_dct):
        back_model = BackendModel(model_dct['owner'], model_dct['display_name'], _id=model_dct['_id'])
        back_model.tuples = model_dct['tuples']
        back_model.c_objects = model_dct['c_objects']
        return back_model

    @init_mongo_conn(MongoModel)
    def _init_categories(self):
        """
        init all categories from db
        """

    @init_mongo_conn(MongoModel)
    def insert_model(self) -> Union[None, str, ObjectId]:
        try:
            self._id = self.mongo_conn.insert_object(self)
        except Exception as err:
            print(err)
            return None
        return self._id

    @init_mongo_conn(MongoModel)
    def delete_model(self) -> bool:
        if self._id is not None:
            self.mongo_conn.remove_object(self._id)
            return True
        return False

    def init_model_metadata(self):
        initialized_tuples = list()
        for t_id in self.tuples:
            initialized_tuples.append(BackendTuple.init_from_mongo(t_id))
        self.tuples = initialized_tuples

        initialized_c_objects = list()
        for c_obj_id in self.c_objects:
            initialized_c_objects.append(BackendCObject.init_from_mongo(c_obj_id))
        self.c_objects = initialized_c_objects

    @classmethod
    @init_mongo_conn(MongoModel)
    def remove_all(cls):
        cls.mongo_conn.drop_collection()

    @classmethod
    @init_mongo_conn(MongoModel)
    def init_from_mongo(cls, _id: Union[str, ObjectId]):
        model_dct = cls.mongo_conn.find_object({'_id': _id}, multiple=False)
        if model_dct:
            back_model = BackendModel.deserialize(model_dct)
            return back_model
        raise Exception('Model is not defined')






