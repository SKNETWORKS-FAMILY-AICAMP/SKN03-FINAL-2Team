from chat_modules.condition import CheckAnswer, CheckSimilarity, Supervisor
from chat_modules.core import (
    EmbedderNode,
    HumanNode,
    HyDENode,
    MongoAggregationNode,
    MongoRetrieverNode,
    PopularityRerankerNode,
    ReWriterNode,
    SimilarityRerankerNode,
    Supervisor,
)
from chat_modules.state import GraphState
from langgraph.graph import END, START, StateGraph


def build_graph(self) -> StateGraph:
    """
    LangGraph를 사용하여 노드들을 연결
    """
    graph = StateGraph(GraphState)

    graph.add_node("hyde", HyDENode())
    graph.add_node("embedder", EmbedderNode())
    graph.add_node("retriever", MongoRetrieverNode())
    graph.add_node("similarity_reranker", SimilarityRerankerNode())
    graph.add_node("popularity_reranker", PopularityRerankerNode())
    graph.add_node("aggregation", MongoAggregationNode())
    graph.add_node("re_writer", ReWriterNode())
    graph.add_node("human", HumanNode())

    graph.add_edge(START, "supervisor")
    graph.add_edge(START, "supervisor")
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
    graph.add_edge("popularity_reranker", "human")
    graph.add_conditional_edges(
        "human",
        CheckAnswer(),
        {
            "accept": END,
            "revise": "re_writer",
        },
    )
    graph.add_edge("re_writer", "retriever")

    # 그래프 컴파일
    return graph.compile()


def process_query(graph: StateGraph, query: str, chat_history: list):
    """
    쿼리를 처리하고 응답을 스트리밍 형식으로 반환
    """
    initial_state = {"query": query, "chat_history": chat_history}

    # LangGraph의 메시지 스트리밍 모드 사용
    for message, metadata in graph.stream(initial_state, stream_mode="messages"):
        # generator 노드의 응답만 스트리밍
        if metadata["langgraph_node"] == "generator":
            yield message.content
