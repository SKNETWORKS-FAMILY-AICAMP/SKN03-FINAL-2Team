import pandas as pd
import os
import openai
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.callbacks.manager import get_openai_callback
from langchain_openai import OpenAI
from langchain.chat_models import ChatOpenAI
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config
from dotenv import load_dotenv


class GenreStoryUpdater:
    def __init__(self):
        self.total_charge = 0
        self.cnt = 0
        self.prompt_template = ChatPromptTemplate.from_template("""
        다음은 뮤지컬의 정보입니다:
        제목: {title}
        상영 위치: {place}
        출연진: {cast}
        포스터 URL: {poster}
        
        1. 이 뮤지컬의 장르를 '역사', '가족', '신화', '지역|창작', '대학로'  이 5가지 카테고리 중에서만 적절한 것을 한 개만 골라서 적어주세요.
        아래와 같은 형식으로 답변해주세요:
        장르: <장르>
        """)
        self.chat_model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=300,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

    def update_genre_and_story(self, df):
        for idx, row in df.iterrows():
            if pd.notnull(row['genre']):
                genre = row['genre']
            else:
                genre= self.get_genre_and_story(row)

            df.at[idx, "genre"] = genre

    def get_genre_and_story(self, row):
        
        if row['genre']:
            return row['genre']
        else:
            try:
                prompt = self.prompt_template.format_messages(
                    title=row['title'],
                    place=row['place'],
                    cast=row['cast'],
                    poster=row['poster']
                )
                
                with get_openai_callback() as cb: 
                    response = self.chat_model(prompt) 
                    content = response.content
                    
                    self.total_charge += cb.total_cost
                    self.cnt += 1
                    print(f"{self.cnt}: 호출에 청구된 총 금액(USD): \t${self.total_charge}")

                genre = content.split("장르: ")[1].split("\n")[0].strip()
                
                return genre
            except Exception as e:
                print(f"오류 발생: {e}")
                return "", ""

def main():
    # 파일 경로 설정
    add_genre_story_path = f'{config.file_path}/{config.add_genre_file_name}'
    processed_performance_details_path = f'{config.file_path}/{config.processed_performance_details}'
    
    # 파일 존재 여부 확인
    if os.path.exists(add_genre_story_path):
        df = pd.read_json(add_genre_story_path)
    else:
        # processed_perfomance_details.json -> 데이터프레임 생성
        df = pd.read_json(processed_performance_details_path)
        df['genre'] = None
        load_dotenv()
    updater = GenreStoryUpdater()
    updater.update_genre_and_story(df)

    # 파일 저장
    df.to_json(add_genre_story_path, orient='records', lines=True, force_ascii=False)

if __name__ == "__main__":
    main()