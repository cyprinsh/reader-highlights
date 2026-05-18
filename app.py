import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime

st.set_page_config(page_title="북리더 통합 독서노트", page_icon="📚", layout="centered")
st.title("📚 북리더 통합 서재 만들기")
st.markdown("여러 개의 파일을 올려 ** 통합 HTML 파일**로 다운로드하세요.")

def parse_mrexpt(file_bytes, filename):
    try:
        content = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        content = file_bytes.decode('cp949', errors='ignore')
        
    lines = content.splitlines()
    if not lines:
        return None

    raw_title = filename.replace(".mrexpt", "").strip()
    core_title = re.split(r'[\(\-]', raw_title)[0].strip()
    
    highlights = []
    
    for line in lines:
        text = line.strip()
        if not text: continue
        if re.match(r'^-?\d+$', text): continue
        if 'indent:' in text.lower() or 'trim:' in text.lower(): continue
        if text.lower() in ['false', 'true']: continue
        if text.startswith('/storage') or text.startswith('/sdcard') or text.startswith('content://'): continue
        if text.lower() == core_title.lower() or text.lower() == raw_title.lower(): continue
        if len(text) <= 2: continue
        
        highlights.append(text)
            
    return {
        "title": raw_title,
        "updated_at": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "highlights": highlights
    }

def generate_combined_html(books_dict):
    html_start = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>나의 통합 독서노트</title>
        <style>
            body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.7; color: #2c3e50; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f7fa; }
            .container { background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-height: 80vh; }
            h1 { color: #1a2a3a; text-align: center; margin-bottom: 5px; }
            .meta { text-align: center; color: #95a5a6; font-size: 0.9em; margin-bottom: 30px; border-bottom: 1px solid #eceff1; padding-bottom: 15px; }
            
            .view-section { display: none; }
            .view-section.active { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            
            .book-card { background: #f8f9fa; border-left: 5px solid #3498db; padding: 20px; margin-bottom: 15px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
            .book-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); background: #fff; }
            .book-card h3 { margin: 0 0 8px 0; color: #2c3e50; }
            
            .back-btn { background: #ecf0f1; color: #34495e; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-bottom: 20px; transition: background 0.2s; display: inline-block; text-decoration: none; }
            .back-btn:hover { background: #dfe6e9; }
            .highlight-item { position: relative; background: #fffdf3; border-left: 4px solid #f1c40f; padding: 15px 20px; margin-bottom: 18px; border-radius: 0 8px 8px 0; font-size: 1.05em; word-break: break-all; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        </style>
    </head>
    <body>
        <div class="container">
    """
    
    home_html = f'<div id="home" class="view-section active">\n<h1>📚 나의 독서노트 서재</h1>\n<div class="meta">총 {len(books_dict)}권의 책이 정리되어 있습니다.</div>\n'
    content_html = ""
    
    for idx, (title, data) in enumerate(books_dict.items()):
        book_id = f"book-{idx}"
        
        # [수정됨] 클릭 시 URL 해시(#)를 변경하는 방식으로 교체
        home_html += f'<div class="book-card" onclick="window.location.hash=\'{book_id}\'">\n'
        home_html += f'    <h3>📘 {title}</h3>\n'
        home_html += f'    <p style="color: #7f8c8d; font-size: 0.85em; margin: 0;">하이라이트: {len(data["highlights"])}개 | 최근 동기화: {data["updated_at"]}</p>\n'
        home_html += f'</div>\n'
        
        content_html += f'<div id="{book_id}" class="view-section">\n'
        # [수정됨] 뒤로 가기 버튼도 해시를 home으로 돌리는 방식으로 교체
        content_html += f'    <a href="#home" class="back-btn">⬅️ 목록으로 돌아가기</a>\n'
        content_html += f'    <h1>📘 {title}</h1><br>\n'
        for hl in data['highlights']:
            content_html += f'    <div class="highlight-item">{hl}</div>\n'
        content_html += f'</div>\n'
        
    home_html += "</div>\n"
    
    # [수정됨] 로컬 파일에서도 100% 작동하는 Hash 라우팅 자바스크립트
    script_html = """
        </div>
        <script>
            function handleNavigation() {
                // 현재 URL의 # 뒤에 있는 글자를 가져옴 (없으면 home)
                var hash = window.location.hash.substring(1);
                if (!hash) hash = 'home';
                
                // 모든 화면 숨기기
                var sections = document.querySelectorAll('.view-section');
                for (var i = 0; i < sections.length; i++) {
                    sections[i].classList.remove('active');
                }
                
                // 선택된 화면만 보여주기
                var target = document.getElementById(hash);
                if (target) {
                    target.classList.add('active');
                } else {
                    document.getElementById('home').classList.add('active');
                }
                window.scrollTo(0,0);
            }

            // 해시(#)가 바뀔 때마다, 그리고 처음 로드될 때 실행
            window.addEventListener('hashchange', handleNavigation);
            window.addEventListener('DOMContentLoaded', handleNavigation);
            handleNavigation(); // 즉시 1회 실행 보장
        </script>
    </body>
    </html>
    """
    
    return html_start + home_html + content_html + script_html


if "books_db" not in st.session_state:
    st.session_state.books_db = {}

with st.expander("📂 여기에 여러 파일 드래그 앤 드롭하기", expanded=not bool(st.session_state.books_db)):
    uploaded_files = st.file_uploader(
        "문리더 백업 파일(.mrexpt)들을 한 번에 추가하세요.", 
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

if st.session_state.books_db:
    st.success(f"총 {len(st.session_state.books_db)}권의 책이 성공적으로 처리되었습니다.")
    
    combined_html_string = generate_combined_html(st.session_state.books_db)
    
    st.download_button(
        label="📥 전체 독서노트 통합 HTML 다운로드",
        data=combined_html_string,
        file_name="나의_통합_독서노트.html",
        mime="text/html",
        type="primary",
        use_container_width=True
    )
    
    st.write("")
    st.markdown("### 📱 다운로드될 파일 미리보기 및 테스트")
    st.caption("아래 화면에서 목록을 클릭하거나 뒤로 가기 버튼을 눌러 테스트해 보세요.")
    
    components.html(combined_html_string, height=700, scrolling=True)
    
    if st.button("🗑️ 전체 목록 초기화"):
        st.session_state.books_db = {}
        st.rerun()

else:
    st.info("💡 위 상자를 열어 .mrexpt 파일들을 추가하면 통합 서재가 만들어집니다.")
