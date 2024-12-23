from muse_chat.chat_modules.base import Base
from muse_chat.chat_modules.chain import Chain
from muse_chat.chat_modules.model import Model
from muse_chat.chat_modules.state import GraphState


class Single2HyDENode(Base):
    """가상의 문서를 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Single2HyDENode"
        self.chain = Chain.set_hyde_chain(mode="single")

    def process(self, state: GraphState) -> GraphState:
        hypothetical_doc = self.chain.invoke({"query": state["query"]})
        return {"hypothetical_doc": hypothetical_doc}


class Multi2HyDENode(Base):
    """가상의 문서를 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Multi2HyDENode"
        self.chain = Chain.set_hyde_chain(mode="multi")

    def process(self, state: GraphState) -> GraphState:
        hypothetical_doc = self.chain.invoke(
            {"query": state["query"], "image": state["image"]}
        )
        return {"hypothetical_doc": hypothetical_doc}


class EmbedderNode(Base):
    """문서 임베딩을 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "EmbedderNode"
        self.model = Model.get_embedding_model()

    def process(self, state: GraphState) -> GraphState:
        embedding = self.model.embed_query(state["hypothetical_doc"])
        return {"embedding": embedding}


class MongoRetrieverNode(Base):
    """MongoDB에서 유사한 문서를 검색하는 노드"""

    def __init__(
        self,
        exact=True,
        embedding_name="E_embedding",
        limit=10,
        collection=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.name = "MongoRetrieverNode"
        self.collection = collection
        self.exact = exact
        self.embedding_name = embedding_name
        self.limit = limit

    def process(self, state: GraphState) -> GraphState:
        # MongoDB에서 문서 검색
        pipeline = [
            {
                "$vectorSearch": {
                    "exact": self.exact,
                    "index": self.embedding_name,
                    "path": self.embedding_name,
                    "queryVector": state["embedding"],
                    "limit": self.limit,
                }
            }
        ]

        documents = list(self.collection.aggregate(pipeline))
        return {"documents": documents}


class SimilarityRerankerNode(Base):
    """문서 유사도를 기반으로 재정렬하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "SimilarityRerankerNode"
        self.model = Model.get_rerank_model()

    def process(self, state: GraphState) -> GraphState:
        # 문서가 없는 경우 빈 리스트 반환
        if not state["documents"]:
            return {"reranked_documents": []}

        # 디서에서 텍스트 추출
        doc_texts = [doc["E_text"] for doc in state["documents"]]

        # 재정렬 수행
        reranked_results = self.model.rerank(
            documents=doc_texts, query=state["hypothetical_doc"]
        )

        # 재정렬된 문서 생성
        reranked_documents = []
        for result in reranked_results:
            doc_index = result["index"] if isinstance(result, dict) else result.index
            doc = state["documents"][doc_index].copy()
            doc["score"] = (
                result["relevance_score"]
                if isinstance(result, dict)
                else result.relevance_score
            )
            reranked_documents.append(doc)

        return {"reranked_documents": reranked_documents}


class MongoAggregationNode(Base):
    """문서를 집계하는 노드"""

    def __init__(self, collection=None, **kwargs):
        super().__init__(**kwargs)
        self.name = "MongoAggregationNode"
        self.collection = collection

    def process(self, state: GraphState) -> GraphState:
        # reranked_documents에서 E_original_id 추출
        original_ids = [doc["E_original_id"] for doc in state["reranked_documents"]]

        # MongoDB 파이프라인 구성
        pipeline = [
            {"$match": {"_id": {"$in": original_ids}}},
            {
                "$project": {
                    "E_title": 1,
                    "E_context": 1,
                    "E_poster": 1,
                    "E_price": 1,
                    "E_place": 1,
                    "E_date": 1,
                    "E_link": 1,
                    "E_ticketcast": 1,
                }
            },
        ]

        # MongoDB에서 문서 검색
        aggregated_docs = list(self.collection.aggregate(pipeline))

        # reranked_documents와 병합
        merged_docs = []
        for reranked_doc in state["reranked_documents"]:
            for agg_doc in aggregated_docs:
                if reranked_doc["E_original_id"] == agg_doc["_id"]:
                    merged_doc = {**reranked_doc, **agg_doc}
                    merged_docs.append(merged_doc)
                    break

        return {"aggregated_documents": merged_docs}


class PopularityRerankerNode(Base):
    """인기도를 기반으로 재정렬하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "PopularityRerankerNode"

    def format_exhibition(self, doc):
        """전시회 정보를 포맷팅하는 헬퍼 함수"""
        try:
            print(f"\nFormatting exhibition: {doc.get('E_title', '제목 없음')}")
            formatted = f"""
### 🎨 {doc.get('E_title', '제목 없음')}

![전시회 포스터]({doc.get('E_poster', '이미지 없음')})

{doc.get('E_context', '내용 없음')}

**상세 정보**
- 💰 가격: {doc.get('E_price', '가격 정보 없음')}
- 📍 위치: {doc.get('E_place', '위치 정보 없음')}
- 📅 날짜: {doc.get('E_date', '날짜 정보 없음')}
- 🔗 링크: {doc.get('E_link', '링크 없음')}
"""
            return formatted
        except Exception as e:
            return "전시회 정보를 표시할 수 없습니다."

    def process(self, state: GraphState) -> GraphState:
        try:
            # 인기도(E_ticketcast) 기준으로 정렬
            sorted_docs = sorted(
                state["aggregated_documents"],
                key=lambda x: x.get("E_ticketcast", 0),
                reverse=True,
            )

            for i, doc in enumerate(sorted_docs):
                print(
                    f"Doc {i+1} ticketcast: {doc.get('E_ticketcast', 0)}, title: {doc.get('E_title', '제목 없음')}"
                )

            # 전시회 정보 포맷팅
            exhibitions = []
            for i, doc in enumerate(sorted_docs, 1):
                formatted = self.format_exhibition(doc)
                exhibitions.append(formatted)

            # 전체 응답 생성
            response = "\n\n".join(exhibitions)

            return {"response": response}

        except Exception as e:
            return {"response": "전시회 정보를 처리하는 중 오류가 발생했습니다."}


class ReWriterNode(Base):
    """문서를 재작성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "ReWriterNode"

    def process(self, state: GraphState) -> GraphState:
        # rewrite 체인 실행
        chain = Chain.set_rewrite_chain()
        rewritten_query = chain.invoke(
            {"query": state["query"], "hypothetical_doc": state["hypothetical_doc"]}
        )
        return {"query": rewritten_query}


class JudgeNode(Base):
    """사용자 쿼리를 평가하고 Rerank 시키는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "JudgeNode"

    def process(self, state: GraphState) -> GraphState:
        # 쿼리 평가 로직 구현
        chain = Chain.set_judge_chain()
        response = chain.invoke(
            {
                "query": state["query"],
                "chat_history": state["chat_history"],
                "documents": state["documents"],
            },
        )
        return {"response": response}
