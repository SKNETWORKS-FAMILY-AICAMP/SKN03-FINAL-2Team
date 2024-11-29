import json
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config


class F_Preprocessing:
    def __init__(self):
        self.data_list = []
        self.df = None
        self.processed_data = f'{config.file_path}/{config.processed_data}'
        self.columns_to_drop = config.columns_to_drop

    def load_data(self):
        data_list = []
        # JSON 파일 한 줄씩 읽어서 처리
        with open(f'{config.file_path}/{config.per_raw}', 'r', encoding='utf-8-sig') as file:
            for line in file:
                # 한 줄의 JSON 문자열을 딕셔너리로 변환
                data = json.loads(line.strip())
                data_list.append(data)  # 리스트에 추가

        # 리스트를 DataFrame으로 변환
        self.df = pd.DataFrame(data_list)

    def preprocessing_data(self):
        
        # 컬럼 삭제
        data = data.drop(columns=self.columns_to_drop)
        # child 값이 'Y'가 아닌 데이터만 필터링
        data = data[data['child'] != 'Y']
        data = data.dropna()
        data['percentage'] = pd.to_numeric(data['percentage'], errors='coerce')  # 값이 문자열일 경우 처리
        data = data[data['percentage'] <= 100]
        # 전처리된 데이터를 새로운 JSON 파일로 저장
        data.to_json(self.processed_data, orient='records', force_ascii=False, lines=True)
        print(f"전처리된 데이터가 {self.processed_data}에 저장되었습니다.")

    def run(self):
        self.load_data()
        self.preprocessing_data()



if __name__ == "__main__":
    preprocessing_instance = F_Preprocessing()
    preprocessing_instance.run()