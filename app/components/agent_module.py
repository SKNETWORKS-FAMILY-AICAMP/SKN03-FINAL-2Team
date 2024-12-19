from langchain.prompts import PromptTemplate
from langchain.agents import create_openai_functions_agent
from langchain_openai.chat_models import ChatOpenAI
from components.tool_module import tools
import os
import json
import sys
import boto3
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))

main_dir = os.path.abspath(os.path.join(current_dir, ".."))
if main_dir not in sys.path:
    sys.path.append(main_dir)

config_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if config_dir not in sys.path:
    sys.path.append(config_dir)

import config
import pandas as pd
from langchain_core.agents import AgentFinish

# JSON 파일에서 배우 목록 생성
df = pd.read_json(config.df_with_negatives_path, lines=True, encoding="utf-8")
cast_list = list(df["cast"].dropna().unique())

# 커스텀 프롬프트 정의
genres_text = ", ".join(config.unique_genres)
actors_text = ", ".join(cast_list)

prompt_text = """
당신은 뮤지컬 추천 및 관련 대화를 전문으로 하는 에이전트입니다.
사용자는 뮤지컬 배우와 장르에 대해 질문하거나 추천을 요청할 수 있습니다.
아래는 사용자가 입력한 내용과 사용 가능한 배우 및 장르 목록입니다:
- 사용자 입력: {input}
- 사용 가능한 배우 목록: {actors}
- 사용 가능한 장르 목록: {genres}

사용자의 질문에서 아래 정보를 추출하십시오:
1. 배우 이름: 제공된 배우 목록({actors}) 중 하나 또는 None
2. 장르 이름: 제공된 장르 목록({genres}) 중 하나 또는 None

추출된 결과를 반드시 다음 JSON 형식으로 반환하십시오:
{{
    "actor": "배우 이름 (actors 중 하나) 또는 None",
    "genre": "장르 이름 (genres 중 하나) 또는 None"
}}

### 작업 내용 ###
{agent_scratchpad}
"""

# PromptTemplate 생성
prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "genres", "actors"],
    template=prompt_text
)

@st.cache_data
def __set_api_key():
    if not os.environ.get("OPENAI_API_KEY"):
        ssm = boto3.client("ssm")
        parameter = ssm.get_parameter(
            Name=f"/DEV/CICD/MUSEIFY/OPENAI_API_KEY", 
            WithDecryption=True
        )
        os.environ["OPENAI_API_KEY"] = parameter["Parameter"]["Value"]

# API 키 설정 실행
__set_api_key()

# OpenAI 모델 초기화
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    streaming=True, 
    api_key=os.getenv("OPENAI_API_KEY")
)

# 에이전트 생성
agent_runnable = create_openai_functions_agent(llm, tools, prompt)

def run_agent(data):
    """Runs the agent and returns the outcome."""
    try:
        # 에이전트 실행
        agent_outcome = agent_runnable.invoke(data)

        # 디버깅 출력
        print(f"[DEBUG] Raw Agent Outcome: {agent_outcome}")

        # AgentFinish 형태 처리
        if isinstance(agent_outcome, AgentFinish):
            output = agent_outcome.return_values.get("output", "{}")
            parsed_response = json.loads(output)
            return {
                "actor": parsed_response.get("actor", None),
                "genre": parsed_response.get("genre", None),
            }
        else:
            # print(f"[DEBUG] Unexpected agent outcome type: {type(agent_outcome)}")
            return {"actor": None, "genre": None, "error": "Unexpected response type"}
    except Exception as e:
        # print(f"[DEBUG] Error in run_agent: {e}")
        return {"actor": None, "genre": None, "error": str(e)}