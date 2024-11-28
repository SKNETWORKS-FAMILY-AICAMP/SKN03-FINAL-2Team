from langchain_cohere import CohereRerank
from langchain_openai import ChatOpenAI
from langchain_upstage import UpstageEmbeddings


class Model:
    def get_embedding_model():
        return UpstageEmbeddings("solar-embedding-1-large-query")

    def get_openai_model():
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    def get_rerank_model():
        return CohereRerank(model="rerank-multilingual-v3.0")
