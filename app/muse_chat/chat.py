from langgraph.graph import END, START, StateGraph

from muse_chat.chat_modules.condition import CheckAnswer, CheckSimilarity, Supervisor
from muse_chat.chat_modules.core import (
    EmbedderNode,
    JudgeNode,
    MongoAggregationNode,
    MongoRetrieverNode,
    Multi2HyDENode,
    PopularityRerankerNode,
    ReWriterNode,
    SimilarityRerankerNode,
    Single2HyDENode,
)
from muse_chat.chat_modules.state import GraphState
from shared.mongo_base import MongoBase


class MuseChatGraph:

    def __init__(self):
        self.vdb_collection = MongoBase.vector_db["Exhibition"]
        self.db_collection = MongoBase.db["Exhibition"]
        self.sub_graph = self.build_sub_graph()
        self.main_graph = self.build_main_graph()
        self.rewrite_graph = self.build_rewrite_graph()

    def build_sub_graph(self) -> StateGraph:
        sub_graph = StateGraph(GraphState)
        sub_graph.add_node("embedder", EmbedderNode())
        sub_graph.add_node(
            "retriever",
            MongoRetrieverNode(collection=self.vdb_collection),
        )
        sub_graph.add_node("similarity_reranker", SimilarityRerankerNode())
        sub_graph.add_node("popularity_reranker", PopularityRerankerNode())
        sub_graph.add_node(
            "aggregation",
            MongoAggregationNode(collection=self.db_collection),
        )

        sub_graph.add_edge("embedder", "retriever")
        sub_graph.add_edge("retriever", "similarity_reranker")
        sub_graph.add_edge("similarity_reranker", "aggregation")
        sub_graph.add_conditional_edges(
            "aggregation",
            CheckSimilarity(),
            {
                "high_similarity": "popularity_reranker",
                "low_similarity": END,
            },
        )
        sub_graph.add_edge("popularity_reranker", END)
        return sub_graph.compile()

    def build_main_graph(self) -> StateGraph:
        """
        LangGraph를 사용하여 노드들을 연결
        """

        main_graph = StateGraph(GraphState)
        main_graph.add_node("single2hyde", Single2HyDENode())
        main_graph.add_node("multi2hyde", Multi2HyDENode())
        main_graph.add_node("sub_graph", self.sub_graph)
        main_graph.add_node("judge", JudgeNode())
        main_graph.add_edge(START, "judge")
        main_graph.add_conditional_edges(
            "judge",
            CheckAnswer(),
            {
                "yes": END,
                "no": "multi2hyde",
            },
        )
        main_graph.add_conditional_edges(
            START,
            Supervisor(),
            {
                "single_modal_input": "single2hyde",
                "multi_modal_input": "multi2hyde",
            },
        )
        main_graph.add_edge("single2hyde", "sub_graph")
        main_graph.add_edge("multi2hyde", "sub_graph")
        main_graph.add_edge("sub_graph", END)

        # 그래프 컴파일
        return main_graph.compile()

    def build_rewrite_graph(self) -> StateGraph:
        rewrite_graph = StateGraph(GraphState)
        rewrite_graph.add_node("re_writer", ReWriterNode())
        rewrite_graph.add_node("sub_graph", self.sub_graph)

        rewrite_graph.add_edge(START, "re_writer")
        rewrite_graph.add_edge("re_writer", "sub_graph")
        rewrite_graph.add_edge("sub_graph", END)
        return rewrite_graph.compile()


def process_query(
    graph: StateGraph,
    query: str,
    images: list = None,
    chat_history: list = None,
    documents: list = None,
):
    """
    쿼리를 처리하고 응답을 반환
    """
    print("\n=== Process Query Start ===")
    print(f"Query: {query}")
    print(f"Images: {images[0]}")

    initial_state = {
        "query": query,
        "images": images or [],
        "chat_history": chat_history or [],
        "documents": documents or [],
    }
    print(f"Initial State: {initial_state}")

    # 일반 실행 모드 사용
    try:
        final_state = graph.invoke(initial_state)
        print(f"Final state: {final_state}")

        if isinstance(final_state, dict) and "response" in final_state:
            response = final_state["response"]
            print(f"Found response in final state: {response[:100]}...")
            yield response
        else:
            print(f"Unexpected final state type: {type(final_state)}")
            yield "응답을 처리하는 중 오류가 발생했습니다."
    except Exception as e:
        print(f"Error in process_query: {e}")
        yield "응답을 처리하는 중 오류가 발생했습니다."

    print("=== Process Query End ===\n")
