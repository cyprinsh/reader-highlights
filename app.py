import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime

st.set_page_config(page_title="북리더 통합 독서노트", page_icon="📚", layout="centered")
st.title("📚 북리더 통합 서재 만들기")
st.markdown("여러 개의 `.mrexpt` 파일을 올려 **단 하나의 통합 HTML 파일**로 다운로드하세요.")

# 1. 정밀 데이터 필터링 함수 (이전과 동일하게 불필요 데이터 완벽 제거)
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

# 2. 하나의 앱처럼 동작하는 '통합 HTML' 생성 함수
def generate_combined_html(books_dict):
    # HTML 기본 뼈대 및 CSS 디자인
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
            
            /* 목록 화면과 상세 화면 전환 제어용 CSS */
            .view-section { display: none; }
            .view-section.active { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            
            /* 책 목록 카드 디자인 */
            .book-card { background: #f8f9fa; border-left: 5px solid #3498db; padding: 20px; margin-bottom: 15px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
            .book-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); background: #fff; }
            .book-card h3 { margin: 0 0 8px 0; color: #2c3e50; }
            
            /* 뒤로 가기 버튼 및 하이라이트 디자인 */
            .back-btn { background: #ecf0f1; color: #34495e; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-bottom: 20px; transition: background 0.2s; }
            .back-btn:hover { background: #dfe6e9; }
            .highlight-item { position: relative; background: #fffdf3; border-left: 4px solid #f1c40f; padding: 15px 20px; margin-bottom: 18px; border-radius: 0 8px 8px 0; font-size: 1.05em; word-break: break-all; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        </style>
    </head>
    <body>
        <div class="container">
    """
    
    # 목록(홈) 화면 구성
    home_html = f'<div id="home" class="view-section active">\n<h1>📚 나의 독서노트 서재</h1>\n<div class="meta">총 {len(books_dict)}권의 책이 정리되어 있습니다.</div>\n'
    
    # 상세 내용(본문) 화면 구성
    content_html = ""
    
    for idx, (title, data) in enumerate(books_dict.items()):
        book_id = f"book-{idx}"
        
        # 목록 화면에 카드 추가 (클릭 시 자바스크립트 함수 호출)
        home_html += f'<div class="book-card" onclick="showSection(\'{book_id}\')">\n'
        home_html += f'    <h3>📘 {title}</h3>\n'
        home_html += f'    <p style="color: #7f8c8d; font-size: 0.85em; margin: 0;">하이라이트: {len(data["highlights"])}개 | 최근 동기화: {data["updated_at"]}</p>\n'
        home_html += f'</div>\n'
        
        # 각각의 상세 화면 추가 (초기에는 숨겨져 있음)
        content_html += f'<div id="{book_id}" class="view-section">\n'
        # history.back()을 사용해 브라우저 네
