from langgraph.graph import END, START, StateGraph

from muse_chat.chat_modules.condition import CheckAnswer, CheckSimilarity, Supervisor
from muse_chat.chat_modules.core import (
    EmbedderNode,
    HumanNode,
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


def build_graph() -> StateGraph:
    """
    LangGraph를 사용하여 노드들을 연결
    """
    vdb_collection = MongoBase.vector_db["Exhibition"]
    db_collection = MongoBase.db["Exhibition"]

    graph = StateGraph(GraphState)
    graph.add_node("single2hyde", Single2HyDENode())
    graph.add_node("multi2hyde", Multi2HyDENode())
    graph.add_node("embedder", EmbedderNode())
    graph.add_node(
        "retriever",
        MongoRetrieverNode(collection=vdb_collection),
    )
    graph.add_node("similarity_reranker", SimilarityRerankerNode())
    graph.add_node("popularity_reranker", PopularityRerankerNode())
    graph.add_node(
        "aggregation",
        MongoAggregationNode(collection=db_collection),
    )
    # graph.add_node("re_writer", ReWriterNode())
    # graph.add_node("human", HumanNode())

    graph.add_conditional_edges(
        START,
        Supervisor(),
        {
            "single_modal_input": "single2hyde",
            "multi_modal_input": "multi2hyde",
        },
    )
    graph.add_edge("single2hyde", "embedder")
    graph.add_edge("multi2hyde", "embedder")
    graph.add_edge("embedder", "retriever")
    graph.add_edge("retriever", "similarity_reranker")
    graph.add_edge("similarity_reranker", "aggregation")
    graph.add_conditional_edges(
        "aggregation",
        CheckSimilarity(),
        {
            "high_similarity": "popularity_reranker",
            "low_similarity": END,
        },
    )

    graph.add_edge("popularity_reranker", END)
    # graph.add_edge("popularity_reranker", "human")

    # graph.add_conditional_edges(
    #     "human",
    #     CheckAnswer(),
    #     {
    #         "accept": END,
    #         "revise": "re_writer",
    #     },
    # )
    # graph.add_edge("re_writer", "retriever")

    # 그래프 컴파일
    return graph.compile()


def process_query(
    graph: StateGraph,
    query: str,
    images: list = None,
    chat_history: list = None,
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
