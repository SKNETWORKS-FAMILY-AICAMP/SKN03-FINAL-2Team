import pandas as pd
import numpy as np
import pickle
from DeepFM import weighted_loss, FMInteraction
from tensorflow.keras.models import load_model
from datetime import datetime   
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config


class Recommender:
    def __init__(self):
        self.model = None
        self.data = None
        self.reference_data = None
        self.label_encoders = {}

    def load_model(self):
        """모델 로드"""
        try:
            self.model = load_model(config.save_model_path, custom_objects={
                "weighted_loss": weighted_loss,
                "FMInteraction": FMInteraction
            })
        except FileNotFoundError:
            raise FileNotFoundError("저장된 모델을 찾을 수 없음")

    def load_data(self):
        """데이터 로드"""
        try:
            self.data = pd.read_json(config.df_with_negatives_path, lines=True)
            # 레이블 인코더 로드
            for column in ['title', 'cast', 'genre']:
                self.label_encoders[column] = {val: idx for idx, val in enumerate(self.data[column].unique())}
        except FileNotFoundError:
            raise FileNotFoundError("데이터 파일을 찾을 수 없음")
        
    def load_reference_data(self):
        """기준 데이터 로드"""
        try:
            self.reference_data = pd.read_json(f"{config.file_path}/{config.add_genre_file_name}", lines=True)
        except FileNotFoundError:
            raise FileNotFoundError("기준 파일을 찾을 수 없습니다.")    

    def recommend(self, cast, genre):
        print(f"Debug: 입력된 cast - {cast}")
        print(f"Debug: 입력된 genre - {genre}")

        cast_encoded = self.label_encoders['cast'][cast]
        genre_encoded = self.label_encoders['genre'][genre]
        
        # 데이터셋 전체를 사용하여 예측
        X = self.data[['title', 
                    'cast',
                    'genre', 
                    # 'percentage',
                    # 'ticket_price'
                    ]].copy()
        title_encoder = self.label_encoders['title']
        cast_encoder = {v: k for k, v in self.label_encoders['cast'].items()}
        genre_encoder = {v: k for k, v in self.label_encoders['genre'].items()}
        
        # 데이터 인코딩
        X['title'] = X['title'].map(title_encoder)
        X['cast'] = X['cast'].map(self.label_encoders['cast'])
        X['genre'] = X['genre'].map(self.label_encoders['genre'])
        # 중복 제거
        X = X.drop_duplicates(subset=['title', 'cast', 'genre'])
        
        predictions = self.model.predict([X['title'].values, 
                                        X['cast'].values, 
                                        X['genre'].values,
                                        # X['percentage'].values,
                                        # X['ticket_price'].values,
                                          ])
        X['predicted_score'] = predictions

        # 입력된 장르로 필터링
        genre_filtered_data = X[X['genre'] == genre_encoded]
        cast_filtered_data = X[X['cast'] == cast_encoded]

        # 1. 장르 기반 추천 10개
        genre_top_titles = genre_filtered_data.sort_values(by='predicted_score', ascending=False).head(15)
        # 2. 배우 기반 추천 10개
        cast_top_titles = cast_filtered_data.sort_values(by='predicted_score', ascending=False).head(15)
        # 3. 병합 후 중복 제거
        combined_titles = pd.concat([genre_top_titles, cast_top_titles])
        # 4. 예측 점수 기준으로 정렬
        top_titles = combined_titles.sort_values(by='predicted_score', ascending=False)
        # 디코딩
        top_titles['decoded_title'] = top_titles['title'].map({v: k for k, v in title_encoder.items()})
        top_titles['decoded_genre'] = top_titles['genre'].map({v: k for k, v in genre_encoder.items()})
        top_titles['decoded_cast'] = top_titles['cast'].map(cast_encoder)
        
        # [ ] 제거 및 중복 처리
        top_titles['clean_title'] = top_titles['decoded_title'].str.replace(r'\[.*?\]', '', regex=True).str.strip()
        top_titles = top_titles.drop_duplicates(subset=['clean_title'])

        matched_recommendations = self.reference_data[self.reference_data['title'].isin(top_titles['clean_title'])]
        matched_recommendations.loc[:, 'clean_title'] = matched_recommendations['title'].str.replace(r'\[.*?\]', '', regex=True).str.strip()
        matched_recommendations = matched_recommendations.drop_duplicates(subset=['clean_title'])

        # 최종 데이터 결합
        final_recommendations = matched_recommendations.merge(
            top_titles[['clean_title', 'predicted_score']],
            on='clean_title'
        ).sort_values(by='predicted_score', ascending=False)

        # 10개 미만이면 필터링되지 않은 데이터 중 추가
        if len(final_recommendations) < 10:
            missing_count = 10 - len(final_recommendations)
            # 이미 포함된 데이터 제외
            excluded_titles = final_recommendations['title'].tolist() + genre_top_titles['title'].tolist() + cast_top_titles['title'].tolist()
            unfiltered_data = self.data[~self.data['title'].isin(excluded_titles)]
            # top_titles와 unfiltered_data 매칭
            matched_data = unfiltered_data.merge(
                top_titles[['decoded_title', 'predicted_score']],
                left_on='title',
                right_on='decoded_title'
            ).drop_duplicates(subset=['title'])
            
            # 추가할 데이터
            additional_recommendations = matched_data.sort_values(by='predicted_score', ascending=False).head(missing_count)
            matched_reference_data = self.reference_data[
                self.reference_data['title'].str.contains('|'.join(additional_recommendations['title']), na=False)
            ]
            # 중복 제거를 위한 임시 컬럼
            matched_reference_data['clean_title'] = matched_reference_data['title'].str.replace(r'\[.*?\]', '', regex=True).str.strip()

            # 'clean_title' 기준으로 중복 제거 (첫 번째로 나온 데이터만 유지)
            matched_reference_data = matched_reference_data.drop_duplicates(subset=['clean_title'])

            score_mapping = dict(zip(additional_recommendations['title'], additional_recommendations['predicted_score']))
            matched_reference_data['predicted_score'] = matched_reference_data['clean_title'].map(score_mapping)            

            # 'clean_title' 컬럼 삭제
            matched_reference_data = matched_reference_data.drop(columns=['clean_title'])

            # 최종 결합
            final_recommendations = pd.concat([final_recommendations, matched_reference_data]).sort_values(by='predicted_score', ascending=False).head(10)

        # 10개만 반환하도록 처리
        final_recommendations = final_recommendations.head(10).iloc[::-1]

        # 결과 출력
        return final_recommendations[['poster', 'title', 'place', 'cast', 'genre', 'ticket_price']]

        """콘솔 테스트용 출력 코드"""    
        # return final_recommendations[['title', 'genre', 'cast', 'predicted_score']]            

    def score(self, cast, genre):
        # 1. 데이터 인코딩
        cast_encoded = self.label_encoders['cast'].get(cast, -1)
        genre_encoded = self.label_encoders['genre'].get(genre, -1)

        if cast_encoded == -1 or genre_encoded == -1:
            return []

        X = self.data.copy()
        title_encoder = self.label_encoders['title']

        X['title'] = X['title'].map(title_encoder)
        X['cast'] = X['cast'].map(self.label_encoders['cast'])
        X['genre'] = X['genre'].map(self.label_encoders['genre'])
        
        # NaN 제거
        X = X.dropna(subset=['title', 'cast', 'genre'])
        
        # 2. 모델 예측
        try:
            predictions = self.model.predict([X['title'].values, 
                                            X['cast'].values, 
                                            X['genre'].values])
            X['predicted_score'] = predictions
        except Exception as e:
            print(f"[ERROR] 모델 예측 중 오류 발생: {e}")
            return []

        # 3. 현재 상영 중인 데이터 필터링
        current_date = datetime.now().strftime('%Y.%m.%d')
        active_data = self.reference_data[self.reference_data["end_date"] > current_date]
        active_titles = set(active_data["title"])

        # 4. 점수가 계산된 데이터와 상영 중인 데이터 매칭
        X = X[X['title'].isin([title_encoder.get(title, -1) for title in active_titles])]
        
        if X.empty:
            print("[DEBUG] 현재 상영 중인 타이틀이 없습니다.")
            return []

        # 5. 상위 5개 타이틀 반환
        top_recommendations = X.sort_values(by="predicted_score", ascending=False).head(7)
        top_titles = top_recommendations['title'].map({v: k for k, v in title_encoder.items()}).tolist()
        print("[DEBUG] Top 7 Recommended Titles:", top_titles)
        return top_titles


"""테스트 입력"""
if __name__ == "__main__":
    # recommender = Recommender()
    # recommender.load_model()
    # recommender.load_data()
    # recommender.load_reference_data()

    # cast = "정성화"
    # genre = "음악중심/주크박스"
    # recommendations = recommender.recommend(cast, genre)
    # print(recommendations)
    pass
