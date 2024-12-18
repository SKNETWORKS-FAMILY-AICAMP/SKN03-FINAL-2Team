from langchain_cohere import CohereRerank
from langchain_openai import ChatOpenAI
from langchain_upstage import UpstageEmbeddings


class Model:
    @staticmethod
    def get_embedding_model():
        return UpstageEmbeddings(model="embedding-query")

    @staticmethod
    def get_openai_single_model():
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    @staticmethod
    def get_openai_multi_model():
        return ChatOpenAI(
            model="gpt-4o-2024-11-20",
            temperature=0.1,
            model_kwargs={"image_to_output": True},
        )

    @staticmethod
    def get_rerank_model():
        return CohereRerank(model="rerank-multilingual-v3.0")
