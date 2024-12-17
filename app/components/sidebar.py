import streamlit as st

def add_custom_sidebar():
    st.markdown("""
    <style>
        /* 기본 사이드바 숨기기 */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* 전체 컨테이너 최대 너비 제한 해제 */
        .block-container {
            max-width: 100% !important;
            padding-left: 250px !important;  /* 사이드바 너비만큼 여백 */
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }
        
        /* 커스텀 사이드바 */
        .custom-sidebar {
            width: 250px;
            height: 100vh;
            background-color: rgb(240, 242, 246);
            padding: 2rem 1rem;
            position: fixed;
            left: 0;
            top: 0;
            overflow-y: auto;
        }
        
        /* 사이드바 아이템 스타일 */
        .sidebar-logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 2rem auto;
            display: block;
            cursor: pointer;
        }
        .sidebar-item {
            color: rgb(49, 51, 63);
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            text-decoration: none;
            display: block;
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        .sidebar-item:hover {
            background-color: rgba(151, 166, 195, 0.15);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="custom-sidebar">
        <a href="." class="sidebar-logo" target="_self">
            <img src="static/images/logo.png" alt="Logo" class="sidebar-logo">
        </a>
        <a href="exhibition" class="sidebar-item" target="_self">
            <span>🏛 exhibition</span>
        </a>
        <a href="musical" class="sidebar-item" target="_self">
            <span>🎭 musical</span>
        </a>
        <a href="musical_chat" class="sidebar-item" target="_self">
            <span>musical ChatBot</span>
        </a>
        <a href="suggestions" class="sidebar-item" target="_self">
            <span>👤 건의 사항</span>
        </a>
    </div>
    """, unsafe_allow_html=True)


def button_style():
    st.markdown("""
    <style>
        button {
            position: relative;
            display: inline-block;
            cursor: pointer;
            outline: none;
            border: 0;
            vertical-align: middle;
            text-decoration: none;
            background: transparent;
            padding: 0;
            font-size: inherit;
            font-family: inherit;
        }

        button.learn-more {
            width: 12rem;
            height: auto;
        }

        button.learn-more .circle {
            transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
            position: relative;
            display: block;
            margin: 0;
            width: 3rem;
            height: 3rem;
            background: #282936;
            border-radius: 1.625rem;
        }

        button.learn-more .circle .icon {
            transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
            position: absolute;
            top: 0;
            bottom: 0;
            margin: auto;
            background: #fff;
        }

        button.learn-more .circle .icon.arrow {
            transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
            left: 0.625rem;
            width: 1.125rem;
            height: 0.125rem;
            background: none;
        }

        button.learn-more .circle .icon.arrow::before {
            position: absolute;
            content: "";
            top: -0.29rem;
            right: 0.0625rem;
            width: 0.625rem;
            height: 0.625rem;
            border-top: 0.125rem solid #fff;
            border-right: 0.125rem solid #fff;
            transform: rotate(45deg);
        }

        button.learn-more .button-text {
            transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            padding: 0.75rem 0;
            margin: 0 0 0 1.85rem;
            color: #282936;
            font-weight: 700;
            line-height: 1.6;
            text-align: center;
            text-transform: uppercase;
        }

        button:hover .circle {
            width: 100%;
        }

        button:hover .circle .icon.arrow {
            background: #fff;
            transform: translate(1rem, 0);
        }

        button:hover .button-text {
            color: #fff;
        }
    </style>        
    """, unsafe_allow_html=True)

"""버튼을 HTML 형식으로 렌더링하는 함수"""
def render_button(button_text, button_key=None):
    html = f"""
    <button class="learn-more" id="{button_key or button_text}">
        <span class="circle" aria-hidden="true">
        <span class="icon arrow"></span>
        </span>
        <span class="button-text">{button_text}</span>
    </button>
    """
    st.markdown(html, unsafe_allow_html=True)
