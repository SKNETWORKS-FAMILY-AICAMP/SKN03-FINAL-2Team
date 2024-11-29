"""파일 경로"""
import os

# 프로젝트 루트 경로를 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # config.py 파일의 절대 경로 기준

# 파일 경로
file_path = os.path.join(BASE_DIR, "data_modules")
per_raw = "per+raw.json"
processed_data = "processed_data.json"
add_genre_file_name = "add_genre_story.json"
df_with_negatives_path = os.path.join(file_path, "df_with_negatives.json")
picture_file_path = os.path.join(BASE_DIR, "app", "static", "Performance.jpg")
save_model_path = os.path.join(file_path, "Model", "Recommend.h5")
    
# genre
unique_genres = [
    "대학로", "가족", "신화", "역사", "지역|창작"
]

# 삭제할 컬럼 목록
columns_to_drop = [
    "performance_id", "facility_id", "producer", "planner", 
    "host", "sponsor", "synopsis", "genre", "open_run", 
    "visit", "daehakro", "festival", "musical_create"
]