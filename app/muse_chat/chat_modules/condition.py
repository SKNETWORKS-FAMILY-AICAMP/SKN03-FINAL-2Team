from muse_chat.chat_modules.base import Base
from muse_chat.chat_modules.state import GraphState


class Supervisor(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Supervisor"

    def process(self, state: GraphState) -> str:
        if state["image"]:
            return "multi_modal_input"
        return "single_modal_input"


class CheckSimilarity(Base):
    def __init__(self, threshold=0.7, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckSimilarity"
        self.threshold = threshold

    def process(self, state: GraphState) -> str:
        try:
            # 점수 정보에서 최대 점수 확인
            max_score = state["scoring_info"].get("max_score", 0)
            print(
                f"CheckSimilarity - Max Score: {max_score}, Threshold: {self.threshold}"
            )

            # 임계값을 넘는지 확인
            if max_score >= self.threshold:
                return "high_similarity"
            return "low_similarity"
        except Exception as e:
            print(f"Error in CheckSimilarity: {e}")
            return "low_similarity"


class CheckAnswer(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckAnswer"

    def process(self, state: GraphState) -> str:
        judge_answer = state.get("judge_answer", "No")
        if judge_answer == "No":
            return "no"
        return "yes"
