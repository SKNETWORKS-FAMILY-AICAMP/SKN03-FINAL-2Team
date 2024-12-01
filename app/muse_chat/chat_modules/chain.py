from operator import itemgetter

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from muse_chat.chat_modules.model import Model
from muse_chat.chat_modules.prompt import Prompt


class Chain:
    """LCEL 체인 저장소"""

    @staticmethod
    def set_hyde_chain(mode: str):
        """HyDE 노드에서 사용할 체인"""
        if mode == "single":
            prompt = Prompt.get_hyde_single_prompt()
            model = Model.get_openai_single_model()
            chain = {"query": lambda x: x["query"]} | prompt | model | StrOutputParser()
        elif mode == "multi":
            model = Model.get_openai_multi_model()
            prompt = Prompt.get_hyde_multi_prompt()

            chain = (
                {
                    "prompt_text": lambda x: prompt.format(query=x["query"]),
                    "images": itemgetter("images"),
                }
                | (
                    lambda x: [
                        HumanMessage(
                            content=[
                                {"type": "text", "text": x["prompt_text"]},
                                *[
                                    {"type": "image_url", "image_url": {"url": img}}
                                    for img in x["images"]
                                ],
                            ]
                        )
                    ]
                )
                | model
                | StrOutputParser()
            )
        return chain

    @staticmethod
    def set_rewrite_chain():
        """Re-write 노드에서 사용할 체인"""
        prompt = Prompt.get_rewrite_prompt()
        model = Model.get_openai_single_model()
        chain = (
            {
                "query": lambda x: x["query"],
                "hypothetical_doc": lambda x: x["hypothetical_doc"],
            }
            | prompt
            | model
            | StrOutputParser()
        )
        return chain
