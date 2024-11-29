from langchain_cohere import CohereRerank
from langchain_openai import ChatOpenAI
from langchain_upstage import UpstageEmbeddings

# from transformers import AutoModelForSequenceClassification, AutoTokenizer
# import torch
# import numpy as np
# model_path = "Dongjin-kr/ko-reranker"
# tokenizer = AutoTokenizer.from_pretrained(model_path)
# model = AutoModelForSequenceClassification.from_pretrained(model_path)
# model.eval()

# with torch.no_grad():
#     inputs = tokenizer(
#         pairs, padding=True, truncation=True, return_tensors="pt", max_length=512
#     )
#     scores = (
#         model(**inputs, return_dict=True)
#         .logits.view(
#             -1,
#         )
#         .float()
#     )
#     scores = exp_normalize(scores.numpy())


class Model:
    @staticmethod
    def get_embedding_model():
        return UpstageEmbeddings("embedding-query")

    @staticmethod
    def get_openai_single_model():
        return ChatOpenAI(model="gpt-4o-mini", temperature=1.5)

    @staticmethod
    def get_openai_multi_model():
        return ChatOpenAI(model="gpt-4o-2024-11-20", temperature=1.5)

    @staticmethod
    def get_rerank_model():
        return CohereRerank(model="rerank-multilingual-v3.0")
