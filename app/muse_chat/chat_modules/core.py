from chat_modules.base import BaseNode
from chat_modules.chain import Chain
from chat_modules.model import Model
from chat_modules.tool import Tool
from chat_modules.state import GraphState


class HyDENode(BaseNode):
    """가상의 문서를 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "HyDENode"
        self.chain = Chain.get_hyde_chain()

    def process(self, state: GraphState) -> GraphState:
        hypothetical_doc = self.chain.invoke(
            {"query": state["query"], "chat_history": state["chat_history"]}
        )
        return {"hypothetical_doc": hypothetical_doc}


class EmbedderNode(BaseNode):
    """문서 임베딩을 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "EmbedderNode"
        self.model = Model.get_embedding_model()

    def process(self, state: GraphState) -> GraphState:
        embedding = self.model.get_embedding(state["hypothetical_doc"])
        return {"embedding": embedding}


class RetrieverNode(BaseNode):
    """MongoDB에서 유사한 문서를 검색하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "RetrieverNode"
        self.collection = MongoBase("manual_vectors")

    def process(self, state: GraphState) -> GraphState:
        # MongoDB에서 문서 검색
        retrieved_docs = self.collection.manual_vector_search(state["embedding"])

        # 검색된 문서를 Reranker 형식으로 변환
        formatted_docs = Tool.format_retrieved_documents(retrieved_docs)
        return {"documents": formatted_docs}


class RerankerNode(BaseNode):
    """검색된 문서를 재순위화하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "RerankerNode"
        self.model = Model.get_rerank_model()

    def process(self, state: GraphState) -> GraphState:
        # Document 객체 리스트를 텍스트 리스트로 변환
        doc_texts = [doc.text for doc in state["documents"]]
        original_docs = {str(i): text for i, text in enumerate(doc_texts)}

        # 문서 재순위화
        reranked_results = self.model.rerank(documents=doc_texts, query=state["query"])

        # 재순위화된 결과에서 텍스트 추출
        reranked_documents = []
        for result in reranked_results:
            if isinstance(result, dict):
                # 인덱스 기반 접근
                if "index" in result:
                    doc_index = str(result["index"])
                    if doc_index in original_docs:
                        reranked_documents.append(original_docs[doc_index])
                # 직접 문서 접근
                elif "document" in result:
                    reranked_documents.append(result["document"])
            else:
                # 객체 기반 접근
                doc = getattr(result, "document", None)
                if doc is not None:
                    reranked_documents.append(doc)

        return {"reranked_documents": reranked_documents}
