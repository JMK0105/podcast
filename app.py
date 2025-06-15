import streamlit as st
from datetime import datetime
import json
from google.oauth2.service_account import Credentials
from drive_handler import (
    get_drive_service_from_secrets, 
    get_current_week, 
    get_weekly_files_with_binary
)
from gpt_brief import generate_brief
from audio_utils import text_to_audio

# ──────────────────────────────────────────────────────────────
# Google Drive 연결
# ──────────────────────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
drive_service = get_drive_service_from_secrets(key_dict)

# ──────────────────────────────────────────────────────────────
# UI: 학습자 정보 입력
# ──────────────────────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

st.markdown("간단한 정보를 입력하면, 오늘 주차의 예습/복습 오디오 브리핑을 들을 수 있어요!")

with st.form("user_form"):
    name = st.text_input("👤 이름")
    grade = st.selectbox("📚 학년", ["1학년", "2학년", "3학년", "4학년"])
    major = st.text_input("🏫 전공")
    course_options = {
        "교육공학": "1k_0XbQO3Jjr1Adgb8XVeqUOX-m1DAh77",
        "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
    }
    course_name = st.selectbox("🎓 수강 중인 강의", list(course_options.keys()))
    style = st.selectbox("🧠 학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
    submitted = st.form_submit_button("🎧 브리핑 듣기")

# ──────────────────────────────────────────────────────────────
# 브리핑 생성 및 오디오 출력
# ──────────────────────────────────────────────────────────────
if submitted:
    if not name or not major:
        st.warning("⚠️ 이름과 전공을 입력해주세요.")
        st.stop()

    folder_id = course_options[course_name]
    semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()
    today = datetime.today()
    week_no = get_current_week(semester_start, today.date())

    st.success(f"📅 오늘은 {today.strftime('%Y-%m-%d')} / {week_no}주차입니다!")

    # 이번 주차 불러오기
    with st.spinner("📂 이번 주차 강의자료 불러오는 중..."):
        last_text, this_text, _ = get_weekly_files_with_binary(drive_service, folder_id, week_no)

    if this_text:
        with st.spinner("💬 이번 주차 GPT 브리핑 생성 중..."):
            last_brief, this_brief = generate_brief(
                name, grade, major, style,
                last_week_text=last_text or "",
                this_week_text=this_text,
                subject_name=course_name
            )

        with st.spinner("🎧 오디오 변환 중..."):
            audio_this = text_to_audio(this_brief)
            audio_this.seek(0)

            st.markdown("### 🔮 이번주차 예습 브리핑")
            st.audio(audio_this, format="audio/mp3")

            if week_no > 1 and last_text:
                audio_last = text_to_audio(last_brief)
                audio_last.seek(0)
                st.markdown("### 🔁 지난주차 복습 브리핑")
                st.audio(audio_last, format="audio/mp3")
    else:
        st.error("❌ 이번 주차 강의자료를 불러올 수 없습니다.")
        st.stop()

    # 이전 주차 브리핑 선택 영역
    if week_no > 1:
        st.markdown("---")
        st.markdown("## ⏪ 이전 주차 브리핑 듣기")
        for past_week in range(1, week_no):
            with st.expander(f"🔊 {past_week}주차 예습 브리핑"):
                with st.spinner(f"📂 {past_week}주차 강의자료 불러오는 중..."):
                    _, prev_text, _ = get_weekly_files_with_binary(drive_service, folder_id, past_week)

                if prev_text:
                    with st.spinner("💬 GPT 브리핑 생성 중..."):
                        _, prev_brief = generate_brief(
                            name, grade, major, style,
                            last_week_text="",  # 복습 생략
                            this_week_text=prev_text,
                            subject_name=course_name
                        )

                    with st.spinner("🎧 오디오 변환 중..."):
                        audio_prev = text_to_audio(prev_brief)
                        audio_prev.seek(0)

                        st.audio(audio_prev, format="audio/mp3")
                else:
                    st.warning("⚠️ 이 주차의 강의자료를 찾을 수 없습니다.")

