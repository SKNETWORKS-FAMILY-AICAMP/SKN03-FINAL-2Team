from typing import TypedDict, Annotated

from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    query: Annotated[str, add_messages]
    hypothetical_doc: Annotated[str, add_messages]
    embedding: Annotated[list, add_messages]
    documents: Annotated[list, add_messages]
    reranked_documents: Annotated[list, add_messages]
    response: Annotated[list, add_messages]
