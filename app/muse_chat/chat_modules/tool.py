from typing import Dict, List

from muse_chat.chat_modules.chain import Chain


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
    def make_history_title(element):
        chain = Chain.set_history_title_chain()
        return chain.invoke(
            {
                "element": element,
            },
        )
