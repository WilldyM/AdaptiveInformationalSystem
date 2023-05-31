from pymongo import MongoClient
from bson.objectid import ObjectId


class MongoConfigBase(object):
    host = 'localhost'
    port = 27017
    username = None
    password = None
    client = None

    db_name = 'adaptive_service'
    models_collection = 'models'
    objects_collection = 'c_objects'
    tuples_collection = 'tuples'
    tuple_parts_collection = 'tuple_parts'
    categories_collection = 'categories'

    users_collection = 'users'

    def set_connection(self):
        try:
            self.client = MongoClient(host=self.host, port=self.port, username=self.username, password=self.password)
        except Exception as e:
            print('mongo_conn error: ', e)

    def close_connection(self):
        self.client.close()

    def drop_database(self, db_name=None):
        if not db_name:
            print('db_name is not defined')
            return
        self.client.drop_database(db_name)

    @staticmethod
    def insert_document(collection, data):
        """ Function to insert a document into a collection and
        return the document's id.
        """
        return collection.insert_one(data).inserted_id

    @staticmethod
    def find_document(collection, elements=None, multiple=False):
        """ Function to retrieve single or multiple documents from a provided
        Collection using a dictionary containing a document's elements.
        """
        if multiple:
            results = collection.find(elements)
            return [r for r in results]
        else:
            return collection.find_one(elements)

    @staticmethod
    def update_document(collection, query_elements, new_values):
        """ Function to update a single document in a collection.
        """
        collection.update_one(query_elements, {'$set': new_values})

    @staticmethod
    def delete_document(collection, query):
        """ Function to delete a single document from a collection.
        """
        collection.delete_one(query)

    def __del__(self):
        self.client.close()
