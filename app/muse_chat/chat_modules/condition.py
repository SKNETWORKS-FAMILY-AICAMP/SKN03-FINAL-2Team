from chat_modules.base import Base
from chat_modules.state import GraphState


class Supervisor(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Supervisor"

    def process(self, state: GraphState) -> GraphState:
        return state


class CheckAnswer(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckAnswer"

    def process(self, state: GraphState) -> GraphState:
        return state


class CheckSimilarity(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "CheckSimilarity"

    def process(self, state: GraphState) -> GraphState:
        return state
