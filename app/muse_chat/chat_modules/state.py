from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    query: str
    images: list
    human_answer: str | None
    chat_history: list
    hypothetical_doc: str
    embedding: list
    documents: list
    reranked_documents: list
    response: Annotated[str, add_messages]
