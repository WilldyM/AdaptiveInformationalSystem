import json
from typing import Union

from bson.objectid import ObjectId

from model_srv.mongodb.BaseBackendObject import BaseMongoObject


class MongoAuthService(BaseMongoObject):

    def drop_collection(self):
        self.db.drop_collection(self.db.get_collection(self.users_collection))

    def insert_object(self, class_object: dict):
        obj_dct = {
            'login': class_object['login'],
            'password': class_object['password'],
            'role': class_object.get('role', 'user')
        }
        obj_id = self.insert_document(self.db.get_collection(self.users_collection), obj_dct)
        return obj_id

    def find_object(self, query, multiple=True) -> Union[dict, list]:
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        obj = self.find_document(self.db.get_collection(self.users_collection), query, multiple=multiple)
        return obj

    def remove_object(self, query):
        if query.get('_id'):
            query['_id'] = ObjectId(query['_id'])
        try:
            self.delete_document(self.db.get_collection(self.users_collection), query)
        except Exception as err:
            print(err)
            return False
        return True

    def auth(self, login, password):
        obj = self.find_object({'login': login}, multiple=False)
        if obj:
            if password == obj['password']:
                print('success')
                return obj
            else:
                raise ValueError('password is invalid')
        else:
            raise ValueError(f'login {login} is not defined')

    def register(self, login, password):
        is_exists_login = self.find_object({'login': login}, multiple=False)
        if not is_exists_login:
            if not password:
                raise ValueError('password can not be empty')
            reg_dct = {'login': login, 'password': password, 'role': 'user'}
            login_id = self.insert_object(reg_dct)
            reg_dct['_id'] = login_id
            return reg_dct
        raise ValueError(f'login {login} already exists')


if __name__ == '__main__':

    m = MongoAuthService()
    # m.insert_object({'login': 'testuser', 'password': 'testpass'})
    m.register('testuser1', '123')
    m.close_connection()


