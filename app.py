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
# Streamlit 세션 상태 초기화
# ───────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "선택"

# ───────────────────────────────────────────────
# Google Drive API 연결
# ───────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
drive_service = get_drive_service_from_secrets(key_dict)

# ───────────────────────────────────────────────
# Sidebar - 사용자 정보 입력
# ───────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 학습자 정보 입력")
    name = st.text_input("👤 이름")
    grade = st.selectbox("📚 학년", ["1학년", "2학년", "3학년", "4학년"])
    major = st.text_input("🏫 전공")
    course_options = {
        "교육공학": "1k_0XbQO3Jjr1Adgb8XVeqUOX-m1DAh77",
        "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
    }
    course_name = st.selectbox("🎓 수강 강의", list(course_options.keys()))
    style = st.selectbox("🧠 학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])

if not name or not major:
    st.warning("⛔ 이름과 전공을 입력해주세요 (사이드바).")
    st.stop()

# ───────────────────────────────────────────────
# 공통 변수 설정
# ───────────────────────────────────────────────
folder_id = course_options[course_name]
semester_start = datetime.strptime(st.secrets["semester_start"], "%Y-%m-%d").date()
today = datetime.today()
week_no = get_current_week(semester_start, today.date())

# ───────────────────────────────────────────────
# STEP 1: 모드 선택 페이지
# ───────────────────────────────────────────────
if st.session_state.current_page == "선택":
    st.title("🎧 데일리 학습 브리핑")
    st.success(f"📅 오늘은 {today.strftime('%Y-%m-%d')} / 현재 {week_no}주차입니다.")
    selected_mode = st.radio(
        "무엇을 듣고 싶으신가요?",
        ["📘 이번주 예습", "📗 전체 복습", "📙 주차 선택"],
        key="learning_mode"
    )
    if st.button("▶️ 선택 완료"):
        st.session_state.current_page = selected_mode
        st.rerun()

# ───────────────────────────────────────────────
# STEP 2-1: 이번주 예습
# ───────────────────────────────────────────────
elif st.session_state.current_page == "📘 이번주 예습":
    st.title("📘 이번주 예습 브리핑")
    if st.button("⬅️ 뒤로"):
        st.session_state.current_page = "선택"
        st.rerun()

    with st.spinner("📂 강의자료 불러오는 중..."):
        last_text, this_text, _ = get_weekly_files_with_binary(drive_service, folder_id, week_no)

    if this_text:
        with st.spinner("💬 GPT 브리핑 생성 중..."):
            last_brief, this_brief = generate_brief(name, grade, major, style, last_text or "", this_text, course_name)

        audio_this = text_to_audio(this_brief)
        if audio_this:
            audio_this.seek(0)
            st.markdown("### 🔮 이번주 예습 브리핑")
            st.audio(audio_this, format="audio/mp3")
        else:
            st.error("❌ 오디오 생성 실패")

        if week_no > 1 and last_text:
            audio_last = text_to_audio(last_brief)
            if audio_last:
                audio_last.seek(0)
                st.markdown("### 🔁 지난주 복습 브리핑")
                st.audio(audio_last, format="audio/mp3")
    else:
        st.warning("이번 주차 자료를 불러올 수 없습니다.")

# ───────────────────────────────────────────────
# STEP 2-2: 전체 복습
# ───────────────────────────────────────────────
elif st.session_state.current_page == "📗 전체 복습":
    st.title("📗 지난주까지 복습하기")
    if st.button("⬅️ 뒤로"):
        st.session_state.current_page = "선택"
        st.rerun()

    if week_no <= 1:
        st.info("아직 복습할 주차가 없습니다!")
    else:
        for w in range(1, week_no):
            with st.spinner(f"📂 {w}주차 자료 불러오는 중..."):
                _, text, _ = get_weekly_files_with_binary(drive_service, folder_id, w)

            if text:
                with st.spinner("💬 GPT 브리핑 생성 중..."):
                    _, brief = generate_brief(name, grade, major, style, "", text, course_name)

                audio = text_to_audio(brief)
                if audio:
                    audio.seek(0)
                    st.markdown(f"### 🔁 {w}주차 복습 브리핑")
                    st.audio(audio, format="audio/mp3")
            else:
                st.warning(f"{w}주차 자료를 찾을 수 없습니다.")

# ───────────────────────────────────────────────
# STEP 2-3: 주차 선택
# ───────────────────────────────────────────────
elif st.session_state.current_page == "📙 주차 선택":
    st.title("📙 특정 주차 선택")
    if st.button("⬅️ 뒤로"):
        st.session_state.current_page = "선택"
        st.rerun()

    selected_week = st.selectbox("🎯 듣고 싶은 주차를 선택하세요", list(range(1, week_no + 1)))
    if st.button("🔍 브리핑 보기"):
        with st.spinner(f"📂 {selected_week}주차 자료 불러오는 중..."):
            _, text, _ = get_weekly_files_with_binary(drive_service, folder_id, selected_week)

        if text:
            with st.spinner("💬 GPT 브리핑 생성 중..."):
                _, brief = generate_brief(name, grade, major, style, "", text, course_name)

            audio = text_to_audio(brief)
            if audio:
                audio.seek(0)
                st.markdown(f"### 🎧 {selected_week}주차 예습 브리핑")
                st.audio(audio, format="audio/mp3")
        else:
            st.warning(f"{selected_week}주차 자료를 찾을 수 없습니다.")
