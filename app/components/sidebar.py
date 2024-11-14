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
        <a href="search" class="sidebar-item" target="_self">
            <span>🔍 검색</span>
        </a>
        <a href="suggestions" class="sidebar-item" target="_self">
            <span>👤 건의 사항</span>
        </a>
    </div>
    """, unsafe_allow_html=True)