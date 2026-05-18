import streamlit as st
import streamlit.components.v1 as components
import re
import html # [핵심 추가] 특수기호를 안전하게 변환하는 모듈
from datetime import datetime

st.set_page_config(page_title="북리더 통합 독서노트", page_icon="📚", layout="centered")
st.title("📚 북리더 통합 서재 만들기")
st.markdown("여러 개의 **북리더 백업 파일**을 올려 **단 하나의 통합 HTML 파일**로 다운로드하세요.")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "books_db" not in st.session_state:
    st.session_state.books_db = {}

# 1. 정밀 데이터 필터링 함수
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

# 2. 통합 HTML 생성 함수
def generate_combined_html(books_dict):
    html_start = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>나의 통합 독서노트</title>
        <style>
            :root { --base-font-size: 16px; }
            body { 
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; 
                line-height: 1.7; 
                color: #2c3e50; 
                max-width: 700px; 
                margin: 0 auto; 
                padding: 20px; 
                background-color: #f5f7fa;
                font-size: var(--base-font-size); 
                transition: font-size 0.2s ease; 
            }
            .container { background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-height: 80vh; position: relative; }
            h1 { color: #1a2a3a; text-align: center; margin-bottom: 5px; font-size: 1.8em; }
            .meta { text-align: center; color: #95a5a6; font-size: 0.9em; margin-bottom: 30px; border-bottom: 1px solid #eceff1; padding-bottom: 15px; }
            
            .font-control-panel { position: fixed; top: 20px; right: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(5px); padding: 5px; border-radius: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; gap: 2px; }
            .font-btn { background: #34495e; color: white; border: none; width: 35px; height: 35px; border-radius: 50%; cursor: pointer; font-weight: bold; font-size: 1.2em; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
            .font-btn:hover { background: #2c3e50; }
            .font-btn:disabled { background: #bdc3c7; cursor: not-allowed; }

            .view-section { display: none; padding-bottom: 80px; padding-top: 10px; }
            .view-section.active { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            
            .book-card { background: #f8f9fa; border-left: 5px solid #3498db; padding: 20px; margin-bottom: 15px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
            .book-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); background: #fff; }
            .book-card h3 { margin: 0 0 8px 0; color: #2c3e50; font-size: 1.3em; }
            
            .back-btn { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); z-index: 999; background: #34495e; color: #ffffff; border: none; padding: 12px 24px; border-radius: 50px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.25); transition: all 0.2s ease; font-size: 1em; }
            .back-btn:hover { background: #2c3e50; transform: translateX(-50%) translateY(-3px); box-shadow:
