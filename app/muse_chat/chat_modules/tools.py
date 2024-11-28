from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Document:
    """문서 데이터 클래스"""

    text: str
    metadata: Dict


class Tool:
    @staticmethod
    def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
        """
        채팅 기록을 문자열로 포맷팅

        Args:
            chat_history: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}] 형식의 리스트

        Returns:
            포맷팅된 대화 기록 문자열
        """
        formatted = []
        for message in chat_history:
            role = "User" if message["role"] == "user" else "Assistant"
            content = message["content"]
            if content.strip():  # 빈 메시지 제외
                formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    @staticmethod
    def format_retrieved_documents(documents: List[Dict]) -> List[Document]:
        """
        Retriever의 출력값을 Reranker의 입력값으로 변환

        Args:
            documents: Retriever에서 반환된 문서 리스트
                [{"content": str, "metadata": Dict}, ...]

        Returns:
            Reranker에서 사용할 수 있는 Document 객체 리스트
        """
        formatted_docs = []
        for doc in documents:
            # 메타데이터에서 문서의 위치 정보와 페이지 정보 추출
            location = " > ".join(doc["metadata"].get("path", []))
            page = doc["metadata"].get("page", "")
            version = doc["metadata"].get("version", "")

            # 문서 내용과 위치 정보를 결합
            source_info = []
            if location:
                source_info.append(f"위치: {location}")
            if page:
                source_info.append(f"페이지: {page}")
            if version:
                source_info.append(f"버전: {version}")

            text = f"{doc['content']}\n[출처 정보]\n{' | '.join(source_info)}"

            # Document 객체 생성
            formatted_doc = Document(text=text, metadata=doc["metadata"])
            formatted_docs.append(formatted_doc)

        return formatted_docs
