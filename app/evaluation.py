import os

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.testset.persona import Persona

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


def generate_testset():
    """전시 데이터를 Sequence[Document] 형태로 변환"""
    collection = init_db()
    # 랜덤으로 100개의 문서 샘플링
    mongo_documents = list(collection.aggregate([{"$sample": {"size": 100}}]))
    documents = []
    for doc in mongo_documents:
        # Langchain Document 생성
        langchain_doc = Document(
            page_content=doc.get("E_context", ""),
            metadata={
                "title": doc.get("E_title", ""),
                "place": doc.get("E_place", ""),
                "date": doc.get("E_date", ""),
                "popularity": doc.get("E_ticketcast", ""),
                "link": doc.get("E_link", ""),
                "poster": doc.get("E_poster", ""),
            },
        )
        documents.append(langchain_doc)
    """페르소나 생성"""
    persona_casual_visitor = Persona(
        name="일반 관람객",
        role_description="미술에 대한 깊은 지식은 없지만, 여가 시간에 전시회를 방문하여 문화생활을 즐기고 싶어하는 관람객",
    )
    persona_art_enthusiast = Persona(
        name="예술 애호가",
        role_description="미술관과 갤러리를 자주 방문하며, 특정 작가나 예술 사조에 대해 깊이 있는 정보를 찾는 관람객",
    )
    persona_professional = Persona(
        name="전문가",
        role_description="미술계 종사자로서 전시의 기획 의도, 작품의 예술사적 맥락, 작가의 작품 세계에 대한 전문적인 정보를 찾는 관람객",
    )

    personas = [persona_casual_visitor, persona_art_enthusiast, persona_professional]

    # generator
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    generator = TestsetGenerator(
        llm=generator_llm,
        embedding_model=generator_embeddings,
        persona_list=personas,
    )
    dataset = generator.generate_with_langchain_docs(
        documents,
        testset_size=10,
    )
    df = dataset.to_pandas()

    # CSV 파일로 저장
    output_path = "testset_results.csv"
    df.to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )  # utf-8-sig를 사용하여 한글 깨짐 방지
    print(f"테스트셋이 {output_path}에 저장되었습니다.")

    return df


def evaluate_rag_pipeline(testset):
    """RAG 파이프라인 평가"""
    chat_graph = MuseChatGraph()
    pass


def main():
    # DB 초기화
    init_db()

    # 테스트셋 생성
    print("Generating Testset...")
    testset = generate_testset()
    print("테스트셋 미리보기:")
    print(testset.head())

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
