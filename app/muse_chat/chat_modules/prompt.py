from langchain_core.prompts import PromptTemplate


class Prompt:
    """프롬프트 템플릿 저장소"""

    @staticmethod
    def get_hyde_prompt():
        # HyDE(Hypothetical Document Embeddings) 프롬프트
        hyde_template = """As an inquirer, your role is to refine and refine the question so that the Retriever system returns optimal results based on the given conversation history and the current question. Your returns should only return questions and not fluff. They should be returned in sentences, not in order, and should never say anything unnecessary. 
        
Here are some requirements to get you thinking:
1. what is the purpose or intent of the user's question?
2. clearly define the core question expressed in the User Query and generate specific sub-questions to support it. 3.
3. Can you isolate the main core concept of the question and break it down into sub-questions?
4. Can you give specific examples or illustrations to clarify the question?
5. Use the conversation history to understand the context of the question.
6. Keep your questions as concise and clear as possible.
7. The final output should be a specific and clear question that is easy for Retriever to process.
8. Don't generate responses to things you don't know or are vague about, and focus on why they're asking.
9. You MUST generate the answer in Korean.

Previous conversation:
{chat_history}

Current question: {query}

Output formats:
[Materialized Question or Refined Question 1].
[Specified question or refined question 2].
[Additional questions if needed]."""

        return PromptTemplate(
            template=hyde_template, input_variables=["query", "chat_history"]
        )

    @staticmethod
    def get_gen_prompt():
        # 최종 응답 생성을 위한 프롬프트
        gen_template = """You are a helpful AI assistant that helps users understand VADA documentation. Use the following pieces of context and conversation history to answer the question at the end.
If you don't know the answer, just say that you don't know. DO NOT try to make up an answer.

Previous conversation:
{chat_history}

Relevant documentation:
{context}

Current question: {query}

Instructions:
1. Use the provided context and conversation history to give a comprehensive answer
2. If the context doesn't contain enough information, say so
3. Keep the answer focused and relevant to the question
4. Use clear and professional language
5. You MUST respond in Korean

Answer: Let me help you with that."""

        return PromptTemplate(
            template=gen_template, input_variables=["query", "context", "chat_history"]
        )
