from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoBase:
    client = None
    db = None
    vector_db = None

    @staticmethod
    def initialize(uri, db_name, vector_db_name):
        if MongoBase.client is None:
            MongoBase.client = MongoClient(uri, server_api=ServerApi("1"))
            MongoBase.db = MongoBase.client[db_name]
            MongoBase.vector_db = MongoBase.client[vector_db_name]

    @staticmethod
    def close():
        if MongoBase.client:
            MongoBase.client.close()

    def __init__(self, collection_name):
        if MongoBase.db is None:
            raise RuntimeError("Initialize MongoBase by calling MongoBase.initialize()")
        self.collection = MongoBase.db[collection_name]

    def find(self, *args, **kwargs) -> list:
        return self.collection.find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        return self.collection.find_one(*args, **kwargs)

    def insert_one(self, document: dict):
        return self.collection.insert_one(document).inserted_id

    def update_one(self, filter, update, upsert=False):
        return self.collection.update_one(filter, update, upsert)

    def delete_one(self, query: dict):
        if not query:
            raise ValueError("Delete operation requires a query condition.")
        return self.collection.delete_one(query)

    def delete_many(self, query: dict):
        if not query:
            raise ValueError("Delete operation requires a query condition.")
        result = self.collection.delete_many(query)
        return result.deleted_count

    def delete_all(self):
        result = self.collection.delete_many({})
        return result.deleted_count
