import ast
import logging
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.testset import TestsetGenerator
from ragas.testset.persona import Persona

from muse_chat.chat import MuseChatGraph, process_query
from shared.mongo_base import MongoBase

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()


def init_db():
    """MongoDB 연결 초기화"""
    try:
        MongoBase.initialize(
            os.getenv("MONGO_URI"),
            os.getenv("MONGO_DB_NAME"),
            os.getenv("MONGO_VECTOR_DB_NAME"),
        )
        return MongoBase.db["Exhibition"]
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise


def safe_eval_contexts(context_str: str) -> List[str]:
    """문자열로 된 컨텍스트 리스트를 안전하게 파싱"""
    try:
        return ast.literal_eval(context_str)
    except Exception as e:
        logger.warning(f"컨텍스트 파싱 중 오류 발생: {e}. 빈 리스트 반환")
        return []


def generate_testset():
    """전시 데이터를 하나의 Document로 변환"""
    try:
        collection = init_db()
        # 랜덤으로 100개의 문서 샘플링
        mongo_documents = list(collection.aggregate([{"$sample": {"size": 100}}]))

        if not mongo_documents:
            raise ValueError("데이터베이스에서 문서를 가져오지 못했습니다.")

        # 모든 전시 정보를 하나의 텍스트로 통합
        combined_content = ""

        for doc in mongo_documents:
            # 각 전시회 정보를 구조화된 텍스트로 변환
            exhibition_text = f"""
전시회명: {doc.get('E_title', '')}
전시회 내용: {doc.get('E_context', '')}
전시회 장소: {doc.get('E_place', '')}
전시회 기간: {doc.get('E_date', '')}
전시회 인기도: {doc.get('E_ticketcast', '')}
전시회 포스터: ![poster]({doc.get('E_poster', '')})
전시회 링크: {doc.get('E_link', '')}

"""
            combined_content += exhibition_text

        # 하나의 통합된 Document 생성
        combined_document = Document(
            page_content=combined_content.strip(),
            metadata={
                "type": "exhibition",
                "content": [
                    "title",
                    "context",
                    "place",
                    "date",
                    "popularity",
                    "poster",
                    "link",
                ],
            },
        )

        # Document를 리스트로 감싸서 반환
        documents = [combined_document]

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

        personas = [
            persona_casual_visitor,
            persona_art_enthusiast,
            persona_professional,
        ]

        # generator
        generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
        generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        generator = TestsetGenerator(
            llm=generator_llm,
            embedding_model=generator_embeddings,
            persona_list=personas,
        )

        logger.info("테스트셋 생성 시작...")
        dataset = generator.generate_with_langchain_docs(
            documents,
            testset_size=100,
        )
        df = dataset.to_pandas()

        # CSV 파일로 저장
        output_path = "testset_results.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"테스트셋이 {output_path}에 저장되었습니다.")

        return df

    except Exception as e:
        logger.error(f"테스트셋 생성 중 오류 발생: {e}")
        raise


def evaluate_rag_pipeline(testset):
    """RAG 파이프라인 평가"""
    try:
        chat_graph = MuseChatGraph()

        # LLM과 임베딩 모델 초기화
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        embeddings = OpenAIEmbeddings()

        # Wrapper 초기화
        llm_wrapper = LangchainLLMWrapper(langchain_llm=llm)
        embeddings_wrapper = LangchainEmbeddingsWrapper(embeddings=embeddings)

        # 평가에 사용할 메트릭 정의
        metrics = [
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ]

        # 평가 데이터셋 준비
        evaluation_samples = []

        logger.info(f"총 {len(testset)} 개의 테스트 케이스에 대해 평가를 시작합니다.")

        # 각 테스트 케이스에 대해 RAG 파이프라인 실행
        for idx, row in testset.iterrows():
            try:
                query = row["user_input"]
                logger.info(
                    f"테스트 케이스 {idx + 1}/{len(testset)} 처리 중: {query[:50]}..."
                )

                # RAG 파이프라인 실행
                response = ""
                retrieved_contexts = []

                for result in process_query(chat_graph.main_graph, query):
                    if isinstance(result, dict):
                        if "aggregated_documents" in result:
                            # 검색된 문서 저장
                            retrieved_contexts = [
                                doc["E_context"]
                                for doc in result["aggregated_documents"]
                            ]
                    else:
                        # 응답 저장
                        response = result

                # ground truth contexts 파싱
                try:
                    ground_truth_contexts = safe_eval_contexts(
                        row["reference_contexts"]
                    )
                except Exception as e:
                    logger.warning(f"ground truth contexts 파싱 실패: {e}")
                    ground_truth_contexts = []

                # 평가 데이터 구성
                if (
                    response and retrieved_contexts
                ):  # 응답과 컨텍스트가 있는 경우만 추가
                    # 데이터셋을 Hugging Face Dataset 형식으로 구성
                    sample_dict = {
                        "question": query,  # 필수: 모든 메트릭
                        "answer": response,  # 필수: 모든 메트릭
                        "contexts": retrieved_contexts,  # 필수: context_precision, context_recall
                        "reference": row["reference"],  # 필수: context_precision
                        "ground_truths": [row["reference"]],  # 필수: answer_relevancy
                        "ground_truth_contexts": ground_truth_contexts,  # 필수: context_recall
                    }
                    evaluation_samples.append(sample_dict)
                    logger.info(f"평가 데이터 추가됨: question={query}")
                else:
                    logger.warning(
                        f"테스트 케이스 {idx + 1} 건너뜀: 응답 또는 컨텍스트 없음"
                    )

            except Exception as e:
                logger.error(f"테스트 케이스 {idx + 1} 처리 중 오류 발생: {e}")
                continue

        if not evaluation_samples:
            raise ValueError("평가할 데이터가 없습니다.")

        logger.info("Ragas 평가 실행 중...")

        # Hugging Face Dataset으로 변환
        from datasets import Dataset

        evaluation_dataset = Dataset.from_list(evaluation_samples)

        # Ragas 평가 실행
        evaluation_results = evaluate(
            metrics=metrics,
            dataset=evaluation_dataset,
            llm=llm_wrapper,
            embeddings=embeddings_wrapper,
        )

        return evaluation_results

    except Exception as e:
        logger.error(f"RAG 파이프라인 평가 중 오류 발생: {e}")
        raise


def save_evaluation_results(results: Dict, testset_size: int):
    """평가 결과를 CSV 파일로 저장"""
    try:
        # 현재 시간을 파일명에 포함
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"evaluation_results_{timestamp}.csv"

        # 결과를 DataFrame으로 변환
        results_df = pd.DataFrame(
            {
                "metric": list(results.keys()),
                "score": list(results.values()),
                "testset_size": [testset_size] * len(results),
                "evaluation_timestamp": [timestamp] * len(results),
            }
        )

        # CSV 파일로 저장
        results_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"평가 결과가 {output_path}에 저장되었습니다.")

        return output_path
    except Exception as e:
        logger.error(f"평가 결과 저장 중 오류 발생: {e}")
        raise


def load_existing_testset():
    """기존 테스트셋 로드"""
    try:
        testset_path = "testset_results.csv"
        if os.path.exists(testset_path):
            logger.info(f"기존 테스트셋 {testset_path}를 로드합니다.")
            return pd.read_csv(testset_path)
        else:
            logger.info("기존 테스트셋이 없어 새로 생성합니다.")
            return None
    except Exception as e:
        logger.error(f"테스트셋 로드 중 오류 발생: {e}")
        raise


def main():
    try:
        # DB 초기화
        init_db()

        # 테스트셋 로드 또는 생성
        testset = load_existing_testset()
        if testset is None:
            logger.info("테스트셋 생성 중...")
            testset = generate_testset()

        logger.info("테스트셋 미리보기:")
        print(testset.head())

        # 평가 수행
        logger.info("\nRAG 파이프라인 평가 중...")
        results = evaluate_rag_pipeline(testset)

        # 결과를 DataFrame으로 변환
        results_df = pd.DataFrame(results.scores)

        # 각 메트릭의 평균 점수 계산
        results_dict = results_df.mean().to_dict()

        # 결과 출력
        logger.info("\nRAG Pipeline 평가 결과:")
        print("================================")
        for metric_name, score in results_dict.items():
            print(f"{metric_name}: {score:.4f}")

        # 평균 결과 저장
        output_path = save_evaluation_results(results_dict, len(testset))
        logger.info(f"평가 결과가 {output_path}에 저장되었습니다.")

        # 상세 결과 저장 (각 테스트 케이스별 점수)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_output_path = f"detailed_evaluation_results_{timestamp}.csv"
        results_df.to_csv(detailed_output_path, index=False, encoding="utf-8-sig")
        logger.info(f"상세 평가 결과가 {detailed_output_path}에 저장되었습니다.")

    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
