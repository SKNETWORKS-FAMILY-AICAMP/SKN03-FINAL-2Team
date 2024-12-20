import pandas as pd
import boto3
import os

# AWS Parameter Store에서 환경 변수 가져오기
def __set_api_key():
    if not os.environ.get("KOPIS_API_KEY"):
        ssm = boto3.client("ssm", region_name="ap-northeast-2")
        parameter = ssm.get_parameter(
            Name=f"/DEV/CICD/MUSEIFY/KOPIS_API_KEY", 
            WithDecryption=True
        )
        os.environ["KOPIS_API_KEY"] = parameter["Parameter"]["Value"]

# API 키 설정 실행
__set_api_key()

API_KEY = os.getenv("KOPIS_API_KEY")

# S3 클라이언트 초기화
s3 = boto3.resource('s3')
BUCKET_NAME = "musical-data"  # 버킷 이름을 문자열로 저장
bucket = s3.Bucket(BUCKET_NAME)  # 버킷 객체 생성

# S3 업로드 함수
def upload_df_to_s3_as_json(df, bucket, s3_file_key):
    """
    DataFrame을 JSON 형식으로 변환하여 S3에 업로드
    """
    try:
        # S3 폴더 확인 및 생성
        s3_folder = "/".join(s3_file_key.split("/")[:-1])
        if s3_folder:
            bucket.put_object(Key=(s3_folder + "/"))

        # 모든 데이터를 JSON으로 변환
        json_data = df.to_json(orient="records", force_ascii=False, indent=4)
        bucket.put_object(Body=json_data, Key=s3_file_key)
        print(f"S3 업로드 성공: {BUCKET_NAME}/{s3_file_key}")
    except Exception as e:
        print(f"S3 업로드 실패: {e}")

# 데이터 가공 함수
# 데이터 가공 함수
def process_data(df):
    """
    데이터를 정제하고 필요한 컬럼 추가 (모든 데이터 유지)
    """
    print("데이터 가공 중...")

    # Step 1: 숫자형 변환
    df['totnmrs'] = pd.to_numeric(df['totnmrs'], errors='coerce')
    df['prfdtcnt'] = pd.to_numeric(df['prfdtcnt'], errors='coerce')
    df['seatcnt'] = pd.to_numeric(df['seatcnt'], errors='coerce')

    # Step 2: 결측값 제거
    df = df.dropna(subset=['totnmrs', 'prfdtcnt', 'seatcnt'])

    # Step 3: 점유율(percentage) 계산 (loc 사용)
    df.loc[:, 'percentage'] = ((df['totnmrs'] / (df['prfdtcnt'] * df['seatcnt'])) * 100).round(2)

    # Step 4: 결측값 추가 제거
    df = df.dropna(subset=['percentage'])

    print(f"가공 완료: 총 {len(df)}개의 데이터")
    return df


# Main 함수
def main(detailed_df):
    """
    추가 데이터를 처리하고 최종 JSON 형식으로 S3에 업로드
    """
    # 데이터 가공
    processed_df = process_data(detailed_df)

    # S3 업로드
    s3_file_key = "results/per+raw.json"
    upload_df_to_s3_as_json(processed_df, bucket, s3_file_key)  # bucket 객체 전달

    print("데이터 처리 및 업로드 완료.")
    return processed_df

# 이 파일이 직접 실행될 경우 main() 호출
if __name__ == "__main__":
    print("이 스크립트는 다른 모듈에서 호출되어야 합니다.")
