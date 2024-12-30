import os

from dotenv import load_dotenv
from ragas.testset.graph import KnowledgeGraph, Node
from ragas.testset.transforms.extractors import NERExtractor

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


async def build_knowledge_graph():
    """전시회 데이터로부터 지식 그래프 생성"""
    collection = init_db()
    documents = list(collection.find({}))

    nodes = []
    for doc in documents:
        nodes.append(
            Node(
                properties={"page_content": doc["E_context"]},
            ),
        )
    extractor = NERExtractor()
    output = [extractor.extract(node) for node in nodes]

    return print(output[0])


def generate_testset(knowledge_graph):
    pass


def evaluate_rag_pipeline(testset):
    """RAG 파이프라인 평가"""
    chat_graph = MuseChatGraph()
    pass


def main():
    # DB 초기화
    init_db()

    # 지식 그래프 생성
    print("Building Knowledge Graph...")
    kg = build_knowledge_graph()
    print(kg)
    # # 테스트셋 생성
    # print("Generating Testset...")
    # testset = generate_testset(kg)

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
