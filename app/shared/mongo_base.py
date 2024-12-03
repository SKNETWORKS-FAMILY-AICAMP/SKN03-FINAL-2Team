import os

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoBase:
    _instance = None
    client = None
    db = None
    vector_db = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls.initialize(
                os.getenv("MONGO_URI"),
                os.getenv("MONGO_DB_NAME"),
                os.getenv("MONGO_VECTOR_DB_NAME"),
            )
        return cls._instance

    @classmethod
    def get_collection(cls, db_type, collection_name):
        instance = cls.get_instance()
        if db_type == "vector":
            return instance.vector_db[collection_name]
        return instance.db[collection_name]

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


def ensure_connection(func):
    def wrapper(*args, **kwargs):
        if MongoBase.client is None:
            MongoBase.initialize(
                os.getenv("MONGO_URI"),
                os.getenv("MONGO_DB_NAME"),
                os.getenv("MONGO_VECTOR_DB_NAME"),
            )
        return func(*args, **kwargs)

    return wrapper
