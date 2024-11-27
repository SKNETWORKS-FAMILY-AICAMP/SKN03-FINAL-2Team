from typing import Dict

from langgraph.graph import END, START, StateGraph
from nodes.core import HyDENode
from nodes.state import GraphState


class VadaRAG:
    def __init__(
        self,
        openai_api_key: str,
        upstage_api_key: str,
        cohere_api_key: str,
        mongo_connection: str,
    ):
        # 그래프 구성
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        LangGraph를 사용하여 노드들을 연결
        """
        graph = StateGraph(GraphState)
        graph.add_node("hyde", HyDE())
        graph.add_node("embedder", Embedder())
        graph.add_node("retriever", Retriever())
        graph.add_node("reranker", Reranker())
        graph.add_node("supervisor", Supervisor())
        graph.add_node("similarity_reranker", SimilarityReranker())
        graph.add_node("popularity_reranker", PopularityReranker())
        graph.add_node("aggregation", Aggregation())
        graph.add_node("re_writer", ReWriter())

        graph.add_edge(START, "supervisor")
        graph.set_entry_point("supervisor")
        graph.add_conditional_edges(
            "supervisor",
            Supervisor(),
            {
                "condition1": "multi_modal",
                "condition2": "single_modal",
            },
        )
        graph.add_edge("multi_modal_hyde", "embedder")
        graph.add_edge("single_modal_hyde", "embedder")
        graph.add_edge("embedder", "retriever")
        graph.add_edge("retriever", "similarity_reranker")
        graph.add_edge("similarity_reranker", "check_similarity")
        graph.set_entry_point("check_similarity")
        graph.add_conditional_edges(
            "check_similarity",
            CheckSimilarity(),
            {
                "condition1": "aggregation",
                "condition2": "no_result",
            },
        )
        graph.add_edge("no_result", END)
        graph.add_edge("aggregation", "popularity_reranker")
        graph.set_entry_point("check_answer")
        graph.add_conditional_edges(
            "check_answer",
            CheckAnswer(),
            {
                "condition1": END,
                "condition2": "re_writer",
            },
        )
        graph.add_edge("re_writer", "retriever")

        # 그래프 컴파일
        return graph.compile()

    def process_query(self, query: str, chat_history: list = None) -> Dict[str, Any]:
        initial_state = GraphState(
            query=query,
            chat_history=chat_history or [],
            hypothetical_doc="",
            embedding=[],
            documents=[],
            reranked_documents=[],
            response="",
        )

        return self.graph.invoke(initial_state)
