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
import requests

# ──────────────────────────────────────────────────────────────
# Google Sheets 정보 불러오기
# ──────────────────────────────────────────────────────────────
SHEET_ID = "1WvPyKF1Enq4fqPHRtJi54SaklpQ54TNjcMicvaw6ZkA"
SHEET_NAME = "user_data"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
key_dict = json.loads(st.secrets["gcp_tts_key"])
creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID)
ws = sh.worksheet(SHEET_NAME)

# ✅ 대안 저장 함수 (Google Sheets API 직접 호출)
def append_user_row_direct(sheet_id, values, creds):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{SHEET_NAME}!A1:append"
    params = {
        "valueInputOption": "USER_ENTERED"
    }
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    body = {
        "values": [values]
    }
    response = requests.post(url, headers=headers, params=params, json=body)
    return response.status_code == 200

# ──────────────────────────────────────────────────────────────
# 사용자 로그인 흐름
# ──────────────────────────────────────────────────────────────
st.title("🎧 데일리 학습 브리핑 팟캐스트")

if "registered" not in st.session_state:
    st.session_state.registered = False

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if not st.session_state.registered:
    with st.form("login_form"):
        user_id = st.text_input("📌 학번(ID)을 입력하세요", value=st.session_state.user_id)
        login_submitted = st.form_submit_button("로그인")

    if not login_submitted or not user_id:
        st.stop()

    st.session_state.user_id = user_id
    user_data = ws.get_all_records()
    df_users = pd.DataFrame(user_data)

    if "ID" in df_users.columns and user_id in df_users["ID"].astype(str).values:
        user_row = df_users[df_users["ID"].astype(str) == user_id].iloc[0]
        st.success(f"환영합니다, {user_row['이름']}님!")
        user_name = user_row["이름"]
        user_grade = user_row["학년"]
        user_major = user_row["전공"]
        user_style = user_row["스타일"]
        st.session_state.registered = True
    else:
        st.warning("등록되지 않은 학번입니다. 아래에 정보를 입력해주세요.")
        with st.form("register_form"):
            st.subheader("👤 사용자 등록")
            user_name = st.text_input("이름")
            user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
            user_major = st.text_input("전공")
            user_style = st.selectbox("학습 스타일", ["개념 중심", "사례 중심", "키워드 요약", "스토리텔링"])
            submitted = st.form_submit_button("등록 완료")

        if not submitted:
            st.stop()
        elif not user_name or not user_grade or not user_major or not user_style:
            st.error("⚠️ 모든 정보를 입력해주세요.")
            st.stop()
        else:
            success = append_user_row_direct(
                sheet_id=SHEET_ID,
                values=[user_id, user_name, user_grade, user_major, user_style],
                creds=creds
            )
            if success:
                st.success("✅ 등록이 완료되었습니다! 계속 진행해주세요.")
                st.session_state.registered = True
                st.rerun()
            else:
                st.error("❌ 저장 실패: Google API 오류")
                st.stop()

else:
    user_data = ws.get_all_records()
    df_users = pd.DataFrame(user_data)
    user_row = df_users[df_users["ID"].astype(str) == st.session_state.user_id].iloc[0]
    user_name = user_row["이름"]
    user_grade = user_row["학년"]
    user_major = user_row["전공"]
    user_style = user_row["스타일"]

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
# PDF 다운로드 (미리보기는 브라우저에 따라 차단될 수 있음)
# ──────────────────────────────────────────────────────────────
if this_pdf_bytes:
    st.subheader("📑 이번주 강의자료 다운로드")
    st.download_button("PDF 다운로드", data=this_pdf_bytes, file_name=f"{course_name}_{week_no}주차.pdf")
    st.info("PDF 미리보기는 보안 설정에 따라 차단될 수 있어 다운로드 버튼을 제공합니다.")

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