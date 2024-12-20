import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import boto3


def get_param(parameter_name):
    ssm = boto3.client('ssm', region_name="ap-northeast-2")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']

API_KEY = get_param("KOPIS_API_KEY")
LIST_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"
DETAIL_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"

# 안전하게 태그 값을 가져오기
def safe_find_text(element, tag, default=""):
    try:
        found = element.find(tag)
        return found.text.strip() if found is not None and found.text.strip() else default
    except AttributeError:
        return default

# 날짜 범위를 지정한 간격으로 분할
def split_date_range(start_date, end_date, max_days=31):
    date_ranges = []
    current_start = datetime.strptime(start_date, "%Y%m%d")
    end_date_obj = datetime.strptime(end_date, "%Y%m%d")

    while current_start <= end_date_obj:
        current_end = min(current_start + timedelta(days=max_days - 1), end_date_obj)
        date_ranges.append((current_start.strftime("%Y%m%d"), current_end.strftime("%Y%m%d")))
        current_start = current_end + timedelta(days=1)

    return date_ranges

# 공연 목록 조회
def get_performance_list(api_key, start_date, end_date, genre, rows=100):
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
            try:
                response = requests.get(LIST_URL, params=params)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
                root = ET.fromstring(response.content)
                for item in root.findall("db"):
                    performance = {
                        "id": safe_find_text(item, "mt20id"),
                        "title": safe_find_text(item, "prfnm"),
                        "start_date": safe_find_text(item, "prfpdfrom"),
                        "end_date": safe_find_text(item, "prfpdto"),
                    }
                    if performance["id"]:
                        performances.append(performance)
                if len(root.findall("db")) < rows:  # 더 이상 데이터가 없으면 종료
                    break
                params["cpage"] += 1
            except requests.exceptions.RequestException as e:
                print(f"API 호출 오류: {e}")
                break
            except ET.ParseError:
                print("XML 파싱 오류가 발생했습니다.")
                break
    return performances

# 공연 상세 데이터 조회
def get_performance_detail(api_key, performance_id):
    url = f"{DETAIL_URL}/{performance_id}?service={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        db = root.find("db")
        if db:
            return {
                "id": performance_id,
                "title": safe_find_text(db, "prfnm"),
                "start_date": safe_find_text(db, "prfpdfrom"),
                "end_date": safe_find_text(db, "prfpdto"),
                "genre": safe_find_text(db, "genrenm"),
                "place": safe_find_text(db, "fcltynm"),
                "state": safe_find_text(db, "prfstate"),
                "runtime": safe_find_text(db, "prfruntime"),
                "cast": safe_find_text(db, "prfcast"),
                "crew": safe_find_text(db, "prfcrew"),
                "story": safe_find_text(db, "sty"),
                "poster": safe_find_text(db, "poster"),
            }
    except requests.exceptions.RequestException as e:
        print(f"상세 조회 오류: {e}")
    return None

# 상세 데이터 추가 처리
def add_detailed_info(df):
    details = []
    for _, row in df.iterrows():
        detail = get_performance_detail(API_KEY, row["id"])
        if detail:
            details.append(detail)
        time.sleep(0.5)  # API 호출 간 딜레이
    return pd.DataFrame(details)

# Main 함수
def main():
    START_DATE = "20241220"
    END_DATE = "20241231"
    GENRE = "GGGA"

    print("공연 데이터를 수집 중입니다...")
    performance_list = get_performance_list(API_KEY, START_DATE, END_DATE, GENRE, rows=100)
    if not performance_list:
        print("공연 데이터를 찾을 수 없습니다.")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    # DataFrame으로 변환
    df = pd.DataFrame(performance_list)
    print(f"{len(df)}개의 공연 데이터를 수집했습니다.")

    # 상세 데이터 추가
    detailed_df = add_detailed_info(df)
    print(f"상세 데이터 수집 완료: {len(detailed_df)}개의 데이터")

    return detailed_df
