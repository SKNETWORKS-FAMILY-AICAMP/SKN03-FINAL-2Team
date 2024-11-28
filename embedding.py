from langchain_upstage import UpstageEmbeddings
import numpy as np
import os
import json
from dotenv import load_dotenv

class TextEmbedding:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('UPSTAGE_API_KEY')
        
        self.embedder = UpstageEmbeddings(
            api_key=api_key,
            model="embedding-passage"
        )
        
        # JSON 파일 읽기
        with open('./data/exhibition_data.json', 'r', encoding='utf-8') as f:
            self.exhibitions = json.load(f)

    def get_embedding(self, text: str) -> np.ndarray:
        try:
            embedding = np.array(self.embedder.embed_query(text))
            return embedding.tolist()  # numpy array를 list로 변환
        except Exception as e:
            print(f"임베딩 오류: {str(e)}")
            return None
            
    def get_all_embeddings(self):
        embeddings = []
        for exhibition in self.exhibitions:
            context = exhibition.get('E_context', '')
            if context:  # E_context가 비어있지 않은 경우만 처리
                embedding = self.get_embedding(context)
                embeddings.append({
                    'E_text': context,  # E_context를 text 값으로 저장
                    'E_embedding': embedding
                })
        
        # JSON 파일을 data 폴더에 저장
        with open('./data/exhibition_embeddings.json', 'w', encoding='utf-8') as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=2)
            
        return embeddings

# 사용 예시
if __name__ == "__main__":
    embedder = TextEmbedding()
    embeddings = embedder.get_all_embeddings()