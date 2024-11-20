import streamlit as st
from components.sidebar import add_custom_sidebar
from PIL import Image

# 페이지 기본 설정
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

add_custom_sidebar()

st.markdown("""
<style>
/* 기본 스타일 */
.stButton > button {
    background-color: transparent;
    border: none;
    color: black;
    font-size: 24px;
}

/* 사이드바 스타일 */
.sidebar { 
    background-color: #f0f0f0;
    padding: 20px;
}

/* 제목 스타일 수정 */
.exhibition-title, .musical-title {
    font-size: 48px;
    font-weight: bold;
    transform: rotate(-10deg);
    text-align: center;
}

.top-10-title {
    font-size: 24px;
    font-weight: bold;
    margin: 40px 0 20px 0;
}

/* 이미지 스타일 수정 */
.main-image {
    max-width: 70%;  /* 이미지 최대 너비 */
    max-height: 250px;
    object-fit: contain;  /* 이미지 비율 유지 */
    display: block;
    margin: 0 auto;  /* 가운데 정렬 */
}

/* TOP 10 슬라이더 스타일 수정 */
.slider-container {
    position: relative;
    width: 90%;
    margin: 20px auto;
    padding-right: 40px;
}

.image-row {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 20px;
}

.image-item {
    width: 200px;
    height: 200px;
    flex: 0 0 auto;
}

.image-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* 슬라이더 버튼 스타일 */
.stButton > button {
    position: absolute;
    right: -5px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24px;
    padding: 5px 10px;
    margin: 0;
    background-color: rgba(255, 255, 255, 0.8);
    border: 1px solid #ddd;
    border-radius: 5px;
    cursor: pointer;
}

/* 섹션 컨테이너 스타일 */
.section-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 300px;  /* 섹션 높이 */
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

# 이미지를 base64로 변환하는 함수
def image_to_base64(image):
    import base64
    from io import BytesIO
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# 상단 섹션 이미지 표시 함수
def display_main_image(image_path):
    try:
        image = Image.open(image_path)
        st.markdown(f"""
            <div class="section-container">
                <img src="data:image/png;base64,{image_to_base64(image)}" 
                     class="main-image">
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"이미지 로딩 오류: {str(e)}")

# TOP 10 슬라이더 함수
def display_top_10(image_paths, section_key):
    if section_key not in st.session_state:
        st.session_state[section_key] = 0
    
    current_index = st.session_state[section_key]
    visible_images = image_paths[current_index:current_index + 4]
    
    cols = st.columns([1, 1, 1, 1, 0.2]) 
    for idx, img_path in enumerate(visible_images):
        with cols[idx]:
            image = Image.open(img_path)
            st.image(image, width=150)  
    # 토글 버튼
    with cols[4]:
        if st.button("▶", key=f'next_{section_key}'):
            st.session_state[section_key] = (current_index + 1) % (len(image_paths) - 3)
            # st.experimental_rerun() 

def main():
    col1, col2 = st.columns(2)
    
    # 왼쪽 상단: EXHIBITION
    with col1:
        st.markdown("""
            <div class="section-container">
                <h1 class="exhibition-title">EXHIBITION</h1>
            </div>
        """, unsafe_allow_html=True)
    
    # 오른쪽 상단: 첫 번째 이미지
    with col2:
        display_main_image("static/images/display_image_1.jpg")
    
    # 왼쪽 하단: 두 번째 이미지
    with col1:
        display_main_image("static/images/display_image_2.jpg")
    
    # 오른쪽 하단: MUSICAL
    with col2:
        st.markdown("""
            <div class="section-container">
                <h1 class="musical-title">MUSICAL</h1>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 전시 TOP 10
    st.markdown('<h2 class="top-10-title">전시 TOP 10</h2>', unsafe_allow_html=True)
    exhibition_images = [f"static/images/display_image_{i}.jpg" for i in range(3, 13)]
    display_top_10(exhibition_images, "exhibition_slider")

    st.markdown("---")

    # 뮤지컬 TOP 10
    st.markdown('<h2 class="top-10-title">뮤지컬 TOP 10</h2>', unsafe_allow_html=True)
    musical_images = [f"static/images/display_image_{i}.jpg" for i in range(14, 24)]
    display_top_10(musical_images, "musical_slider")

if __name__ == "__main__":
    main()      