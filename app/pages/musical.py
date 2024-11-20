import streamlit as st
from components.sidebar import add_custom_sidebar

add_custom_sidebar()

# CSS 스타일 적용
st.markdown("""
<style>
.stButton > button {
    background-color: transparent;
    border: none;
    color: black;
    font-size: 24px;
}

.sidebar {
    background-color: #f0f0f0;
    padding: 20px;
}

.search-container {
    background-color: #f5f5f5;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}

.search-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
}

.search-box {
    background-color: white;
    border-radius: 25px;
    padding: 10px 20px;
    margin: 10px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.header-text {
    background-color: #e0e0e0;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 30px;
    text-align: center;
    font-size: 18px;
}

.result-container {
    background-color: #f5f5f5;
    padding: 30px;
    border-radius: 10px;
    margin: 20px 0;
}

.show-info {
    margin: 20px 0;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# 메인 페이지 제목
st.markdown("# 뮤지컬 chat")

# 상단 설명 텍스트
st.markdown("""
<div class="header-text">
    좋아하시는 배우들과 비슷한<br>
    배우들을 기반으로 뮤지컬이 추천됩니다
</div>
""", unsafe_allow_html=True)

# 폼 생성
with st.form(key='musical_form'):
    actor = st.text_input("좋아하는 배우", placeholder="배우 박종명?")
    genre = st.text_input("좋아하는 장르", placeholder="좋아하는 장르가 어떻게 박종명?")
    content = st.text_input("좋아하는 내용", placeholder="좋아하는 내용이 왜 이주원?")
    submit = st.form_submit_button("추천받기")

if submit:
    st.markdown("### 챗봇 왈 : 당신에게 추천드리는 전시회입니다.")
    
    # 메인 추천 결과
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image("static/images/display_image_1.jpg", width=400) 
    with col2:
        st.markdown(f"""
        - 제목 : {genre}
        - 일시 : 2024.01.01 - 2024.12.31
        - 위치 : 예술의 전당
        - 배우 : {actor}
        - 가격 : 30,000원
        - 간단 내용 : {content}
        - 링크 : http://localhost:8501
        """)

    st.markdown("### 유사한 뮤지컬")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("static/images/display_image_2.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)

    with col2:
        st.image("static/images/display_image_3.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)

    with col3:
        st.image("static/images/display_image_4.jpg", use_container_width=True)
        st.markdown("""
        - 제목:
        - 가격:
        - 링크:
        """)