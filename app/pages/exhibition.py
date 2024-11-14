import streamlit as st
from components.sidebar import add_custom_sidebar
from PIL import Image

add_custom_sidebar()

st.markdown("""
<style>
.stButton > button {
    background-color: transparent;
    border: none;
    color: black;
    font-size: 24px;
}

.header-text {
    font-size: 24px;
    margin-bottom: 30px;
    text-align: center;
}

.input-section {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
}

.upload-section {
    background-color: #f0f0f0;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    margin-top: 20px;
}

/* 검색 입력 필드 스타일 */
.stTextInput > div > div > input {
    border-radius: 20px;
    padding-left: 40px;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>');
    background-repeat: no-repeat;
    background-position: 12px center;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 전시회 chat")

st.markdown("""
<div class="header-text">
    좋아하는 사진이나 감성을 알려주세요
</div>
""", unsafe_allow_html=True)

# 입력 섹션
col1, col2 = st.columns([2, 1])

with col1:
    # 검색 입력 필드
    st.markdown("### 좋아하는 그림의 특징")
    search_feature = st.text_input("", placeholder="바로크 화풍", key="feature")
    st.markdown("### 좋아하는 화가")
    search_artist = st.text_input("", placeholder="박종명", key="artist")

with col2:
    # 이미지 업로드 섹션
    st.markdown("### 좋아하는 사진")
    uploaded_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
    else:
        st.markdown("""
            <div style="
                width: 100%;
                height: 200px;
                background-color: #f0f0f0;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
            ">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
            </div>
        """, unsafe_allow_html=True)

if search_feature:
    st.markdown("""
        <div style="
            position: absolute;
            right: 10px;
            top: 50%;
            width: 24px;
            height: 24px;
            background-color: #gray;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        ">
            1
        </div>
    """, unsafe_allow_html=True)

if st.button("제출하기"):
    st.markdown("### 챗봇 왈 : 당신에게 추천드리는 전시회입니다.")
    
    # 메인 추천 결과
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image("static/images/display_image_37.jpg", width=400)
    with col2:
        st.markdown(f"""
        - 제목 : {search_artist}의 {search_feature} 작품
        - 일시 : 2024.01.01 - 2024.12.31
        - 위치 : 예술의 전당
        - 화가 : {search_artist}
        - 가격 : 30,000원
        - 간단 내용 : 바로크 시대의 대표적인 작품
        - 링크 : http://localhost:8501
        """)

    st.markdown("### 유사한 전시회")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("static/images/display_image_1.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)

    with col2:
        st.image("static/images/display_image_2.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)

    with col3:
        st.image("static/images/display_image_3.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)
