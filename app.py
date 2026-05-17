import streamlit as st
import re
from datetime import datetime

# 1. 모바일 맞춤 기본 설정 (layout="wide" 제거)
st.set_page_config(page_title="독서노트", page_icon="📚")

# 타이틀 최소화 (모바일 화면 공간 절약)
st.title("📚 문리더 노트")

# mrexpt 파싱 함수 (이전과 동일)
def parse_mrexpt(file_bytes, filename):
    try:
        content = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        content = file_bytes.decode('cp949', errors='ignore')
        
    lines = content.splitlines()
    if not lines:
        return None

    book_title = filename.replace(".mrexpt", "")
    highlights = [line.strip() for line in lines if line.strip()]
            
    return {
        "title": book_title,
        "updated_at": datetime.now().strftime("%y.%m.%d %H:%M"), # 모바일용 짧은 날짜
        "highlights": highlights
    }

# 데이터 저장소 초기화
if "books_db" not in st.session_state:
    st.session_state.books_db = {}

# 2. 모바일용 접이식 업로드 메뉴 (Expander)
with st.expander("⚙️ 파일 업로드 및 설정", expanded=not bool(st.session_state.books_db)):
    cover_file = st.file_uploader("🖼️ 책 표지 (선택)", type=["png", "jpg", "jpeg"])
    uploaded_files = st.file_uploader(
        "📂 .mrexpt 파일 추가", 
        type=["mrexpt"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            bytes_data = file.read()
            parsed_data = parse_mrexpt(bytes_data, file.name)
            
            if parsed_data:
                title = parsed_data["title"]
                if title in st.session_state.books_db:
                    st.toast(f"'{title}' 최신 업데이트 완료!", icon="🔄") # 모바일 알림 팝업
                st.session_state.books_db[title] = parsed_data

st.divider()

# 3. 모바일 메인 뷰어 화면
if st.session_state.books_db:
    book_list = list(st.session_state.books_db.keys())
    
    # 책 선택 메뉴를 화면 정중앙 윗부분에 배치해 터치하기 쉽게 구성
    selected_book = st.selectbox("📖 읽을 책을 선택하세요", book_list)
    book_data = st.session_state.books_db[selected_book]
    
    # 표지 이미지가 있을 경우 상단 중앙에 적절한 크기로 배치
    if cover_file is not None:
        # 모바일에서 이미지가 너무 커지지 않도록 비율 조정
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(cover_file, use_container_width=True)
            
    st.markdown(f"### {book_data['title']}")
    st.caption(f"최근 동기화: {book_data['updated_at']}")
    st.write("") # 간격 띄우기
    
    # 4. 모바일 가독성을 높인 카드형 하이라이트 출력
    for idx, hl in enumerate(book_data["highlights"]):
        with st.container(border=True): # 테두리가 있는 둥근 박스(카드) 생성
            st.markdown(f"**{idx+1}.** {hl}")

else:
    st.info("상단의 '파일 업로드'를 눌러 문리더 백업 파일을 추가해 주세요.")