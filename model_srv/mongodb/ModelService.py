import json
import copy
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.CObjectService import BackendCObject
from model_srv.mongodb.TupleService import BackendTuple
from model_srv.mongodb.TuplePartService import BackendTuplePart


class MongoModel(BaseMongoObject):

    def __init__(self):
        super().__init__()

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.models_collection))

    def insert_object(self, model_obj: 'BackendModel', with_id=False):
        model_dct = model_obj.serialize(with_id=with_id)
        model_id = self.insert_document(self.db.get_collection(self.models_collection), model_dct)
        return model_id

    def find_object(self, query: dict, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.models_collection), query, multiple=multiple)
        return obj

    def update_object(self, find_query: dict, set_query: dict, multiple: bool = False):
        if find_query.get('_id'):
            find_query['_id'] = ObjectId(find_query['_id'])
        updated_obj = self.update_document(self.db.get_collection(self.models_collection),
                                           find_query, set_query, multiple=multiple)
        return updated_obj

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

    def add_c_object(self, bk_obj: Union[str, ObjectId, BackendCObject]):
        if isinstance(bk_obj, str):
            self.c_objects.append(bk_obj)
        elif isinstance(bk_obj, ObjectId):
            self.c_objects.append(str(bk_obj))
        elif isinstance(bk_obj, BackendCObject):
            self.c_objects.append(str(bk_obj._id))
        else:
            return False
        return True

    def add_tuple(self, bk_tuple: Union[str, ObjectId, BackendTuple]):
        if isinstance(bk_tuple, str):
            self.tuples.append(bk_tuple)
        elif isinstance(bk_tuple, ObjectId):
            self.tuples.append(str(bk_tuple))
        elif isinstance(bk_tuple, BackendTuple):
            self.tuples.append(str(bk_tuple._id))
        else:
            return False
        return True

    @classmethod
    @init_mongo_conn(MongoModel)
    def get_all_models(cls, query):
        obj_lst = cls.mongo_conn.find_object(query, multiple=True)
        return obj_lst

    def serialize(self, with_id=False):
        model_dct = self.__dict__.copy()
        model_dct.pop('mongo_conn')
        model_dct.pop('categories')
        model_dct['_id'] = ObjectId(model_dct['_id'])
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
        categories = BackendCategory.get_all_categories()
        self.categories = {str(i['_id']): i['display_name'] for i in categories}

    @init_mongo_conn(MongoModel)
    def insert_model(self, with_id=False) -> Union[None, str, ObjectId]:
        try:
            self._id = self.mongo_conn.insert_object(self, with_id=with_id)
        except Exception as err:
            print(err)
            return None
        return self._id

    @init_mongo_conn(MongoModel)
    def update_model(self):
        model_dct = self.serialize(with_id=False)
        self.mongo_conn.update_object({'_id': self._id}, model_dct, multiple=False)

    @init_mongo_conn(MongoModel)
    def delete_model(self, cascade=False) -> bool:
        if self._id is not None:
            if cascade:
                for c_object_id in self.c_objects:
                    if isinstance(c_object_id, BackendCObject):
                        c_object_id.delete_object()
                        continue
                    bk_obj = BackendCObject.init_from_mongo(c_object_id)
                    bk_obj.delete_object()
                for tuple_id in self.tuples:
                    if isinstance(tuple_id, BackendTuple):
                        tuple_id.delete_object()
                        continue
                    bk_tuple = BackendTuple.init_from_mongo(tuple_id)
                    bk_tuple.delete_object(cascade=True)
            self.mongo_conn.remove_object({'_id': self._id})
            return True
        return False

    def get_model_metadata(self):
        initialized_tuples = list()
        for t_id in self.tuples:
            initialized_tuples.append(BackendTuple.init_from_mongo(t_id))
        initialized_c_objects = list()
        for c_obj_id in self.c_objects:
            initialized_c_objects.append(BackendCObject.init_from_mongo(c_obj_id))
        res = {'c_objects': initialized_c_objects, 'tuples': initialized_tuples}
        return res

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






