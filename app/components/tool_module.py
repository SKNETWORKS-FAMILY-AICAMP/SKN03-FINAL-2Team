from langchain.tools import tool
from typing import List, Dict
from langchain_community.tools.tavily_search import TavilySearchResults
import random

def recommend_musical_site() -> str:
    """Recommends a list of ticket booking sites, each on a new line."""
    sites = [
        "https://tickets.interpark.com/contents/genre/musical",
        "https://www.ticketlink.co.kr/performance/16",
        "https://m.playdb.co.kr/Play/List?maincategory=000001",
    ]
    # 각 사이트를 줄바꿈하여 표시할 수 있도록 문자열로 반환
    return "\n".join(sites)


@tool("musical_recommendation", return_direct=True)
def musical_recommendation(location: str) -> str:
    """Provides a response if a location outside Jeju is requested."""
    if "뮤지컬" not in location:
        return "죄송합니다. 뮤지컬 추천 챗봇입니다. 다른 내용 추천을 원하시면 네이버에서 검색해보세요: https://www.naver.com"
    else:
        return "뮤지컬 추천 챗봇입니다. 무엇을 도와드릴까요?"

@tool("search", return_direct=True)
def search_site(query: str) -> List[Dict[str, str]]:
    """Search News by input keyword"""
    site_tool = TavilySearchResults(
        max_results=6,
        include_answer=True,
        include_raw_content=True,
        include_domains=["google.com", "naver.com"],
    )
    return site_tool.invoke({"query": query})

@tool
def say_hello(user_input: str) -> str:
    """Responds with a greeting if the user says hello or a similar greeting."""
    greetings = ["안녕하세요", "hello", "hi", "안녕", "안뇽", "헬로", "하이"]
    
    # 인삿말을 사용자가 입력한 경우 응답 반환
    if any(greeting in user_input.lower() for greeting in greetings):
        return "안녕하세요✋ 뮤지컬 관람을 계획중이신가요? 필요하신 정보를 입력해주세요 ☺️"
    else:
        return ""


# 도구들을 리스트로 묶어 정의
tools = [recommend_musical_site, musical_recommendation, search_site, say_hello]