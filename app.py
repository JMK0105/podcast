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

# ───────────────────────────────────────────────
# Google Drive 연결
# ───────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
drive_service = get_drive_service_from_secrets(key_dict)

# ───────────────────────────────────────────────
# UI: 사용자 정보 입력
# ───────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

with st.form("user_form"):
    name = st.text_input("👤 이름")
    grade = st.selectbox("📚 학년", ["1학년", "2학년", "3학년", "4학년"])
    major = st.text_input("🏫 전공")
    course_options = {
        "교육공학": "1k_0XbQO3Jjr1Adgb8XVeqUOX-m1DAh77",
        "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
    }
    course_name = st.selectbox("🎓 수강 강의", list(course_options.keys()))
    style = st.selectbox("🧠 학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
    submitted = st.form_submit_button("➡️ 다음으로")

if not submitted or not name or not major:
    st.stop()

# ───────────────────────────────────────────────
# 기본 변수 설정
# ───────────────────────────────────────────────
folder_id = course_options[course_name]
semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()
today = datetime.today()
week_no = get_current_week(semester_start, today.date())

st.success(f"🗓️ 오늘은 {today.strftime('%Y-%m-%d')} / 현재 {week_no}주차입니다.")

# ───────────────────────────────────────────────
# 학습 유형 선택 메뉴
# ───────────────────────────────────────────────
mode = st.radio(
    "무엇을 듣고 싶으신가요?",
    ["📘 이번주 예습하기", "📗 지난주까지 복습하기", "📙 특정 주차 선택하기"]
)

# ───────────────────────────────────────────────
# 예습: 이번 주차
# ───────────────────────────────────────────────
if mode == "📘 이번주 예습하기":
    with st.spinner("📂 강의자료 로딩 중..."):
        last_text, this_text, _ = get_weekly_files_with_binary(drive_service, folder_id, week_no)

    if this_text:
        with st.spinner("💬 GPT 예습 브리핑 생성 중..."):
            last_brief, this_brief = generate_brief(
                name, grade, major, style,
                last_week_text=last_text or "",
                this_week_text=this_text,
                subject_name=course_name
            )
        with st.spinner("🎧 오디오 변환 중..."):
            st.markdown("### 🔮 이번주 예습 브리핑")
            audio_this = text_to_audio(this_brief)
            audio_this.seek(0)
            st.audio(audio_this, format="audio/mp3")

            if week_no > 1 and last_text:
                st.markdown("### 🔁 지난주 복습 브리핑")
                audio_last = text_to_audio(last_brief)
                audio_last.seek(0)
                st.audio(audio_last, format="audio/mp3")
    else:
        st.error("❌ 이번 주차 자료가 없습니다.")

# ───────────────────────────────────────────────
# 복습: 1주차부터 (이번주-1)까지 반복
# ───────────────────────────────────────────────
elif mode == "📗 지난주까지 복습하기":
    if week_no <= 1:
        st.info("복습할 내용이 아직 없습니다!")
    else:
        for w in range(1, week_no):
            with st.spinner(f"📂 {w}주차 강의자료 로딩 중..."):
                _, text, _ = get_weekly_files_with_binary(drive_service, folder_id, w)

            if text:
                with st.spinner("💬 GPT 브리핑 생성 중..."):
                    _, brief = generate_brief(
                        name, grade, major, style,
                        last_week_text="",
                        this_week_text=text,
                        subject_name=course_name
                    )
                with st.spinner("🎧 오디오 변환 중..."):
                    st.markdown(f"### 📖 {w}주차 예습 브리핑")
                    audio = text_to_audio(brief)
                    audio.seek(0)
                    st.audio(audio, format="audio/mp3")
            else:
                st.warning(f"⚠️ {w}주차 자료가 없습니다.")

# ───────────────────────────────────────────────
# 주차 선택: 드롭다운으로 원하는 주차 선택
# ───────────────────────────────────────────────
elif mode == "📙 특정 주차 선택하기":
    available_weeks = list(range(1, week_no + 1))
    selected_week = st.selectbox("🎯 듣고 싶은 주차를 선택하세요", available_weeks)

    with st.spinner(f"📂 {selected_week}주차 강의자료 로딩 중..."):
        _, text, _ = get_weekly_files_with_binary(drive_service, folder_id, selected_week)

    if text:
        with st.spinner("💬 GPT 브리핑 생성 중..."):
            _, brief = generate_brief(
                name, grade, major, style,
                last_week_text="",
                this_week_text=text,
                subject_name=course_name
            )
        with st.spinner("🎧 오디오 변환 중..."):
            st.markdown(f"### 🎧 {selected_week}주차 예습 브리핑")
            audio = text_to_audio(brief)
            audio.seek(0)
            st.audio(audio, format="audio/mp3")
    else:
        st.warning("⚠️ 선택한 주차의 자료가 없습니다.")