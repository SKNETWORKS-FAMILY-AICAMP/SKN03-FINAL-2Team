from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    query: str
    images: list
    chat_history: list
    hypothetical_doc: str
    embedding: list
    documents: list
    reranked_documents: list
    aggregated_documents: list
    popularity_ranked_documents: list
    human_answer: str | None
    answer_type: str
    response: str
