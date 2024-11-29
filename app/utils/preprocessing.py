import json
import pandas as pd
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

    def preprocessing_data(self):

        # 장르 처리: '중' 키워드 포함 시 마지막 장르 선택
        def extract_final_genre(genre):
            if genre == '창작':
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
        df_selected = df_expanded[["cast", "title", "genre", "percentage"]]

        # # percentage 컬럼 정규화 (0과 1 사이 값으로 스케일링)
        min_percentage = df_selected['percentage'].min()
        max_percentage = df_selected['percentage'].max()
        df_selected['percentage'] = (df_selected['percentage'] - min_percentage) / (max_percentage - min_percentage)
        df_selected['percentage'] = df_selected['percentage'].round(4)
        # '등'을 제거하고 공백을 제거
        df_selected['cast'] = df_selected['cast'].str.replace('등', '', regex=False).str.strip()

        df_selected['target'] = 1
        
        # 1. target=1인 데이터만 필터링
        positive_df = df_selected[df_selected['target'] == 1]

        # 2. 전체 영화 목록 추출 (중복 제거)
        all_movies = df_selected[['title', 'genre']].drop_duplicates()

        # 3. 부정 샘플을 위한 빈 리스트 생성

        positive_count = len(positive_df)
        max_negative_samples = positive_count * 4
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
            
            # negative sampling: 배우가 등장하지 않은 영화에 대해 target=0
            # `4배`만큼 랜덤 샘플링
            # non_cast_movies_sampled = non_cast_movies.sample(
            #     n=len(movies_played_by_cast) * 4, 
            #     random_state=42, 
            #     replace=True)]

            non_cast_movies_sampled = non_cast_movies.sample(
                n=min(len(non_cast_movies), max_negative_samples),
                random_state=42,
                replace=False
            )

            # 샘플링된 영화와 그에 해당하는 배우 및 target=0을 negative_samples에 추가
            for _, movie_row in non_cast_movies_sampled.iterrows():
                if len(negative_samples) >= max_negative_samples:
                    break  # 최대 개수를 초과하면 중단
                negative_samples.append({
                    'cast': cast, 
                    'title': movie_row['title'], 
                    'genre': movie_row['genre'], 
                    'percentage': movie_row['percentage'] if not pd.isna(movie_row['percentage']) else 0,
                    'target': 0
                })

        # 5. negative_samples 리스트로부터 새로운 DataFrame 생성
        negative_df = pd.DataFrame(negative_samples)

        # 6. 기존 DataFrame과 negative samples DataFrame을 합침
        df_with_negatives = pd.concat([df_selected, negative_df], ignore_index=True)

        df_with_negatives.to_json(config.df_with_negatives_path, orient='records', lines=True, force_ascii=False)

    def run(self):
        self.load_data()
        self.preprocessing_data()



if __name__ == "__main__":
    preprocessing_instance = Preprocessing()
    preprocessing_instance.run()