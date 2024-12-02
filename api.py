import requests
import xml.etree.ElementTree as ET
import json
import time
from dotenv import load_dotenv
import os

# 환경 변수에서 API 키 가져오기
load_dotenv()
API_KEY = os.getenv("KOPIS_API_KEY")

# API 엔드포인트
LIST_URL = "http://kopis.or.kr/openApi/restful/pblprfr"
DETAIL_URL = "http://kopis.or.kr/openApi/restful/pblprfr"

# 안전하게 태그 값 가져오기
def safe_find_text(element, tag, default="미입력"):
    """
    주어진 XML Element에서 태그 값을 안전하게 추출합니다.
    """
    found = element.find(tag)
    return found.text.strip() if found is not None and found.text.strip() else default

# 공연 목록 조회 함수
def get_performance_list(api_key, start_date, end_date, genre, rows=10):
    """
    공연 목록을 조회하여 반환합니다.
    """
    performances = []
    page = 1
    while True:
        params = {
            "service": api_key,
            "stdate": start_date,
            "eddate": end_date,
            "shcate": genre,
            "rows": rows,
            "cpage": page
        }
        response = requests.get(LIST_URL, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            current_page_data = []
            for item in root.findall("db"):
                current_page_data.append({
                    "id": safe_find_text(item, "mt20id"),
                    "title": safe_find_text(item, "prfnm"),
                    "start_date": safe_find_text(item, "prfpdfrom"),
                    "end_date": safe_find_text(item, "prfpdto")
                })
            if not current_page_data:  # 더 이상 데이터가 없으면 종료
                break
            performances.extend(current_page_data)
            page += 1
        else:
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
            # XML 데이터 파싱
            root = ET.fromstring(response.content)
            db = root.find("db")  # <db> 태그 탐색

            if db is None:
                return None

            # 공연 상세 정보 추출
            detail = {
                "title": safe_find_text(db, "prfnm"),
                "start_date": safe_find_text(db, "prfpdfrom"),
                "end_date": safe_find_text(db, "prfpdto"),
                "genre": safe_find_text(db, "genrenm"),
                "place": safe_find_text(db, "fcltynm"),
                "poster": safe_find_text(db, "poster"),
                "prfstate": safe_find_text(db, "prfstate"),
                "runtime": safe_find_text(db, "prfruntime"),
                "age": safe_find_text(db, "prfage"),
                "cast": safe_find_text(db, "prfcast"),
                "crew": safe_find_text(db, "prfcrew"),
                "story": safe_find_text(db, "sty"),
                "ticket_price": safe_find_text(db, "pcseguidance"),
                "host": safe_find_text(db, "entrpsnmH"),
                "sponsor": safe_find_text(db, "entrpsnmS"),
                "musical_license": safe_find_text(db, "musicallicense"),
                "musical_create": safe_find_text(db, "musicalcreate"),
                "time": safe_find_text(db, "dtguidance"),
                "additional_images": [
                    safe_find_text(styurl, ".") for styurl in db.findall("styurls/styurl")
                ]
            }
            return detail
        except Exception:
            return None
    else:
        return None

# 파일에 저장하는 함수
def save_to_file(filename, data, as_json=False):
    """
    데이터를 파일에 저장합니다.
    """
    with open(filename, "w", encoding="utf-8") as f:
        if as_json:
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write(data)

# 메인 함수
if __name__ == "__main__":
    # 공연 목록 조회 설정
    START_DATE = "20230101"  # 시작일
    END_DATE = "20241231"    # 종료일
    GENRE = "GGGA"           # 뮤지컬 장르 코드

    # 공연 목록 가져오기
    performance_list = get_performance_list(API_KEY, START_DATE, END_DATE, GENRE)

    # 공연 상세 정보 가져오기 (전체 데이터 처리)
    all_details = []
    for performance in performance_list:  # 전체 공연 처리
        detail = get_performance_detail(API_KEY, performance["id"])
        if detail:
            all_details.append(detail)
        time.sleep(1)  # 요청 간 대기 (API 호출 제한 방지)

    # 결과 저장
    save_to_file("musical_details.json", all_details, as_json=True)
