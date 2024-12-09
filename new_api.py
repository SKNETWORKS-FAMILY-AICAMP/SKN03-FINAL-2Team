import requests
import xml.etree.ElementTree as ET
import json
import time
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# 환경 변수에서 API 키 가져오기
load_dotenv()
API_KEY = os.getenv("KOPIS_API_KEY")

# API 엔드포인트
LIST_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"
DETAIL_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"

# 안전하게 태그 값 가져오기
def safe_find_text(element, tag, default="미입력"):
    found = element.find(tag)
    return found.text.strip() if found is not None and found.text.strip() else default

# 날짜 범위를 31일씩 분할
def split_date_range(start_date, end_date, max_days=31):
    date_ranges = []
    current_start = datetime.strptime(start_date, "%Y%m%d")
    end_date_obj = datetime.strptime(end_date, "%Y%m%d")

    while current_start <= end_date_obj:
        current_end = min(current_start + timedelta(days=max_days - 1), end_date_obj)
        date_ranges.append((current_start.strftime("%Y%m%d"), current_end.strftime("%Y%m%d")))
        current_start = current_end + timedelta(days=1)

    return date_ranges

# 공연 목록 조회 함수
def get_performance_list(api_key, start_date, end_date, genre, rows=100):
    """
    공연 목록을 조회하여 반환합니다.
    """
    performances = []
    date_ranges = split_date_range(start_date, end_date)
    for start, end in date_ranges:
        params = {
            "service": api_key,
            "stdate": start,
            "eddate": end,
            "shcate": genre,
            "rows": rows,
            "cpage": 1
        }
        while True:
            response = requests.get(LIST_URL, params=params)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                current_page_data = []
                for item in root.findall("db"):
                    performance_id = safe_find_text(item, "mt20id")
                    if performance_id == "미입력":
                        continue
                    current_page_data.append({
                        "id": performance_id,
                        "title": safe_find_text(item, "prfnm"),
                        "start_date": safe_find_text(item, "prfpdfrom"),
                        "end_date": safe_find_text(item, "prfpdto")
                    })
                performances.extend(current_page_data)
                # 다음 페이지로 이동
                if len(current_page_data) < rows:
                    break
                params["cpage"] += 1
            else:
                print(f"[Error] Fetching performances failed: {response.status_code}, {response.text}")
                break
    return performances

# 공연 상세 조회 함수
def get_performance_detail(api_key, performance_id):
    """
    공연 상세 정보를 가져옵니다.
    """
    url = f"{DETAIL_URL}/{performance_id}?service={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            db = root.find("db")
            if db is None:
                return None
            return {
                "title": safe_find_text(db, "prfnm"),
                "start_date": safe_find_text(db, "prfpdfrom"),
                "end_date": safe_find_text(db, "prfpdto"),
                "genre": safe_find_text(db, "genrenm"),
                "place": safe_find_text(db, "fcltynm"),
                "poster": safe_find_text(db, "poster"),
                "state": safe_find_text(db, "prfstate"),
                "runtime": safe_find_text(db, "prfruntime"),
                "age": safe_find_text(db, "prfage"),
                "cast": safe_find_text(db, "prfcast"),
                "crew": safe_find_text(db, "prfcrew"),
                "story": safe_find_text(db, "sty"),
                "ticket_price": safe_find_text(db, "pcseguidance"),
                "time": safe_find_text(db, "dtguidance"),
                "additional_images": [
                    safe_find_text(styurl, ".") for styurl in db.findall("styurls/styurl")
                ]
            }
        except Exception as e:
            print(f"[Error] Parsing performance detail failed for ID {performance_id}: {e}")
            return None
    else:
        print(f"[Error] Fetching performance detail failed for ID {performance_id}: {response.status_code}, {response.text}")
        return None

# 파일에 저장
def save_to_file(filename, data, as_json=False):
    with open(filename, "w", encoding="utf-8") as f:
        if as_json:
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write(data)

# 메인
if __name__ == "__main__":
    START_DATE = "20230101"  # 시작일
    END_DATE = "20241231"    # 종료일
    GENRE = "GGGA"           # 뮤지컬 장르 코드

    # 공연 목록 가져오기
    performance_list = get_performance_list(API_KEY, START_DATE, END_DATE, GENRE, rows=100)

    all_details = []
    for performance in performance_list:
        detail = get_performance_detail(API_KEY, performance["id"])
        if detail:
            all_details.append(detail)
        time.sleep(1)  # API 호출 간 대기
        # 현재까지 수집된 상세 정보 개수 출력
        print(f"Collected {len(all_details)} performance details so far.")

    save_to_file("musical_details.json", all_details, as_json=True)
    print(f"Final count: {len(all_details)} performance details saved to 'musical_details.json'")
