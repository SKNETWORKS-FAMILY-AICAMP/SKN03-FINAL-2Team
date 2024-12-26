from langchain_upstage import UpstageEmbeddings
import numpy as np
import json
import logging
from ..utils.paramstore import ParameterStore

class TextEmbedding:
    def __init__(self):
        self.setup_embedder()
        self.setup_logging()

    def setup_embedder(self):
        try:
            api_key = ParameterStore.get_parameter('UPSTAGE_API_KEY')
            self.embedder = UpstageEmbeddings(
                api_key=api_key,
                model="embedding-passage"
            )
        except Exception as e:
            logging.error(f"임베더 설정 중 오류 발생: {str(e)}")
            raise

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_embedding(self, text: str) -> np.ndarray:
        try:
            self.logger.info(f"텍스트 임베딩 처리 중 (길이: {len(text)}자)")
            embedding = np.array(self.embedder.embed_query(text))
            self.logger.info(f"임베딩 생성 완료 (차원: {embedding.shape})")
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"임베딩 오류: {str(e)}")
            return None
    def get_all_embeddings(self):
        embeddings = []
        total = len(self.exhibitions)
        
        self.logger.info(f"\n전체 {total}개 전시회 임베딩 처리 시작")
        
        for idx, exhibition in enumerate(self.exhibitions, 1):
            context = exhibition.get('E_context', '')
            if context:
                self.logger.info(f"\n[{idx}/{total}] '{exhibition.get('E_title', '제목 없음')}' 임베딩 처리 중...")
                embedding = self.get_embedding(context)
                if embedding:
                    embeddings.append({
                        'E_text': context,
                        'E_embedding': embedding
                    })
                    self.logger.info(f"임베딩 처리 완료")
            else:
                self.logger.warning(f"[{idx}/{total}] '{exhibition.get('E_title', '제목 없음')}' - 컨텍스트 없음, 건너뜀")

        self._save_embeddings(embeddings)
        return embeddings

    def _save_embeddings(self, embeddings):
        output_path = './data/exhibition_embeddings.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=2)
        self.logger.info(f"\n임베딩 처리 완료. 총 {len(embeddings)}개의 임베딩이 {output_path}에 저장됨")

# 사용 예시
if __name__ == "__main__":
    embedder = TextEmbedding()
    embeddings = embedder.get_all_embeddings()
