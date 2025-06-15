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
from user_manager import get_user_df, is_existing_user, get_user_row, register_user

# ──────────────────────────────────────────────────────────────
# Google Sheets 연결
# ──────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1WvPyKF1Enq4fqPHRtJi54SaklpQ54TNjcMicvaw6ZkA/edit#gid=0"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_url(SHEET_URL)
ws = sh.worksheet("user_data")

# ──────────────────────────────────────────────────────────────
# 세션 초기화
# ──────────────────────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

if "registered" not in st.session_state:
    st.session_state.registered = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# ──────────────────────────────────────────────────────────────
# 로그인 또는 회원가입
# ──────────────────────────────────────────────────────────────
if not st.session_state.registered:
    with st.form("login_form"):
        user_id = st.text_input("📌 학번(ID)을 입력하세요", value=st.session_state.user_id)
        login_submitted = st.form_submit_button("로그인")

    if not login_submitted or not user_id:
        st.stop()

    st.session_state.user_id = user_id
    df_users = get_user_df(ws)

    if is_existing_user(df_users, user_id):
        user_row = get_user_row(df_users, user_id)
        if user_row is None:
            st.error("❌ 사용자 정보를 불러오는 데 실패했습니다.")
            st.stop()

        st.success(f"환영합니다, {user_row['이름']}님!")
        st.session_state.user_info = {
            "이름": user_row["이름"],
            "학년": user_row["학년"],
            "전공": user_row["전공"],
            "스타일": user_row["스타일"]
        }
        st.session_state.registered = True
        st.rerun()
    else:
        st.warning("등록되지 않은 학번입니다. 아래에 정보를 입력해주세요.")
        with st.form("register_form"):
            st.subheader("👤 사용자 등록")
            user_id = st.text_input("📌 학번(ID)", value=user_id)
            user_name = st.text_input("이름")
            user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
            user_major = st.text_input("전공")
            user_style = st.selectbox("학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
            submitted = st.form_submit_button("등록 완료")

        if not submitted:
            st.stop()
        elif not user_id or not user_name or not user_grade or not user_major or not user_style:
            st.error("⚠️ 모든 정보를 입력해주세요.")
            st.stop()
        else:
            if register_user(ws, user_id, user_name, user_grade, user_major, user_style):
                st.session_state.registered = True
                st.session_state.user_id = user_id
                st.session_state.user_info = {
                    "이름": user_name,
                    "학년": user_grade,
                    "전공": user_major,
                    "스타일": user_style
                }
                st.success("✅ 등록이 완료되었습니다! 계속 진행해주세요.")
                st.rerun()
            else:
                st.error("❌ 등록 실패")
                st.stop()

# ──────────────────────────────────────────────────────────────
# 사용자 정보 불러오기
# ──────────────────────────────────────────────────────────────
user_name = st.session_state.user_info.get("이름", "")
user_grade = st.session_state.user_info.get("학년", "")
user_major = st.session_state.user_info.get("전공", "")
user_style = st.session_state.user_info.get("스타일", "")

# ──────────────────────────────────────────────────────────────
# 과목 선택 및 환경설정
# ──────────────────────────────────────────────────────────────
course_options = {
    "교육공학": "1k_0XbQO3Jjr1Adgb8XVeqUOX-m1DAh77",
    "학습과학": "1OpgPDpJmvSEy5RyWNiO-_x1Fcybf1ENH"
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
# PDF 다운로드
# ──────────────────────────────────────────────────────────────
if this_pdf_bytes:
    st.subheader("📑 이번주 강의자료 다운로드")
    st.download_button("PDF 다운로드", data=this_pdf_bytes, file_name=f"{course_name}_{week_no}주차.pdf")
    st.info("PDF 미리보기는 보안 설정에 따라 차단될 수 있어 다운로드 버튼을 제공합니다.")

# ──────────────────────────────────────────────────────────────
# GPT 브리핑 + 오디오 변환
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
