# app.py (과목 선택 포함 리팩터링)

import streamlit as st
from datetime import datetime
import json
from drive_handler import get_drive_service_from_secrets, get_current_week, get_weekly_files
from gpt_brief import generate_brief
from audio_utils import text_to_audio

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
# 2. 과목 선택 + 환경설정 (secrets 기반)
# ──────────────────────────────────────────────────────────────
course_options = {
    "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
}

course_name = st.selectbox("🎓 오늘 들을 강의를 선택하세요", list(course_options.keys()))
folder_id = course_options[course_name]

semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()
key_dict = json.loads(st.secrets["gcp_tts_key"])

# ──────────────────────────────────────────────────────────────
# 3. 주차 계산 및 Drive 텍스트 추출
# ──────────────────────────────────────────────────────────────
today = datetime.today()
week_no = get_current_week(semester_start, today.date())

st.info(f"📅 오늘은 {today.strftime('%Y-%m-%d')} / 학기 {week_no}주차입니다.\n📘 선택한 과목: {course_name}")

with st.spinner("📂 강의자료를 불러오고 있습니다..."):
    drive_service = get_drive_service_from_secrets(key_dict)
    last_text, this_text = get_weekly_files(drive_service, folder_id, week_no)

# ──────────────────────────────────────────────────────────────
# 4. GPT 요약 및 오디오 생성
# ──────────────────────────────────────────────────────────────
if last_text and this_text:
    st.success("✅ 자료 불러오기 성공!")

    # GPT 요약 생성
    last_brief, this_brief = generate_brief(
        user_name=user_name,
        user_grade=user_grade,
        user_major=user_major,
        user_style=user_style,
        last_week_text=last_text,
        this_week_text=this_text,
        subject_name=course_name
    )

    # 오디오 생성
    audio_last = text_to_audio(last_brief)
    audio_last.seek(0)
    audio_this = text_to_audio(this_brief)
    audio_this.seek(0)

    # ──────────────────────────────────────────────────────────────
    # 5. 오디오 재생
    # ──────────────────────────────────────────────────────────────
    st.markdown("### 🔁 지난주차 복습 브리핑")
    st.audio(audio_last, format="audio/mp3")

    st.markdown("### 🔮 이번주차 예습 브리핑")
    st.audio(audio_this, format="audio/mp3")

else:
    st.warning("⚠️ 해당 주차의 강의자료를 찾을 수 없습니다. 폴더명 또는 파일명을 확인하세요.")
