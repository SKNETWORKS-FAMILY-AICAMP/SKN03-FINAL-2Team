import os

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.testset.graph import KnowledgeGraph, Node, NodeType
from ragas.testset.synthesizers import default_query_distribution
from ragas.testset.transforms import apply_transforms, default_transforms

from muse_chat.chat import MuseChatGraph
from shared.mongo_base import MongoBase

# 환경 변수 로드
load_dotenv()


def init_db():
    """MongoDB 연결 초기화"""
    MongoBase.initialize(
        os.getenv("MONGO_URI"),
        os.getenv("MONGO_DB_NAME"),
        os.getenv("MONGO_VECTOR_DB_NAME"),
    )
    return MongoBase.db["Exhibition"]


def build_knowledge_graph(llm, embedding_model):
    """전시 데이터를 Sequence[Document] 형태로 변환"""
    collection = init_db()
    # 랜덤으로 100개의 문서 샘플링
    mongo_documents = list(collection.aggregate([{"$sample": {"size": 100}}]))
    kg = KnowledgeGraph()
    # MongoDB 문서들을 Langchain Document 형태로 변환
    documents = []
    for doc in mongo_documents:
        # 각 문서의 메타데이터와 내용을 포함하여 Document 객체 생성
        document = Document(
            page_content=doc["E_context"],
            metadata={
                "title": doc.get("E_title", ""),
            },
        )
        documents.append(document)

    for doc in documents:
        kg.nodes.append(
            Node(
                type=NodeType.DOCUMENT,
                properties={
                    "page_content": doc.page_content,
                    "document_metadata": doc.metadata,
                },
            )
        )

    trans = default_transforms(
        documents=documents, llm=llm, embedding_model=embedding_model
    )
    apply_transforms(kg, trans)

    return kg


def generate_testset(knowledge_graph, llm, embedding_model):
    generator = TestsetGenerator(
        llm=llm,
        embedding_model=embedding_model,
        knowledge_graph=knowledge_graph,
    )

    query_distribution = default_query_distribution(llm)
    testset = generator.generate(testset_size=10, query_distribution=query_distribution)
    return testset.to_pandas()


def evaluate_rag_pipeline(testset):
    """RAG 파이프라인 평가"""
    chat_graph = MuseChatGraph()
    pass


def main():
    # DB 초기화
    init_db()

    llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
    embedding_model = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

    # 지식 그래프 생성
    print("Building Knowledge Graph...")
    kg = build_knowledge_graph(llm, embedding_model)
    print(kg)
    # 테스트셋 생성
    print("Generating Testset...")
    testset = generate_testset(kg, llm, embedding_model)
    print(testset)

    # # 평가 수행
    # print("Evaluating RAG Pipeline...")
    # results = evaluate_rag_pipeline(testset)

    # # 결과 출력
    # print("RAG Pipeline Evaluation Results:")
    # print("================================")
    # for metric_name, score in results.items():
    #     print(f"{metric_name}: {score:.4f}")


if __name__ == "__main__":
    main()
