import streamlit as st
import datetime
from gtts import gTTS
from io import BytesIO
from auth_drive import authenticate_and_get_service
from drive_handler import get_week_folder_file, extract_text_from_file
from gpt_brief import generate_briefing
from audio_utils import play_audio

# ------------------- 기본 설정 ------------------- #
st.set_page_config(page_title="📚 데일리 예습 브리핑", layout="wide")
st.title("🎧 수업 예습 자동 브리핑 시스템")

# ------------------- 사용자 입력 ------------------- #
with st.sidebar:
    st.header("👤 사용자 정보")
    user_name = st.text_input("이름")
    user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년"])
    user_major = st.text_input("전공")

    st.markdown("---")
    st.header("📆 수업 정보")
    selected_course = st.selectbox("수업명", ["교육공학", "심리학입문"])  # 예시
    course_schedule = {
        "교육공학": {"요일": ["화요일", "목요일"], "folder_id": "1AbcDxxx..."},
        "심리학입문": {"요일": ["수요일"], "folder_id": "1ZyxWxxx..."},
    }

# ------------------- 오늘 수업인지 확인 ------------------- #
today = datetime.datetime.today()
today_weekday = today.strftime('%A')  # 'Tuesday', 'Wednesday' 등 영어 요일
korean_weekday = {
    'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
    'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
}[today_weekday]

course_info = course_schedule[selected_course]

if korean_weekday in course_info["요일"]:
    st.success(f"오늘은 📘 {selected_course} 수업이 있는 날입니다. 예습 브리핑을 생성합니다!")

    # ------------------- Google Drive 연동 ------------------- #
    service = authenticate_and_get_service()
    file = get_week_folder_file(service, course_info["folder_id"], today)

    if file:
        with st.spinner("강의자료 불러오는 중..."):
            text = extract_text_from_file(service, file)
            if text:
                with st.spinner("GPT로 예습 요약 중..."):
                    briefing = generate_briefing(text, selected_course)
                    st.subheader("📜 브리핑 스크립트")
                    st.markdown(briefing)

                    with st.spinner("🎧 오디오 생성 중..."):
                        tts = gTTS(briefing, lang='ko')
                        mp3_fp = BytesIO()
                        tts.write_to_fp(mp3_fp)
                        mp3_fp.seek(0)
                        st.audio(mp3_fp.read(), format='audio/mp3')
            else:
                st.warning("📄 강의자료에서 텍스트를 추출할 수 없습니다.")
    else:
        st.warning("📁 오늘 주차에 해당하는 강의자료를 찾을 수 없습니다.")
else:
    st.info(f"오늘은 {selected_course} 수업이 없는 날입니다.")
