# app.py

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
from gpt_brief import generate_brief
from audio_utils import text_to_audio

# ──────────────────────────────────────────────────────────────
# Google Sheets 정보 불러오기
# ──────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1WvPyKF1Enq4fqPHRtJi54SaklpQ54TNjcMicvaw6ZkA/edit?gid=0#gid=0"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_url(SHEET_URL)
ws = sh.sheet1

# ──────────────────────────────────────────────────────────────
# 사용자 로그인
# ──────────────────────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

user_id = st.text_input("📌 학번(ID)을 입력하세요")
if not user_id:
    st.stop()

user_data = ws.get_all_records()
df_users = pd.DataFrame(user_data)

if user_id in df_users["ID"].values:
    user_row = df_users[df_users["ID"] == user_id].iloc[0]
    user_name = user_row["이름"]
    user_grade = user_row["학년"]
    user_major = user_row["전공"]
    user_style = user_row["스타일"]
    st.success(f"환영합니다, {user_name}님!")
else:
    with st.form("user_form"):
        st.subheader("👤 최초 사용자 정보 입력")
        user_name = st.text_input("이름")
        user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
        user_major = st.text_input("전공")
        user_style = st.selectbox("학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
        submitted = st.form_submit_button("정보 저장")

    if submitted:
        ws.append_row([user_id, user_name, user_grade, user_major, user_style])
        st.success("✅ 정보가 저장되었습니다! 페이지를 새로고침해주세요.")
        st.stop()
    else:
        st.stop()

# ──────────────────────────────────────────────────────────────
# 과목 선택 및 환경설정
# ──────────────────────────────────────────────────────────────
course_options = {
    "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH",
}
course_name = st.selectbox("🎓 오늘 들을 강의를 선택하세요", list(course_options.keys()))
folder_id = course_options[course_name]
semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()

# ──────────────────────────────────────────────────────────────
# Drive에서 자료 불러오기
# ──────────────────────────────────────────────────────────────
today = datetime.today()
week_no = get_current_week(semester_start, today.date())
st.info(f"📅 오늘은 {today.strftime('%Y-%m-%d')} / {week_no}주차")

with st.spinner("📂 강의자료를 불러오고 있습니다..."):
    drive_service = get_drive_service_from_secrets(key_dict)
    last_text, this_text, this_pdf_bytes = get_weekly_files_with_binary(
        drive_service, folder_id, week_no
    )

# ──────────────────────────────────────────────────────────────
# PDF 미리보기
# ──────────────────────────────────────────────────────────────
if this_pdf_bytes:
    st.subheader("📑 이번주 강의자료 (PDF 미리보기)")
    st.download_button("📥 PDF 다운로드", data=this_pdf_bytes, file_name=f"{course_name}_{week_no}주차.pdf")
    st.components.v1.iframe("data:application/pdf;base64," + this_pdf_bytes.getvalue().encode("base64").decode(), height=600)

# ──────────────────────────────────────────────────────────────
# GPT + 오디오
# ──────────────────────────────────────────────────────────────
if this_text:
    with st.spinner("💬 GPT 브리핑 생성 중..."):
        last_brief, this_brief = generate_brief(
            user_name, user_grade, user_major, user_style,
            last_week_text=last_text or "",
            this_week_text=this_text,
            subject_name=course_name
        )

    with st.spinner("🎧 오디오 변환 중..."):
        audio_this = text_to_audio(this_brief)
        audio_this.seek(0)

        if week_no > 1 and last_text:
            audio_last = text_to_audio(last_brief)
            audio_last.seek(0)
            st.markdown("### 🔁 지난주차 복습 브리핑")
            st.audio(audio_last, format="audio/mp3")
        elif week_no == 1:
            st.info("이번이 첫 수업입니다 😊 복습 브리핑은 다음주부터 제공돼요!")

        st.markdown("### 🔮 이번주차 예습 브리핑")
        st.audio(audio_this, format="audio/mp3")
else:
    st.warning("❌ 강의자료를 불러올 수 없습니다.")
