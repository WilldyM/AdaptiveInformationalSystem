from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.mongo_service import MongoConfigBase


def init_mongo_conn(class_object):
    def class_decorator(func):
        def wrapper(self, *args, **kwargs):
            self.mongo_conn = class_object()
            r = func(self, *args, **kwargs)
            self.mongo_conn.close_connection()
            return r
        return wrapper
    return class_decorator


class BaseMongoObject(MongoConfigBase):

    def __init__(self):
        self.set_connection()
        self.db = self.client[self.db_name]

    def drop_database(self, db_name=None):
        if db_name:
            self.client.drop_database(db_name)
        else:
            self.client.drop_database(self.db_name)

    def drop_collection(self):
        pass

    def insert_object(self, class_obj, with_id=False):
        pass

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        pass

    def update_object(self, find_query, set_query, multiple=False):
        pass

    def remove_object(self, query):
        pass


class BaseBackendObject(object):
    mongo_conn = None

    def __init__(self, display_name: str, model: Union[str, ObjectId], _id: str = None):
        if isinstance(model, ObjectId):
            model = str(model)
        self._id = _id
        self.display_name = display_name
        self.model = model

    @classmethod
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

    @classmethod
    def new_name(cls, value, search_lst, i=0):
        start_value = value + '_' + str(i) if i != 0 else value
        end_value = start_value
        if start_value in search_lst:
            i += 1
            end_value = cls.new_name(value, search_lst, i)
        return end_value

    def serialize(self, with_id=False):
        obj_dct = self.__dict__.copy()
        obj_dct.pop('mongo_conn')
        obj_dct.pop('_id')
        if with_id is True:
            obj_dct['_id'] = ObjectId(self._id)
        return obj_dct

    @staticmethod
    def deserialize(obj_dct):
        pass

    def insert_object(self, with_id=False):
        try:
            self._id = self.mongo_conn.insert_object(self, with_id=with_id)
        except Exception as err:
            print(err)
            return None
        return self._id

    def update_object(self):
        obj_dct = self.serialize(with_id=False)
        self.mongo_conn.update_object({'_id': self._id}, obj_dct, multiple=False)

    def delete_object(self):
        if self._id is not None:
            self.mongo_conn.remove_object({'_id': self._id})
            return True
        return False

    @classmethod
    def remove_all(cls):
        cls.mongo_conn.drop_collection()

    @classmethod
    def init_from_mongo(cls, _id: Union[str, ObjectId]):
        pass
