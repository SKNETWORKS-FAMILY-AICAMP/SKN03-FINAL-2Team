from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoBase:
    _client = None
    _db = None
    _vector_db = None

    @staticmethod
    def initialize(uri, db_name, vector_db_name):
        if MongoBase._client is None:
            MongoBase._client = MongoClient(uri, server_api=ServerApi("1"))
            MongoBase._db = MongoBase._client[db_name]
            MongoBase._vector_db = MongoBase._client[vector_db_name]

    @staticmethod
    def close():
        if MongoBase._client:
            MongoBase._client.close()

    def __init__(self, collection_name):
        if MongoBase._db is None:
            raise RuntimeError("Initialize MongoBase by calling MongoBase.initialize()")
        self.collection = MongoBase._db[collection_name]

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

    def manual_vector_search(
        self, index_name, query_vector, path, limit=10, exact=True
    ):
        pipeline = [
            {
                "$vectorSearch": {
                    "exact": exact,
                    "index": index_name,
                    "limit": limit,
                    "path": "embedding",
                    "queryVector": query_vector,
                }
            }
        ]
        return [
            {"content": obj["content"], "metadata": obj["metadata"]}
            for obj in self.collection.aggregate(pipeline)
        ]
