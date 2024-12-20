# main.py
from .musical_data.pipeline import api, charge, process


def main():
    """
    전체 워크플로우 실행: 
    1. API 호출로 공연 기본 데이터 수집
    2. 추가 데이터 수집
    3. 데이터 가공 및 S3 업로드
    """
    print("Step 1: API 호출로 기본 공연 데이터 수집")
    musical_details = api.main()

    if musical_details.empty:
        print("공연 데이터를 수집할 수 없습니다. 프로그램을 종료합니다.")
        return

    print("Step 2: 추가 데이터 수집")
    detailed_data = charge.main(musical_details)

    if detailed_data.empty:
        print("추가 데이터를 수집할 수 없습니다. 기본 데이터를 S3에 업로드합니다.")
        process.main(musical_details)
        return

    print("Step 3: 데이터 가공 및 S3 업로드")
    processed_data = process.main(detailed_data)

    print("모든 작업이 완료되었습니다.")

# 이 파일이 직접 실행될 경우 main() 호출
if __name__ == "__main__":
    main()
