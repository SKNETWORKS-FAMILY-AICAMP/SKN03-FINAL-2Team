import base64
import os
from datetime import datetime

# import boto3
import streamlit as st

from muse_chat.chat import MuseChatGraph, process_query
from muse_chat.chat_modules.tool import Tool
from shared.mongo_base import MongoBase

# @st.cache_data  # 데이터를 caching 처리
# def __set_api_key():
#     for i in [
#         "MONGO_URI",
#         "MONGO_DB_NAME",
#         "MONGO_VECTOR_DB_NAME",
#         "UPSTAGE_API_KEY",
#         "COHERE_API_KEY",
#         "OPENAI_API_KEY",
#     ]:
#         if not os.environ.get(i):
#             ssm = boto3.client("ssm")
#             parameter = ssm.get_parameter(
#                 Name=f"/DEV/CICD/MUSEIFY/{i}", WithDecryption=True
#             )
#             os.environ[i] = parameter["Parameter"]["Value"]


@st.cache_resource
def connect_db():
    MongoBase.initialize(
        os.getenv("MONGO_URI"),
        os.getenv("MONGO_DB_NAME"),
        os.getenv("MONGO_VECTOR_DB_NAME"),
    )


@st.cache_resource
def get_chat_history_db():
    return MongoBase.db["ExhibitionUserHistory"]


@st.cache_resource
def get_graph():
    muse_chat_graph = MuseChatGraph()
    return muse_chat_graph.main_graph, muse_chat_graph.rewrite_graph


def new_chat():
    return {
        "messages": [],
        "title": "New chat",
        "last_documents": [],
        "updated_at": None,
        "_id": None,
    }


def update_sidebar(mongo_client):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = list(mongo_client.find().sort("updated_at", -1))
    with st.sidebar:
        if st.button("새 채팅", key="new_chat"):
            st.session_state.current_chat = new_chat()
        st.title("Past Conversation")
        for chat in st.session_state.chat_history:
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(chat["title"], key=chat["_id"], type="primary"):
                    st.session_state.current_chat = chat
            with col2:
                if st.button("❌", key=f"delete_{chat["_id"]}", type="primary"):
                    mongo_client.delete_one({"_id": chat["_id"]})
                    st.session_state.chat_history = [
                        item
                        for item in st.session_state.chat_history
                        if item["_id"] != chat["_id"]
                    ]
                    if st.session_state.current_chat["_id"] == chat["_id"]:
                        st.session_state.current_chat = new_chat()
                    st.rerun()


def insert_chat(mongo_client):
    del st.session_state.current_chat["_id"]
    result = mongo_client.insert_one(st.session_state.current_chat)
    st.session_state.current_chat["_id"] = result.inserted_id
    st.session_state.chat_history.insert(0, st.session_state.current_chat)


def update_title(mongo_client):
    st.session_state.current_chat["title"] = Tool.make_history_title(
        st.session_state.current_chat["messages"][0]["content"]
    )
    mongo_client.update_one(
        {"_id": st.session_state.current_chat["_id"]},
        {"$set": {"title": st.session_state.current_chat["title"]}},
    )


def update_chat(mongo_client):
    st.session_state.current_chat["updated_at"] = datetime.now()
    if st.session_state.chat_history[0]["_id"] != st.session_state.current_chat["_id"]:
        move_to_top(st.session_state.current_chat["_id"])

    # MongoDB에 저장할 데이터 준비
    update_data = {
        "updated_at": st.session_state.current_chat["updated_at"],
        "messages": st.session_state.current_chat["messages"],
        "last_documents": st.session_state.current_chat["last_documents"],
    }

    mongo_client.update_one(
        {"_id": st.session_state.current_chat["_id"]},
        {"$set": update_data},
    )


def move_to_top(chat_id):
    chat_index = next(
        (
            i
            for i, chat in enumerate(st.session_state.chat_history)
            if chat["_id"] == chat_id
        ),
        None,
    )
    if chat_index is not None:
        chat = st.session_state.chat_history.pop(chat_index)
        st.session_state.chat_history.insert(0, chat)


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


def get_style():
    return """
        <style>
            button[kind="primary"] {
                background: none !important;
                border: none;
                padding: 0 !important;
                color: gray !important;
                text-decoration: none;
                cursor: pointer;
                border: none !important;
            }
            button[kind="primary"]:hover {
                text-decoration: none;
                color: black !important;
            }
            button[kind="primary"]:focus {
                outline: none !important;
                box-shadow: none !important;
                color: black !important;
            }
        </style>
    """


def encode_image_to_base64(upload_image):
    if upload_image is None:
        return None

    # 이미지를 base64로 인코딩
    bytes_data = upload_image.getvalue()
    base64_image = base64.b64encode(bytes_data).decode()
    return f"data:image/{upload_image.type.split('/')[-1]};base64,{base64_image}"


def main():
    st.markdown(get_style(), unsafe_allow_html=True)

    chat_history_db = get_chat_history_db()
    main_graph, rewrite_graph = get_graph()

    with st.sidebar:
        upload_image = st.file_uploader(
            "좋아하는 사진 넣기", type=["jpg", "png", "jpeg"]
        )

    # 세션 상태 초기화
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = new_chat()

    update_sidebar(chat_history_db)

    # 채팅 메시지들을 표시
    for message in st.session_state.current_chat["messages"]:
        avatar = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if query := st.chat_input("최근 관심사를 입력해주세요 :)"):

        # 사용자 메시지 표시
        st.chat_message("user", avatar="user").write(query)

        if not st.session_state.current_chat["_id"]:
            insert_chat(chat_history_db)

        # 이미지 처리
        image_data = encode_image_to_base64(upload_image) if upload_image else None

        # 어시스턴트 응답 처리
        with st.chat_message("assistant", avatar="assistant"):
            for result in process_query(
                main_graph,
                query,
                image_data,
                last_documents=st.session_state.current_chat["last_documents"],
                chat_history=st.session_state.current_chat["messages"],
            ):
                if result["type"] == "memory_update":
                    # last_documents를 새로운 문서들로 완전히 교체
                    st.session_state.current_chat["last_documents"] = result[
                        "documents"
                    ]
                else:
                    response = st.write_stream(result)

        st.session_state.current_chat["messages"].extend(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response},
            ]
        )
        if st.session_state.current_chat["title"] == "New chat":
            update_title(chat_history_db)

        update_chat(chat_history_db)
        st.rerun()


if __name__ == "__main__":
    st.title("💬 Muse Chat")
    st.caption("사용자 관심사 기반 전시회 추천 가이드")
    connect_db()
    main()
