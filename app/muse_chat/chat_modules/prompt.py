from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


class Prompt:
    """프롬프트 템플릿 저장소"""

    @staticmethod
    def get_hyde_multi_prompt():
        multi_hyde_template = """You are an expert exhibition recommender.
Given a user query and the provided images, create a detailed hypothetical exhibition description that would best match what the user is looking for.
Focus on aspects like the exhibition theme, style, atmosphere, and target audience.
Consider both the textual query and the visual elements in the provided images. 

All responses must be in Korean.

User Query: {query}

Create a detailed exhibition description:"""
        return PromptTemplate(
            template=multi_hyde_template,
            input_variables=["query"],
        )

    @staticmethod
    def get_hyde_single_prompt():
        single_hyde_template = """You are an expert exhibition recommender.
Given a user query, create a detailed hypothetical exhibition description that would best match what the user is looking for.
Focus on aspects like the exhibition theme, style, atmosphere, and target audience. 

All responses must be in Korean.

User Query: {query}

Create a detailed exhibition description:"""
        return PromptTemplate(
            template=single_hyde_template,
            input_variables=["query"],
        )

    @staticmethod
    def get_rewrite_prompt():
        rewrite_template = """You are an expert at rewriting queries to find alternative exhibition recommendations.
Given the original query and the hypothetical document that didn't satisfy the user, rewrite the query to find different but relevant exhibitions.
Consider changing the perspective, focus, or emphasis while maintaining the core intent.

All responses must be in Korean.

Original Query: {query}
Previous Hypothetical Document: {hypothetical_doc}

Rewrite the query to find different exhibitions:"""
        return PromptTemplate(
            template=rewrite_template,
            input_variables=["query", "hypothetical_doc"],
        )
