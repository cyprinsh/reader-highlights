import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime

# 1. 모바일 및 웹 공용 기본 설정
st.set_page_config(page_title="북리더 독서노트", page_icon="📚")
st.title("📚 북리더 하이라이트 추출기")
st.markdown("여러 개의 `.mrexpt` 파일을 드래그 앤 드롭하여 한 번에 변환하세요.")

# 2. 초정밀 데이터 필터링 함수 (불필요한 정보 완전 제거)
def parse_mrexpt(file_bytes, filename):
    try:
        content = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        content = file_bytes.decode('cp949', errors='ignore')
        
    lines = content.splitlines()
    if not lines:
        return None

    raw_title = filename.replace(".mrexpt", "").strip()
    
    # [핵심 수정] 괄호 '(' 나 하이픈 '-' 이전의 진짜 핵심 제목만 추출
    # 예: "결국, 강점 (유선영)-260516" -> "결국, 강점"
    core_title = re.split(r'[\(\-]', raw_title)[0].strip()
    
    highlights = []
    
    for line in lines:
        text = line.strip()
        if not text: continue
        
        # [필터 1] 양수/음수 일체 숫자 제거
        if re.match(r'^-?\d+$', text): continue
        
        # [필터 2] 문리더 내부 설정값 제거
        if 'indent:' in text.lower() or 'trim:' in text.lower(): continue
        if text.lower() in ['false', 'true']: continue
        
        # [필터 3] 시스템 파일 경로 제거
        if text.startswith('/storage') or text.startswith('/sdcard') or text.startswith('content://'): continue
        
        # [필터 4] 본문 내 불필요하게 반복되는 책 제목 제거 (핵심 제목 기준)
        if text.lower() == core_title.lower() or text.lower() == raw_title.lower(): continue
        
        # [필터 5] 너무 짧은 의미 없는 파편 문자 제거
        if len(text) <= 2: continue
        
        highlights.append(text)
            
    return {
        "title": raw_title,
        "updated_at": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "highlights": highlights
    }

# 3. 다운로드용 예쁜 HTML 문서 생성 함수 (꼬리말 제거)
def generate_html(book_data):
    title = book_data['title']
    highlights = book_data['highlights']
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - 독서노트</title>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.7; color: #2c3e50; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f7fa; }}
            .container {{ background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            h1 {{ color: #1a2a3a; text-align: center; font-size: 1.8em; margin-bottom: 5px; }}
            .meta {{ text-align: center; color: #95a5a6; font-size: 0.9em; margin-bottom: 30px; border-bottom: 1px solid #eceff1; padding-bottom: 15px; }}
            .highlight-item {{ position: relative; background: #fffdf3; border-left: 4px solid #f1c40f; padding: 15px 20px; margin-bottom: 18px; border-radius: 0 8px 8px 0; font-size: 1.05em; word-break: break-all; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📘 {title}</h1>
            <div class="meta">생성일: {book_data['updated_at']} | 하이라이트: {len(highlights)}개</div>
    """
    
    for hl in highlights:
        html_content += f'        <div class="highlight-item">{hl}</div>\n'
        
    # [핵심 수정] 불필요한 footer(꼬리말) 제거
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content

# 세션 데이터 저장소 초기화
if "books_db" not in st.session_state:
    st.session_state.books_db = {}

# 4. 드래그 앤 드롭 다중 파일 업로드 UI
with st.expander("📂 여기에 여러 파일 드래그 앤 드롭하기", expanded=not bool(st.session_state.books_db)):
    uploaded_files = st.file_uploader(
        "문리더에서 내보낸 .mrexpt 파일들을 한 번에 올리세요.", 
        type=["mrexpt"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            bytes_data = file.read()
            parsed_data = parse_mrexpt(bytes_data, file.name)
            
            if parsed_data:
                title = parsed_data["title"]
                st.session_state.books_db[title] = parsed_data

st.divider()

# 5. 결과물 동시 확인(HTML 렌더링) 및 다운로드 제공
if st.session_state.books_db:
    book_list = list(st.session_state.books_db.keys())
    selected_book = st.selectbox("📖 결과물을 확인할 책을 선택하세요", book_list)
    book_data = st.session_state.books_db[selected_book]
    
    html_string = generate_html(book_data)
    
    st.download_button(
        label=f"📥 {book_data['title']} HTML 다운로드",
        data=html_string,
        file_name=f"{book_data['title']}_독서노트.html",
        mime="text/html",
        type="primary"
    )
    
    st.write("")
    st.markdown("### 🖥️ HTML 실시간 미리보기")
    st.caption("실제 다운로드되는 HTML 파일과 완전히 동일한 화면입니다. 아래 창에서 스크롤하여 보실 수 있습니다.")
    
    components.html(html_string, height=600, scrolling=True)

else:
    st.info("💡 위 상자를 클릭하여 문리더 백업 파일(.mrexpt)들을 마우스로 끌어다 놓아주세요.")
