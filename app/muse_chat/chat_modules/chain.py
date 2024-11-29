from chat_modules.model import Model
from chat_modules.prompt import Prompt
from langchain_core.output_parsers import StrOutputParser

from muse_chat.chat_modules.tools import Tool


class Chain:
    """LCEL 체인 저장소"""

    @staticmethod
    def set_hyde_chain():
        """HyDE 노드에서 사용할 체인"""
        prompt = Prompt.get_hyde_prompt()
        model = Model.get_openai_model()

        chain = (
            {
                "query": lambda x: x["query"],
                "chat_history": lambda x: Tool.format_chat_history(x["chat_history"]),
            }
            | prompt
            | model
            | StrOutputParser()
        )

        return chain
