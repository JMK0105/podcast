# app.py

import streamlit as st
from datetime import datetime
from drive_handler import get_weekly_files, get_current_week
from auth_drive import authenticate_and_get_drive
from gpt_brief import generate_brief
from audio_utils import text_to_audio

# ▶️ 설정값
SEMESTER_START = datetime(2025, 3, 4).date()
DRIVE_FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID"  # 수정 필요

# ──────────────────────────────────────────────────────────────
# 1. 학습자 정보 입력
# ──────────────────────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

with st.form("user_form"):
    st.subheader("👤 학습자 정보 입력")
    user_name = st.text_input("이름")
    user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
    user_major = st.text_input("전공")
    user_style = st.selectbox("학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
    submitted = st.form_submit_button("입력 완료")

if not submitted:
    st.stop()

# ──────────────────────────────────────────────────────────────
# 2. Drive 인증 및 오늘 날짜 기반 자료 불러오기
# ──────────────────────────────────────────────────────────────
drive = authenticate_and_get_drive()
today = datetime.today()
today_week = get_current_week(SEMESTER_START, today.date())

st.info(f"📅 오늘은 {today.strftime('%Y-%m-%d')} / 학기 {today_week}주차입니다.")

with st.spinner("📂 강의 자료를 불러오고 있습니다..."):
    last_text, this_text = get_weekly_files(drive, today_week, folder_id=DRIVE_FOLDER_ID)

# ──────────────────────────────────────────────────────────────
# 3. GPT 요약 및 오디오 생성
# ──────────────────────────────────────────────────────────────
if last_text and this_text:
    st.success("✅ 자료 불러오기 성공!")

    # GPT 요약
    last_brief, this_brief = generate_brief(
        user_name=user_name,
        user_grade=user_grade,
        user_major=user_major,
        user_style=user_style,
        last_week_text=last_text,
        this_week_text=this_text,
        subject_name="교육공학"
    )

    # TTS 오디오 생성
    audio_last = text_to_audio(last_brief)
    audio_last.seek(0)

    audio_this = text_to_audio(this_brief)
    audio_this.seek(0)

    # ──────────────────────────────────────────────────────────────
    # 4. 오디오 재생 UI
    # ──────────────────────────────────────────────────────────────
    st.markdown("### 🔁 지난주차 복습 브리핑")
    st.audio(audio_last, format="audio/mp3")

    st.markdown("### 🔮 이번주차 예습 브리핑")
    st.audio(audio_this, format="audio/mp3")

else:
    st.warning("해당 주차의 강의 자료를 찾을 수 없습니다.")
