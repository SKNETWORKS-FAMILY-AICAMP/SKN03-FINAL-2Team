import os

import boto3
import streamlit as st
from muse_chat.chat import build_graph, process_query
from shared.mongo_base import MongoBase

# from st_multimodal_chatinput import multimodal_chatinput


@st.cache_data  # 데이터를 caching 처리
def __set_api_key():
    for i in [
        "MONGO_URI",
        "MONGO_DB_NAME",
        "MONGO_VECTOR_DB_NAME",
        "UPSTAGE_API_KEY",
        "COHERE_API_KEY",
        "OPENAI_API_KEY",
    ]:
        if not os.environ.get(i):
            ssm = boto3.client("ssm")
            parameter = ssm.get_parameter(
                Name=f"/DEV/CICD/MUSEIFY/{i}", WithDecryption=True
            )
            os.environ[i] = parameter["Parameter"]["Value"]


@st.cache_resource
def connect_db():
    MongoBase.initialize(
        os.getenv("MONGO_URI"),
        os.getenv("MONGO_DB_NAME"),
        os.getenv("MONGO_VECTOR_DB_NAME"),
    )


@st.cache_resource
def get_graph():
    return build_graph()


def new_chat():
    return {"messages": []}


def reconfig_chatinput():
    st.markdown(
        """
    <style>
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:first-of-type {
            position: fixed;
            bottom: 0;
            width: 100%; /* Span the full width of the viewport */;
            background-color: #0E117;
            z-index: 1000;
            /* Other styles as needed */    
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
    return


def main():
    st.title("💬 Muse Chat")
    st.caption("사용자 관심사 기반 전시회 추천 가이드")

    graph = get_graph()

    # 세션 상태 초기화
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = new_chat()

    # 채팅 메시지들을 표시
    for message in st.session_state.current_chat["messages"]:
        avatar = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if query := st.chat_input("메시지를 입력하세요..."):

        # 사용자 메시지 표시
        st.chat_message("user", avatar="user").write(query)

        # 어시스턴트 응답 처리
        with st.chat_message("assistant", avatar="assistant"):
            # process_query에서 생성된 모든 응답을 수집
            full_response = ""
            try:
                print("Collecting responses from process_query...")
                for response in process_query(graph, query):

                    # HumanMessage 타입 처리
                    if hasattr(response, "content"):
                        response = response.content
                    elif isinstance(response, list):
                        # 리스트의 각 항목이 HumanMessage인 경우 처리
                        response = "\n\n".join(
                            msg.content if hasattr(msg, "content") else str(msg)
                            for msg in response
                        )
                    elif not isinstance(response, str):
                        response = str(response)

                    if response:
                        full_response += response

                # 전체 응답 표시
                if full_response.strip():
                    st.markdown(full_response)
                else:
                    st.error("응답을 생성하지 못했습니다.")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")

        # 메시지 히스토리에 저장
        if full_response.strip():
            print("Saving to chat history")
            st.session_state.current_chat["messages"].extend(
                [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": full_response},
                ]
            )

        print("=== Exhibition Page Processing End ===\n")


if __name__ == "__main__":
    __set_api_key()
    connect_db()
    main()
