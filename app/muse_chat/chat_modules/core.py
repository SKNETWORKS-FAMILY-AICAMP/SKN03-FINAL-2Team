import streamlit as st

from muse_chat.chat_modules.base import Base
from muse_chat.chat_modules.chain import Chain
from muse_chat.chat_modules.model import Model
from muse_chat.chat_modules.state import GraphState


class Single2HyDENode(Base):
    """가상의 문서를 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "HyDESingleNode"
        self.chain = Chain.set_hyde_chain(mode="single")

    def process(self, state: GraphState) -> GraphState:
        hypothetical_doc = self.chain.invoke({"query": state["query"]})
        print("Single2HyDENode : ", hypothetical_doc)
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
        print("Multi2HyDENode : ", hypothetical_doc)
        return {"hypothetical_doc": hypothetical_doc}


class EmbedderNode(Base):
    """문서 임베딩을 생성하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "EmbedderNode"
        self.model = Model.get_embedding_model()

    def process(self, state: GraphState) -> GraphState:
        embedding = self.model.get_embedding(state["hypothetical_doc"])
        print("EmbedderNode : ", embedding)
        return {"embedding": embedding}


class MongoRetrieverNode(Base):
    """MongoDB에서 유사한 문서를 검색하는 노드"""

    def __init__(
        self, exact=True, index_name="E_embedding", limit=10, collection=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.name = "MongoRetrieverNode"
        self.collection = collection
        self.exact = exact
        self.index_name = index_name
        self.limit = limit

    def process(self, state: GraphState) -> GraphState:
        # MongoDB에서 문서 검색
        pipeline = [
            {
                "$vectorSearch": {
                    "exact": self.exact,
                    "index": self.index_name,
                    "limit": self.limit,
                    "path": "embedding",
                    "queryVector": state["embedding"],
                }
            }
        ]
        documents = self.collection.aggregate(pipeline)
        print("MongoRetrieverNode : ", documents)
        return {"documents": documents}


class SimilarityRerankerNode(Base):
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

        print("SimilarityRerankerNode : ", reranked_documents)
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

        print("MongoAggregationNode : ", merged_docs)
        return {"aggregated_documents": merged_docs}


class PopularityRerankerNode(Base):
    """인기도를 기반으로 재순위화하는 노드"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "PopularityRerankerNode"

    def process(self, state: GraphState) -> GraphState:
        # aggregated_documents를 E_ticketcast 기준으로 정렬
        sorted_docs = sorted(
            state["aggregated_documents"],
            key=lambda x: x.get("E_ticketcast", 0),
            reverse=True,  # 높은 순서대로 정렬
        )
        print("PopularityRerankerNode : ", sorted_docs)
        return {"popularity_ranked_documents": sorted_docs}


class HumanNode(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "HumanNode"

    def process(self, state: GraphState) -> GraphState:
        # GraphState에서 현재 상태 확인
        current_answer = state.get("human_answer")

        if current_answer is None:
            # 처음 선택하는 경우에만 라디오 버튼 표시
            answer = st.radio(
                "추천된 전시회가 마음에 드시나요?",
                ["만족합니다", "다른 추천을 볼래요"],
                key="temp_human_answer",  # 임시 키로 사용
            )

            # AI 응답 메시지 표시
            with st.chat_message("assistant"):
                if answer == "만족합니다":
                    st.write("좋은 선택이에요! 즐거운 관람 되시길 바랍니다. 😊")
                else:
                    st.write(
                        "다른 전시회를 추천해드리도록 하겠습니다. 잠시만 기다려주세요... 🔍"
                    )

            # GraphState 업데이트
            return {
                "human_answer": answer,
                "answer_type": "accept" if answer == "만족합니다" else "revise",
            }
        else:
            # 이미 선택한 경우 저장된 응답 표시
            with st.chat_message("assistant"):
                if current_answer == "만족합니다":
                    st.write("좋은 선택이에요! 즐거운 관람 되시길 바랍니다. 😊")
                else:
                    st.write(
                        "다른 전시회를 추천해드리도록 하겠습니다. 잠시만 기다려주세요... 🔍"
                    )

            # 저장된 상태 반환
            print("HumanNode : ", current_answer)
            return {
                "human_answer": current_answer,
                "answer_type": "accept" if current_answer == "만족합니다" else "revise",
            }


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
        print("ReWriterNode : ", rewritten_query)
        return {"query": rewritten_query}
