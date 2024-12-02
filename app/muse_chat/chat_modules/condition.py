from muse_chat.chat_modules.base import Base
from muse_chat.chat_modules.state import GraphState


class Supervisor(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Supervisor"

    def process(self, state: GraphState) -> str:
        if state["images"]:
            return "multi_modal_input"
        return "single_modal_input"


class CheckSimilarity(Base):
    def __init__(self, threshold=0.7, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckSimilarity"
        self.threshold = threshold

    def process(self, state: GraphState) -> str:
        # reranked_documents의 점수 확인
        scores = [doc.get("score", 0) for doc in state["reranked_documents"]]
        max_score = max(scores) if scores else 0

        print(f"CheckSimilarity - Max Score: {max_score}, Threshold: {self.threshold}")

        # 임계값을 넘는 문서가 있는지 확인
        if max_score >= self.threshold:
            return "high_similarity"
        return "low_similarity"


class CheckAnswer(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckAnswer"

    def process(self, state: GraphState) -> str:
        return state.get("answer_type", "revise")
