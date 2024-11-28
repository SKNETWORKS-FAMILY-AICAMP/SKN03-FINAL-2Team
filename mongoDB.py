import pymongo
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

load_dotenv()

db_password = os.getenv("MONGO_PASSWORD")

# MongoDB 연결
try:
    uri = f"mongodb+srv://museify52:{db_password}@museifycluster.g6flg.mongodb.net/?retryWrites=true&w=majority&appName=MuseifyCluster"
    client = MongoClient(uri)
except pymongo.errors.ConfigurationError:
    print("URI 호스트 에러가 발생했습니다. Atlas 호스트 이름을 확인해주세요.")
    sys.exit(1)

# 두 데이터베이스와 컬렉션 연결
db = client["MuseifyDB"]
collection_main = db["Exhibition"]

vector_db = client["MuseifyVectorDB"]
collection_vector = vector_db["Exhibition"]

# 데이터 삽입
try:
    with open("./data/exhibition_data.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    print("JSON 파일을 찾을 수 없습니다.")
    sys.exit(1)
except json.JSONDecodeError:
    print("JSON 파일 형식이 올바르지 않습니다.")
    sys.exit(1)

# 기존 데이터 삭제
try:
    collection_main.delete_many({})  # 조건 없이 모든 데이터 삭제
    print("기존 데이터를 삭제했습니다.")
except pymongo.errors.OperationFailure:
    print("인증 에러가 발생했습니다. 사용자 이름과 비밀번호를 확인해주세요.")
    sys.exit(1)

# JSON 파일에서 E_context가 빈 문자열이 아닌 데이터만 필터링
if isinstance(data, list):
    filtered_data = [item for item in data if item.get('E_context', '') != '']
    try:
        result = collection_main.insert_many(filtered_data)
    except pymongo.errors.OperationFailure:
        print("인증 에러가 발생했습니다. 데이터베이스 쓰기 권한을 확인해주세요.")
        sys.exit(1)
    else:
        inserted_count = len(result.inserted_ids)
        print(f"총 {len(data)}개 중 {inserted_count}개의 문서가 삽입되었습니다.")
else:
    print("JSON 파일이 배열 형식이어야 합니다.")
    sys.exit(1)

# 벡터 데이터 삽입
try:
    with open("./data/exhibition_embeddings.json", "r", encoding="utf-8") as vector_file:
        vector_data = json.load(vector_file)
except FileNotFoundError:
    print("벡터 JSON 파일을 찾을 수 없습니다.")
    sys.exit(1)
except json.JSONDecodeError:
    print("벡터 JSON 파일 형식이 올바르지 않습니다.")
    sys.exit(1)

# 기존 벡터 데이터 삭제
try:
    collection_vector.delete_many({})  # 조건 없이 모든 데이터 삭제
    print("기존 벡터 데이터를 삭제했습니다.")
except pymongo.errors.OperationFailure:
    print("벡터 데이터 삭제 중 문제가 발생했습니다.")
    sys.exit(1)

# Main DB와 Vector DB 데이터를 연결
for exhibition, vector in zip(filtered_data, vector_data):
    # Exhibition 데이터의 _id 가져오기
    exhibition_id = result.inserted_ids[filtered_data.index(exhibition)]

    # Vector 데이터 삽입
    vector_entry = {
        "E_text": vector["E_text"],
        "E_embedding": vector["E_embedding"],
        "E_original_id": exhibition_id  # MuseifyDB의 _id 참조
    }
    try:
        collection_vector.insert_one(vector_entry)
    except pymongo.errors.OperationFailure:
        print("벡터 데이터 삽입 중 문제가 발생했습니다.")
        sys.exit(1)

print(f"총 {len(vector_data)}개의 벡터 데이터가 Exhibition 데이터와 연결되었습니다.")
