from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


class Prompt:
    """프롬프트 템플릿 저장소"""

    @staticmethod
    def get_multi_hyde_prompt():
        # Multi-Modal HyDE(Hypothetical Document Embeddings) 프롬프트
        multi_hyde_template = """"""
        return PromptTemplate(
            template=multi_hyde_template,
            input_variables=["query"],
        )

    @staticmethod
    def get_single_hyde_prompt():
        # Sigle-Modal HyDE(Hypothetical Document Embeddings) 프롬프트
        single_hyde_template = """"""
        return PromptTemplate(
            template=single_hyde_template,
            input_variables=["query"],
        )

    @staticmethod
    def get_rewrite_prompt():
        # Re-write 프롬프트
        rewrite_template = """"""

        return PromptTemplate(
            template=rewrite_template,
            input_variables=["query"],
        )
