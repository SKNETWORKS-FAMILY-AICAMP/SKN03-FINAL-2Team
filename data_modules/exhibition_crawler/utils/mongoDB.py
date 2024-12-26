import pymongo
from pymongo import MongoClient
import sys
import logging
from .paramstore import ParameterStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        try:
            uri = ParameterStore.get_parameter('MONGO_URI')
            self.client = MongoClient(uri)
            self.db = self.client[ParameterStore.get_parameter('MONGO_DB_NAME')]
            self.vector_db = self.client[ParameterStore.get_parameter('MONGO_VECTOR_DB_NAME')]
            self.collection_main = self.db["Exhibition"]
            self.collection_vector = self.vector_db["Exhibition"]
            # 연결 테스트
            self.client.admin.command('ping')
            logger.info("MongoDB 연결 성공")
        except pymongo.errors.ConfigurationError as e:
            logger.error(f"URI 설정 오류: {str(e)}")
            raise
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"MongoDB 연결 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            raise

    def clear_collections(self):
        """기존 컬렉션의 모든 데이터를 삭제합니다."""
        try:
            self.collection_main.delete_many({})
            self.collection_vector.delete_many({})
            logger.info("기존 데이터를 모두 삭제했습니다.")
        except pymongo.errors.OperationFailure as e:
            logger.error(f"데이터 삭제 중 오류 발생: {str(e)}")
            sys.exit(1)

    def insert_exhibition_data(self, exhibition_data):
        """전시회 메타데이터를 삽입합니다."""
        try:
            if not exhibition_data:
                return None
            result = self.collection_main.insert_many(exhibition_data)
            logger.info(f"{len(result.inserted_ids)}개의 전시회 데이터가 삽입되었습니다.")
            return result.inserted_ids
        except pymongo.errors.OperationFailure as e:
            logger.error(f"메타데이터 삽입 중 오류 발생: {str(e)}")
            return None

    def insert_vector_data(self, vector_data, original_id):
        """벡터 데이터를 삽입합니다."""
        try:
            vector_entry = {
                "E_text": vector_data["text"],
                "E_embedding": vector_data["embedding"],
                "E_original_id": original_id
            }
            self.collection_vector.insert_one(vector_entry)
            return True
        except pymongo.errors.OperationFailure as e:
            logger.error(f"벡터 데이터 삽입 중 오류 발생: {str(e)}")
            return False