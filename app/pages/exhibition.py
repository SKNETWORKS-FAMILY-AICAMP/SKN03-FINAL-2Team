import os
import sys

project_root_dir = os.getcwd()
sys.path.append(project_root_dir)

import streamlit as st
from dotenv import load_dotenv
from st_multimodal_chatinput import multimodal_chatinput

from components.sidebar import add_custom_sidebar
from muse_chat.chat import build_graph, process_query
from shared.mongo_base import MongoBase

load_dotenv()

add_custom_sidebar()


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
    graph = get_graph()

    # 세션 상태 초기화
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = new_chat()

    st.title("💬 Muse Chat")
    st.caption("사용자 관심사 기반 전시회 추천 가이드")

    # with st.container():
    #     reconfig_chatinput()

    #     # 채팅 메시지들을 표시
    #     for message in st.session_state.current_chat["messages"]:
    #         st.chat_message(message["role"]).write(message["content"])

    # # 텍스트 입력 필드
    # if query := multimodal_chatinput():
    #     st.write(query)
    #     st.session_state.current_chat["messages"].extend(
    #         [
    #             {"role": "user", "content": query},
    #         ]
    #     )
    if query := st.chat_input("메시지를 입력하세요..."):
        st.chat_message("user", avatar="user").write(query)

        with st.chat_message("assistant", avatar="assistant"):
            response = st.write_stream(process_query(graph, query))

        st.session_state.current_chat["messages"].extend(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response},
            ]
        )


if __name__ == "__main__":
    main()
