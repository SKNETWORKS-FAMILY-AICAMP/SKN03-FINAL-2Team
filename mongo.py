import pymongo
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# .env 파일 로드
load_dotenv()

db_password = os.getenv("MONGO_PASSWORD")

# MongoDB 연결
try:
    uri = f"mongodb+srv://museify52:{db_password}@museifycluster.g6flg.mongodb.net/?retryWrites=true&w=majority&appName=MuseifyCluster"
    client = MongoClient(uri)
except pymongo.errors.ConfigurationError:
    print("URI 호스트 에러가 발생했습니다. Atlas 호스트 이름을 확인해주세요.")
    sys.exit(1)

# 데이터베이스와 컬렉션 연결
db = client["MuseifyDB"]
collection_main = db["Musical"]

# JSON 파일 읽기 및 키값 수정
try:
    with open("per+raw.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    print("JSON 파일을 찾을 수 없습니다.")
    sys.exit(1)
except json.JSONDecodeError:
    print("JSON 파일 형식이 올바르지 않습니다.")
    sys.exit(1)

# 키값에 M_ 추가
if isinstance(data, list):
    modified_data = [
        {f"M_{key}": value for key, value in item.items()}
        for item in data
    ]
elif isinstance(data, dict):
    modified_data = {f"M_{key}": value for key, value in data.items()}
else:
    print("JSON 데이터 형식이 올바르지 않습니다.")
    sys.exit(1)

# 수정된 JSON 파일 저장
try:
    with open("M_per+raw_modified.json", "w", encoding="utf-8") as file:
        json.dump(modified_data, file, ensure_ascii=False, indent=4)
    print("수정된 JSON 파일이 저장되었습니다: M_per+raw_modified.json")
except IOError:
    print("수정된 JSON 파일 저장 중 오류가 발생했습니다.")
    sys.exit(1)

# 기존 데이터 삭제
try:
    collection_main.delete_many({})  # 조건 없이 모든 데이터 삭제
    print("기존 데이터를 삭제했습니다.")
except pymongo.errors.OperationFailure:
    print("인증 에러가 발생했습니다. 사용자 이름과 비밀번호를 확인해주세요.")
    sys.exit(1)

# 데이터 삽입
if isinstance(modified_data, list):
    try:
        result = collection_main.insert_many(modified_data)
    except pymongo.errors.OperationFailure:
        print("인증 에러가 발생했습니다. 데이터베이스 쓰기 권한을 확인해주세요.")
        sys.exit(1)
    else:
        inserted_count = len(result.inserted_ids)
        print(f"총 {len(modified_data)}개의 문서가 삽입되었습니다.")
else:
    print("JSON 파일이 배열 형식이어야 합니다.")
    sys.exit(1)
