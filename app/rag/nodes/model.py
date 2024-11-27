class Model:
    def __init__(self, openai_api_key: str, upstage_api_key: str, cohere_api_key: str):
        self.openai_api_key = openai_api_key
        self.upstage_api_key = upstage_api_key
        self.cohere_api_key = cohere_api_key
