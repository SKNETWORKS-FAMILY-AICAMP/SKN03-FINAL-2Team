import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import boto3

# AWS Parameter Store에서 환경 변수 가져오기
def get_param(parameter_name):
    ssm = boto3.client('ssm', region_name="ap-northeast-2")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']

API_KEY = get_param("KOPIS_API_KEY")
DETAIL_URL = "http://kopis.or.kr/openApi/restful/prfstsPrfByFct"

# 이후 기존 코드 유지...


# XML 데이터를 JSON으로 변환
def xml_to_json(xml_data):
    try:
        root = ET.fromstring(xml_data)
        json_result = []

        # XML 구조 파싱
        for child in root:
            entry = {element.tag: element.text for element in child}
            json_result.append(entry)

        return json_result
    except ET.ParseError:
        print("XML 파싱 오류가 발생했습니다.")
        return []

# 공연 추가 데이터 조회
def get_prfsts_by_fct(api_key, start_date, end_date, place):
    """
    공연의 장소, 기간에 따른 세부 정보를 조회
    """
    params = {
        "service": api_key,
        "cpage": 1,
        "rows": 100,
        "stdate": start_date,
        "eddate": end_date,
        "shprfnmfct": place
    }

    try:
        response = requests.get(DETAIL_URL, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"API 호출 실패: {e}")
        return ""

# 추가 데이터를 포함하는 DataFrame 생성
def add_additional_details(df):
    all_results = []
    for _, row in df.iterrows():
        try:
            result_xml = get_prfsts_by_fct(
                api_key=API_KEY,
                start_date=row["start_date"].replace(".", ""),
                end_date=row["end_date"].replace(".", ""),
                place=row["place"].split("(")[0].strip(),
            )
            result_json = xml_to_json(result_xml)
            for entry in result_json:
                entry["title"] = row["title"]  # 원본 제목 포함
                entry["id"] = row["id"]       # 원본 ID 포함
            all_results.extend(result_json)
        except Exception as e:
            print(f"추가 데이터 처리 오류: {e}")
        time.sleep(0.5)  # API 호출 간 딜레이

    # JSON 데이터를 DataFrame으로 변환
    if all_results:
        return pd.DataFrame(all_results)
    return pd.DataFrame()

# Main 함수
def main(musical_details_df):
    """
    추가 데이터를 수집하고 처리
    """
    print("추가 공연 데이터를 수집 중입니다...")
    detailed_df = add_additional_details(musical_details_df)

    if detailed_df.empty:
        print("추가 데이터를 수집할 수 없었습니다.")
        return musical_details_df

    print(f"총 {len(detailed_df)}개의 추가 데이터를 수집했습니다.")
    return detailed_df
