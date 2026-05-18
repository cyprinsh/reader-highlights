import streamlit as st
import streamlit.components.v1 as components
import re
import html
from datetime import datetime

st.set_page_config(page_title="북리더 통합 독서노트", page_icon="📚", layout="centered")
st.title("📚 북리더 통합 서재 만들기")
st.markdown("PC에 백업해둔 **문리더 백업 파일**들을 드래그 앤 드롭하여 통합 HTML 파일을 만드세요.")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "books_db" not in st.session_state:
    st.session_state.books_db = {}

# 1. 정밀 데이터 필터링 함수
def parse_backup_file(file_bytes, filename):
    try:
        content = file_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        content = file_bytes.decode('cp949', errors='ignore')
        
    lines = content.splitlines()
    if not lines:
        return None

    raw_title = re.sub(r'\.(mrexpt|txt)$', '', filename, flags=re.IGNORECASE).strip()
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

# 2. 통합 HTML 생성 함수 (삭제 기능 및 저장 기능 추가)
def generate_combined_html(books_dict):
    sorted_books = dict(sorted(books_dict.items()))

    html_start = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>나의 통합 독서노트</title>
        <style>
            :root { --base-font-size: 16px; }
            body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.7; color: #2c3e50; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f7fa; font-size: var(--base-font-size); transition: font-size 0.2s ease; }
            .container { background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-height: 80vh; position: relative; }
            h1 { color: #1a2a3a; text-align: center; margin-bottom: 5px; font-size: 1.8em; }
            .meta { text-align: center; color: #95a5a6; font-size: 0.9em; margin-bottom: 30px; border-bottom: 1px solid #eceff1; padding-bottom: 15px; }
            .search-box { width: 100%; padding: 12px 15px; margin-bottom: 25px; border: 2px solid #e0e6ed; border-radius: 8px; font-size: 1em; box-sizing: border-box; outline: none; transition: border-color 0.2s; }
            .search-box:focus { border-color: #3498db; }
            
            /* 우측 상단 컨트롤 패널 */
            .font-control-panel { position: fixed; top: 20px; right: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(5px); padding: 5px; border-radius: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; gap: 5px; }
            .control-btn { background: #34495e; color: white; border: none; width: 38px; height: 38px; border-radius: 50%; cursor: pointer; font-weight: bold; font-size: 1.1em; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
            .control-btn:hover { background: #2c3e50; }
            .control-btn.save { background: #27ae60; }
            .control-btn.save:hover { background: #219653; }
            .control-btn:disabled { background: #bdc3c7; cursor: not-allowed; }

            .view-section { display: none; padding-bottom: 80px; padding-top: 10px; }
            .view-section.active { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            
            /* 카드 및 삭제 버튼 스타일 */
            .book-card { background: #f8f9fa; border-left: 5px solid #3498db; padding: 20px; margin-bottom: 15px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
            .book-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); background: #fff; }
            .card-header { display: flex; justify-content: space-between; align-items: flex-start; }
            .book-card h3 { margin: 0 0 8px 0; color: #2c3e50; font-size: 1.3em; }
            
            .del-btn { background: transparent; border: none; font-size: 1.2em; opacity: 0.3; cursor: pointer; transition: all 0.2s; padding: 0; }
            .del-btn:hover { opacity: 1; transform: scale(1.1); filter: grayscale(0); }
            
            .back-btn { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); z-index: 999; background: #34495e; color: #ffffff; border: none; padding: 12px 24px; border-radius: 50px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.25); transition: all 0.2s ease; font-size: 1em; }
            .back-btn:hover { background: #2c3e50; transform: translateX(-50%) translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
            
            .highlight-item { position: relative; background: #fffdf3; border-left: 4px solid #f1c40f; padding: 15px 20px 15px 15px; margin-bottom: 18px; border-radius: 0 8px 8px 0; font-size: 1.05em; word-break: break-all; box-shadow: 0 1px 3px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: flex-start; gap: 15px;}
            .hl-content { flex-grow: 1; }
            .hl-del { flex-shrink: 0; margin-top: -5px; }
        </style>
    </head>
    <body>
        <div class="font-control-panel">
            <button class="control-btn save" onclick="saveHTML()" title="삭제 등 변경사항을 새 HTML 파일로 저장">💾</button>
            <button class="control-btn" id="zoomOut" onclick="changeFontSize(-1)" title="글씨 축소">-</button>
            <button class="control-btn" id="zoomIn" onclick="changeFontSize(1)" title="글씨 확대">+</button>
        </div>
        <div class="container">
    """
    
    home_html = f'<div id="home" class="view-section active">\n<h1>📚 나의 독서노트 서재</h1>\n<div class="meta">총 <span id="book-count">{len(sorted_books)}</span>권의 책이 정리되어 있습니다.</div>\n'
    content_html = ""
    
    for idx, (title, data) in enumerate(sorted_books.items()):
        book_id = f"book-{idx}"
        safe_title = html.escape(title)
        
        # 메인 화면 책 카드 (삭제 버튼 포함)
        home_html += f'<div class="book-card" id="card-{book_id}" onclick="showDetail(\'{book_id}\')">\n'
        home_html += f'    <div class="card-header">\n'
        home_html += f'        <h3>📘 {safe_title}</h3>\n'
        home_html += f'        <button class="del-btn" onclick="event.stopPropagation(); deleteBook(\'{book_id}\', \'{safe_title}\')" title="이 책 삭제하기">🗑️</button>\n'
        home_html += f'    </div>\n'
        home_html += f'    <p style="color: #7f8c8d; font-size: 0.85em; margin: 0;">하이라이트: <span class="hl-count">{len(data["highlights"])}</span>개</p>\n'
        home_html += f'</div>\n'
        
        # 책 상세 화면
        content_html += f'<div id="{book_id}" class="view-section">\n'
        content_html += f'    <h1>📘 {safe_title}</h1>\n'
        content_html += f'    <input type="text" class="search-box" placeholder="이 책에서 내용 검색하기..." onkeyup="filterHighlights(this, \'{book_id}\')">\n'
        
        content_html += f'    <div class="highlight-container">\n'
        for hl in data['highlights']:
            temp_hl = re.sub(r'<[bB][rR]\s*/?>', '\n', hl)
            safe_hl = html.escape(temp_hl)
            safe_hl = safe_hl.replace('\n', '<br>')
            
            # 개별 하이라이트 (삭제 버튼 포함)
            content_html += f'        <div class="highlight-item">\n'
            content_html += f'            <div class="hl-content">{safe_hl}</div>\n'
            content_html += f'            <div class="hl-del"><button class="del-btn" onclick="deleteHighlight(this, \'{book_id}\')" title="하이라이트 지우기">🗑️</button></div>\n'
            content_html += f'        </div>\n'
            
        content_html += f'    </div>\n'
        content_html += f'    <button class="back-btn" onclick="goHome()">⬅️ 목록으로 돌아가기</button>\n'
        content_html += f'</div>\n'
        
    home_html += "</div>\n"
    
    script_html = """
        </div>
        <script>
            // 화면 이동 로직
            function showDetail(id) {
                var sections = document.querySelectorAll('.view-section');
                for(var i=0; i<sections.length; i++) { sections[i].classList.remove('active'); }
                var target = document.getElementById(id);
                if(target) {
                    target.classList.add('active');
                    var searchBox = target.querySelector('.search-box');
                    if(searchBox) { searchBox.value = ''; filterHighlights(searchBox, id); }
                }
                window.scrollTo(0,0);
                try { history.pushState({view: id}, '', '#' + id); } catch(e) {}
            }

            function goHome() {
                var sections = document.querySelectorAll('.view-section');
                for(var i=0; i<sections.length; i++) { sections[i].classList.remove('active'); }
                document.getElementById('home').classList.add('active');
                window.scrollTo(0,0);
                try { history.pushState({view: 'home'}, '', '#home'); } catch(e) {}
            }
            
            // 삭제 기능 로직
            function deleteBook(bookId, bookTitle) {
                if(confirm("'" + bookTitle + "' 책을 서재에서 완전히 삭제하시겠습니까?")) {
                    var card = document.getElementById('card-' + bookId);
                    var detail = document.getElementById(bookId);
                    if(card) card.remove();
                    if(detail) detail.remove();
                    
                    // 총 권수 업데이트
                    var countSpan = document.getElementById('book-count');
                    var currentCount = parseInt(countSpan.innerText);
                    countSpan.innerText = currentCount - 1;
                }
            }
            
            function deleteHighlight(btnElement, bookId) {
                if(confirm("이 하이라이트를 삭제하시겠습니까?")) {
                    // DOM에서 하이라이트 아이템 제거
                    btnElement.closest('.highlight-item').remove();
                    
                    // 메인 화면의 하이라이트 개수 업데이트
                    var card = document.getElementById('card-' + bookId);
                    if(card) {
                        var hlCountSpan = card.querySelector('.hl-count');
                        var currentCount = parseInt(hlCountSpan.innerText);
                        hlCountSpan.innerText = currentCount - 1;
                    }
                }
            }

            // HTML 오프라인 덮어쓰기 다운로드 (Save) 로직
            function saveHTML() {
                if(!confirm("삭제 등 지금까지 변경된 내용을 새로운 파일로 저장하시겠습니까?")) return;
                
                // 현재 문서의 상태(DOM)를 텍스트로 추출
                var htmlContent = "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
                
                // Blob을 이용해 다운로드 링크 생성 및 클릭
                var blob = new Blob([htmlContent], {type: "text/html;charset=utf-8"});
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = "나의_통합_독서노트_수정본(저장됨).html";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            // 검색 및 기타 로직
            function filterHighlights(inputElement, bookId) {
                var filter = inputElement.value.toLowerCase();
                var container = document.getElementById(bookId);
                var items = container.getElementsByClassName('highlight-item');
                for (var i = 0; i < items.length; i++) {
                    var text = items[i].querySelector('.hl-content').innerText;
                    items[i].style.display = (text.toLowerCase().indexOf(filter) > -1) ? "" : "none";
                }
            }

            window.addEventListener('popstate', function(event) {
                var sections = document.querySelectorAll('.view-section');
                for(var i=0; i<sections.length; i++) { sections[i].classList.remove('active'); }
                if(event.state && event.state.view && document.getElementById(event.state.view)) {
                    document.getElementById(event.state.view).classList.add('active');
                } else {
                    document.getElementById('home').classList.add('active');
                }
            });

            const zoomLevels = [12, 14, 16, 18, 20];
            let currentZoomIndex = 2;

            function changeFontSize(delta) {
                let newIndex = currentZoomIndex + delta;
                if(newIndex < 0 || newIndex >= zoomLevels.length) return;
                currentZoomIndex = newIndex;
                document.documentElement.style.setProperty('--base-font-size', zoomLevels[currentZoomIndex] + 'px');
                document.getElementById('zoomOut').disabled = (currentZoomIndex === 0);
                document.getElementById('zoomIn').disabled = (currentZoomIndex === zoomLevels.length - 1);
            }

            try { history.replaceState({view: 'home'}, '', '#home'); } catch(e) {}
        </script>
    </body>
    </html>
    """
    
    return html_start + home_html + content_html + script_html

# UI 화면
with st.expander("📂 여기에 백업 파일 끌어다 놓기", expanded=not bool(st.session_state.books_db)):
    uploaded_files = st.file_uploader(
        "마우스로 여러 개의 파일을 한 번에 드래그 앤 드롭 하세요.", 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded_files:
        for file in uploaded_files:
            if not (file.name.lower().endswith('.mrexpt') or file.name.lower().endswith('.txt')):
                continue
            bytes_data = file.read()
            parsed_data = parse_backup_file(bytes_data, file.name)
            if parsed_data:
                title = parsed_data["title"]
                st.session_state.books_db[title] = parsed_data

st.divider()

if st.session_state.books_db:
    st.success(f"🎉 총 {len(st.session_state.books_db)}권의 책이 성공적으로 처리되었습니다.")
    
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
    st.markdown("### 📱 다운로드될 HTML 미리보기")
    st.caption("우측의 🗑️ 버튼으로 하이라이트를 삭제하고, 상단의 초록색 💾(저장) 버튼을 누르면 수정된 내용이 파일로 저장됩니다.")
    components.html(combined_html_string, height=700, scrolling=True)
    
    if st.button("🗑️ 업로드 목록 초기화"):
        st.session_state.books_db = {}
        st.session_state.uploader_key += 1
        st.rerun()

else:
    st.info("💡 위의 상자를 열어 백업 파일들을 추가하면 나만의 통합 서재가 만들어집니다.")
