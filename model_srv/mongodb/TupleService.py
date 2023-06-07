import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import init_mongo_conn, BaseMongoObject, BaseBackendObject
from model_srv.mongodb.GroupService import BackendGroup
from model_srv.mongodb.TuplePartService import BackendTuplePart


class MongoTuple(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.tuples_collection))

    def insert_object(self, class_obj: 'BackendTuple', with_id=False):
        obj_dct = class_obj.serialize(with_id=with_id)
        obj_id = self.insert_document(self.db.get_collection(self.tuples_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.tuples_collection), query, multiple=multiple)
        return obj

    def update_object(self, find_query: dict, set_query: dict, multiple: bool = False):
        if find_query.get('_id'):
            find_query['_id'] = ObjectId(find_query['_id'])
        updated_obj = self.update_document(self.db.get_collection(self.tuples_collection),
                                           find_query, set_query, multiple=multiple)
        return updated_obj

    def remove_object(self, query):
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        try:
            self.delete_document(self.db.get_collection(self.tuples_collection), query)
        except Exception as err:
            print(err)
            return False
        return True


class BackendTuple(BaseBackendObject):

    def __init__(self, display_name: str, model: str, _id: str = None):
        super().__init__(display_name, model, _id)
        self.tuple_parts = list()

    def remove_group(self, bk_group: Union[str, ObjectId, BackendGroup]):
        if isinstance(bk_group, (str, ObjectId)):
            self.tuple_parts.remove([str(bk_group)])
        elif isinstance(bk_group, BackendGroup):
            self.tuple_parts.remove([str(bk_group._id)])
        else:
            return False
        return True

    def remove_tuple_part(self, bk_tuple: Union[str, ObjectId, BackendTuplePart]):
        if isinstance(bk_tuple, (str, ObjectId)):
            self.tuple_parts.remove(str(bk_tuple))
        elif isinstance(bk_tuple, BackendTuplePart):
            self.tuple_parts.remove(str(bk_tuple._id))
        else:
            return False
        return True

    def add_tuple_part(self, bk_tuple_part: Union[str, ObjectId, BackendTuplePart, list]):
        if isinstance(bk_tuple_part, (str, ObjectId)):
            self.tuple_parts.append(str(bk_tuple_part))
        elif isinstance(bk_tuple_part, BackendTuplePart):
            self.tuple_parts.append(str(bk_tuple_part._id))
        elif isinstance(bk_tuple_part, list):
            self.tuple_parts.append(bk_tuple_part)
        elif isinstance(bk_tuple_part, tuple):
            self.tuple_parts.append(bk_tuple_part)

    @classmethod
    @init_mongo_conn(MongoTuple)
    def get_unique_name(cls, model_id: Union[str, ObjectId], start_value: str):
        return super().get_unique_name(model_id, start_value)

    def serialize(self, with_id=False):
        obj_dct = super().serialize(with_id=with_id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        back_obj = BackendTuple(obj_dct['display_name'], obj_dct['model'], _id=obj_dct['_id'])
        back_obj.tuple_parts = obj_dct['tuple_parts']
        return back_obj

    @init_mongo_conn(MongoTuple)
    def insert_object(self, with_id=False):
        return super().insert_object(with_id=with_id)

    @init_mongo_conn(MongoTuple)
    def update_object(self):
        return super().update_object()

    @init_mongo_conn(MongoTuple)
    def delete_object(self, cascade=False):
        if cascade:
            for tpl_part in self.tuple_parts:
                if isinstance(tpl_part, BackendTuplePart):
                    tpl_part.delete_object()
                    continue
                if isinstance(tpl_part, list):
                    group_id = tpl_part[0]
                    bk_group = BackendGroup.init_from_mongo(group_id)
                    bk_group.delete_object()
                    continue
                if isinstance(tpl_part, tuple):
                    continue
                bk_tuple_part = BackendTuplePart.init_from_mongo(tpl_part)
                bk_tuple_part.delete_object()
        return super().delete_object()

    @classmethod
    @init_mongo_conn(MongoTuple)
    def remove_all(cls):
        super().remove_all()

    @classmethod
    @init_mongo_conn(MongoTuple)
    def init_from_mongo(cls, _id: Union[str, ObjectId]):
        obj_dct = cls.mongo_conn.find_object({'_id': _id}, multiple=False)
        if obj_dct:
            back_obj = BackendTuple.deserialize(obj_dct)
            return back_obj
        raise Exception(f'{cls.__name__} is not defined')
