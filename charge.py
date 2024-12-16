import os
import requests
import json
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# .env 파일에 저장된 API 키 가져오기
KOPIS_API_KEY = os.getenv('KOPIS_API_KEY')

# API 호출 함수
def get_prfsts_by_fct(service, cpage, rows, stdate, eddate, shprfnmfct):
    base_url = "http://kopis.or.kr/openApi/restful/prfstsPrfByFct"
    
    # 요청 변수 정의
    params = {
        "service": service,
        "cpage": cpage,
        "rows": rows,
        "stdate": stdate,
        "eddate": eddate,
        "shprfnmfct": shprfnmfct,
    }
    
    # API 호출
    response = requests.get(base_url, params=params)
    
    # 결과 확인
    if response.status_code == 200:
        return response.text  # XML 형식의 결과 반환
    else:
        raise Exception(f"API 호출 실패: {response.status_code}, {response.text}")

# XML 데이터를 JSON으로 변환
def xml_to_json(xml_data):
    root = ET.fromstring(xml_data)
    json_result = []

    # XML 구조 파싱
    for child in root:
        entry = {element.tag: element.text for element in child}
        json_result.append(entry)
    
    return json_result

# JSON 파일 저장 함수
def save_json_to_file(json_data, folder_path, file_name):
    # 폴더가 없으면 생성
    os.makedirs(folder_path, exist_ok=True)
    
    # 파일 저장 경로 설정
    file_path = os.path.join(folder_path, file_name)
    
    # JSON 파일 저장
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

# JSON 파일 로드 함수
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

# main 함수 정의
def main():
    try:
        # JSON 파일에서 값 읽기
        data2 = load_json("musical_details.json")  # JSON 파일 경로 예시

        # 리스트인지 확인
        if not isinstance(data2, list):
            raise Exception("musical_details.json 파일 형식은 리스트여야 합니다.")

        # 저장 폴더 경로
        folder_path = "results"  # 저장할 폴더 이름

        # 모든 데이터 처리
        for item in data2:
            title = item["title"]
            start_date = item["start_date"].replace(".", "")  # 날짜 포맷 변경 (YYYYMMDD)
            end_date = item["end_date"].replace(".", "")      # 날짜 포맷 변경 (YYYYMMDD)
            place = item["place"]                            # place 값 가져오기
            
            # place 값 전처리: 괄호 이후 내용 제거
            processed_place = place.split("(")[0].strip()

            # API 호출
            result_xml = get_prfsts_by_fct(
                service=KOPIS_API_KEY, 
                cpage=1, 
                rows=100, 
                stdate=start_date, 
                eddate=end_date,
                shprfnmfct=processed_place,  # 전처리된 place 사용
            )
            
            # XML -> JSON 변환
            result_json = xml_to_json(result_xml)

            # API 결과에 title 추가
            for entry in result_json:
                entry["title"] = title  # title 추가

            # 파일명에서 사용할 수 없는 문자 제거
            safe_title = "".join(char for char in title if char.isalnum() or char in " _-").strip()

            # JSON 파일 저장
            file_name = f"{safe_title}.json"  # title 값을 파일명으로 사용
            save_json_to_file(result_json, folder_path, file_name)
        
    except Exception as e:
        print(e)

# 이 파일이 직접 실행될 경우 main() 호출
if __name__ == "__main__":
    main()
