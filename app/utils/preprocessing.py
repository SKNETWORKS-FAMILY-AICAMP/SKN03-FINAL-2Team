import json
import pandas as pd
import numpy as np
import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

class Preprocessing:
    def __init__(self):
        self.data_list = []
        self.df = None

    def load_data(self):
        data_list = []
        # JSON 파일 한 줄씩 읽어서 처리
        with open(f'{config.file_path}/{config.add_genre_file_name}', 'r', encoding='utf-8-sig') as file:
            for line in file:
                # 한 줄의 JSON 문자열을 딕셔너리로 변환
                data = json.loads(line.strip())
                data_list.append(data)  # 리스트에 추가

        # 리스트를 DataFrame으로 변환
        self.df = pd.DataFrame(data_list)
    
    def extract_ticket_price(self, ticket_price):
        """ticket_price 컬럼 처리 로직"""
        # 1. 전석 무료 처리
        if "전석 무료" in ticket_price:
            return 0
        # 2. 전석 + 단일 가격 처리
        elif "전석" in ticket_price:
            match = re.search(r'(\d+),?\d*원', ticket_price)
            if match:
                return int(match.group(1).replace(",", ""))
        # 3. 여러 좌석 가격 처리
        else:
            prices = re.findall(r'석\s*(\d+),?\d*원', ticket_price)
            if prices:
                prices = [int(price.replace(",", "")) for price in prices]
                return sum(prices) / len(prices)  # 평균 계산
        return None  # 기본값 (가격이 없는 경우)
    
    def normalize_column(self, column, min_value=None, max_value=None):
        """로그 변환 및 0~1 정규화"""
            # 최소/최대값 지정
        if min_value is None:
            min_value = column.min()
        if max_value is None:
            max_value = column.max()

        # 값이 모두 동일한 경우 처리 (분모가 0이 되는 경우 방지)
        if min_value == max_value:
            return pd.Series(0.001, index=column.index)  # 동일값이면 최소값 반환

        # 정규화
        normalized = 0.001 + (column - min_value) / (max_value - min_value) * (1 - 0.001)

        # 소수점 4자리로 반올림
        return normalized.round(4)


    def preprocessing_data(self):

        # 장르 처리: '중' 키워드 포함 시 마지막 장르 선택
        def extract_final_genre(genre):
            if genre == '연애' or genre == '미스터리' or genre == '가요뮤지컬' or genre == '창작':
                    return "대학로"
            
            if genre == '부산북구':
                    return "지역|창작"
            
            return genre
        
        self.df['genre'] = self.df['genre'].apply(extract_final_genre)
        # cast 열을 쉼표로 나누고 행으로 확장
        self.df["cast_split"] = self.df["cast"].str.split(", ")  # 쉼표로 분리
        df_expanded = self.df.explode("cast_split").reset_index(drop=True)  # 행으로 확장

        # cast_split 열 이름을 cast로 덮어쓰기
        df_expanded["cast"] = df_expanded["cast_split"]
        df_expanded = df_expanded.drop(columns=["cast_split"])

        # 필요한 열만 선택
        df_selected = df_expanded[["cast", 
                                "title", 
                                "genre", 
                                "percentage",
                                "ticket_price"
                                ]]

        # '등'을 제거하고 공백을 제거
        df_selected['cast'] = df_selected['cast'].str.replace('등', '', regex=False).str.strip()

        # 1. target=1인 데이터만 필터링
        df_selected['target'] = 1
        positive_df = df_selected[df_selected['target'] == 1]


        cast_counts = positive_df.groupby('cast')['target'].count()
        # target=1 데이터가 5개 이상인 배우만 필터링
        valid_casts = cast_counts[cast_counts >= 5].index
        positive_df = positive_df[positive_df['cast'].isin(valid_casts)]

        # 2. 전체 영화 목록 추출 (중복 제거)
        all_movies = df_selected[['title', 'genre']].drop_duplicates()

        # ticket_price 처리 및 컬럼 추가
        df_selected['processed_ticket_price'] = df_selected['ticket_price'].apply(self.extract_ticket_price)

        # ticket_price 정규화
        df_selected['normalized_ticket_price'] = self.normalize_column(
            df_selected['processed_ticket_price'].fillna(0),  # 결측값 처리
            min_value=df_selected['processed_ticket_price'].min(),
            max_value=df_selected['processed_ticket_price'].max()
        )
        # 'ticket_price' 컬럼에 normalized 값을 덮어쓰기
        positive_df['ticket_price'] = df_selected.loc[
            df_selected['target'] == 1, 'normalized_ticket_price'
        ].round(4)
        # 중간 컬럼 제거
        df_selected = df_selected.drop(columns=['normalized_ticket_price', 'processed_ticket_price'])
        
         # percentage 값이 20 미만인 데이터 제거
        df_selected = df_selected[df_selected['percentage'] >= 20]

        # percentage 정규화
        df_selected['percentage'] = self.normalize_column(
            df_selected['percentage'].fillna(0),  # 결측값 처리
            min_value=df_selected['percentage'].min(),
            max_value=df_selected['percentage'].max()
        )
        positive_df['percentage'] = df_selected.loc[
            df_selected['target'] == 1, 'percentage'
        ]
        
        all_movies = df_selected.groupby(['title', 'genre'], as_index=False).first()
        
        negative_samples = []
        # 4. 각 배우에 대해 해당 배우가 등장한 영화 외의 영화들에 대해 target=0으로 샘플 생성
        for _, row in positive_df.iterrows():
            cast = row['cast']
            movies_played_by_cast = positive_df[positive_df['cast'] == cast]['title'].unique()
            genres_played_by_cast = positive_df[positive_df['cast'] == cast]['genre'].unique()

            # 해당 배우가 등장하지 않은 영화들 중 장르가 동일하지 않은 영화만
            non_cast_movies = all_movies[
                ~all_movies['title'].isin(movies_played_by_cast) &
                ~all_movies['genre'].isin(genres_played_by_cast)
            ]
            
            # 긍정 샘플 수에 따라 부정 샘플 수 결정
            positive_count_for_cast = len(movies_played_by_cast)
            max_negative_samples_for_cast = positive_count_for_cast * 4

            # 부정 샘플링 (필요한 만큼만)
            non_cast_movies_sampled = non_cast_movies.sample(
                n=min(len(non_cast_movies), max_negative_samples_for_cast),
                random_state=42,
                replace=False
            )

            # 샘플링된 영화 데이터를 negative_samples에 추가
            for _, movie_row in non_cast_movies_sampled.iterrows():
                matching_movie = all_movies[
                    (all_movies['title'] == movie_row['title']) &
                    (all_movies['genre'] == movie_row['genre']) &
                    (all_movies['percentage'] == movie_row['percentage'])
                ]
                normalized_ticket_price = matching_movie['ticket_price'].iloc[0] if not matching_movie.empty else 0.01

                negative_samples.append({
                    'cast': cast,
                    'title': movie_row['title'],
                    'genre': movie_row['genre'],
                    'percentage': movie_row['percentage'] if not pd.isna(movie_row['percentage']) else 0,
                    'ticket_price': normalized_ticket_price,
                    'target': 0
                })

        # Negative samples DataFrame 생성
        negative_df = pd.DataFrame(negative_samples)

        # Positive와 Negative 데이터 결합
        df_with_negatives = pd.concat([positive_df, negative_df], ignore_index=True)

        # 최종 비율 확인
        positive_count = len(df_with_negatives[df_with_negatives['target'] == 1])
        negative_count = len(df_with_negatives[df_with_negatives['target'] == 0])

        print(f"Positive count: {positive_count}, Negative count: {negative_count}")
        if negative_count > positive_count * 4:
            print("Too many negative samples. Adjusting to 1:4 ratio.")
            df_with_negatives = pd.concat([
                positive_df,
                negative_df.sample(
                    n=positive_count * 4,
                    random_state=42
                )
            ], ignore_index=True)

        # 결과 저장
        df_with_negatives.to_json(config.df_with_negatives_path, orient='records', lines=True, force_ascii=False)

    def run(self):
        self.load_data()
        self.preprocessing_data()



if __name__ == "__main__":
    preprocessing_instance = Preprocessing()
    preprocessing_instance.run()