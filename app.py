import streamlit as st
from datetime import datetime
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from drive_handler import (
    get_drive_service_from_secrets,
    get_current_week,
    get_weekly_files_with_binary
)
from gpt_brief import generate_this_brief, generate_last_brief
from audio_utils import text_to_audio

# ──────────────────────────────────────────────────────────────
# Google Sheets 설정 (사용자 정보 저장 X)
# ──────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1WvPyKF1Enq4fqPHRtJi54SaklpQ54TNjcMicvaw6ZkA/edit?gid=0"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_url(SHEET_URL)

# ──────────────────────────────────────────────────────────────
# 사용자 입력
# ──────────────────────────────────────────────────────────────
st.title("🎧 학습 브리핑 팟캐스트")

with st.form("user_form"):
    user_name = st.text_input("이름")
    user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
    user_major = st.text_input("전공")
    user_style = st.selectbox("학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
    course_options = {
        "교육공학": "1k_0XbQO3Jjr1Adgb8XVeqUOX-m1DAh77",
        "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
    }
    course_name = st.selectbox("수강 강의 선택", list(course_options.keys()))
    submitted = st.form_submit_button("선택 완료")

if not submitted:
    st.stop()

# ──────────────────────────────────────────────────────────────
# 수업 주차 정보 및 자료 불러오기
# ──────────────────────────────────────────────────────────────
folder_id = course_options[course_name]
semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()
today = datetime.today()
week_no = get_current_week(semester_start, today.date())

st.sidebar.title("🗂️ 학습 모드 선택")
mode = st.sidebar.radio("원하는 브리핑을 선택하세요", ["이번주 예습", "지난주 복습", "주차별 복습 듣기"])

with st.spinner("📂 강의자료를 불러오고 있습니다..."):
    drive_service = get_drive_service_from_secrets(key_dict)
    last_text, this_text, _ = get_weekly_files_with_binary(
        drive_service, folder_id, week_no
    )

# ──────────────────────────────────────────────────────────────
# 예습 모드
# ──────────────────────────────────────────────────────────────
if mode == "이번주 예습":
    if this_text:
        with st.spinner("💬 예습 브리핑 생성 중..."):
            this_brief = generate_this_brief(user_name, user_grade, user_major, user_style, this_text, course_name)
        with st.spinner("🎧 오디오 변환 중..."):
            audio_this = text_to_audio(this_brief)
            audio_this.seek(0)
            st.subheader(f"🔮 {week_no}주차 예습 브리핑")
            st.audio(audio_this, format="audio/mp3")
    else:
        st.warning("❌ 이번 주 강의자료를 불러올 수 없습니다.")

# ──────────────────────────────────────────────────────────────
# 복습 모드
# ──────────────────────────────────────────────────────────────
elif mode == "지난주 복습":
    if week_no > 1 and last_text:
        with st.spinner("💬 복습 브리핑 생성 중..."):
            last_brief = generate_last_brief(user_name, user_grade, user_major, user_style, last_text, course_name)
        with st.spinner("🎧 오디오 변환 중..."):
            audio_last = text_to_audio(last_brief)
            audio_last.seek(0)
            st.subheader(f"🔁 {week_no - 1}주차 복습 브리핑")
            st.audio(audio_last, format="audio/mp3")
    else:
        st.info("복습할 지난 주차가 없습니다.")

# ──────────────────────────────────────────────────────────────
# 주차별 복습 모드
# ──────────────────────────────────────────────────────────────
elif mode == "주차별 복습 듣기":
    selected_week = st.slider("주차 선택", min_value=1, max_value=week_no - 1 if week_no > 1 else 1)
    _, selected_text, _ = get_weekly_files_with_binary(drive_service, folder_id, selected_week)
    if selected_text:
        with st.spinner("💬 복습 브리핑 생성 중..."):
            brief = generate_last_brief(user_name, user_grade, user_major, user_style, selected_text, course_name)
        with st.spinner("🎧 오디오 변환 중..."):
            audio = text_to_audio(brief)
            audio.seek(0)
            st.subheader(f"🔁 {selected_week}주차 복습 브리핑")
            st.audio(audio, format="audio/mp3")
    else:
        st.warning("해당 주차의 자료를 찾을 수 없습니다.")
