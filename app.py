import streamlit as st
import openai
from gtts import gTTS
import tempfile
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime
import json

# ------------------------
# Google Drive 연동
# ------------------------
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

drive = authenticate_drive()

# ------------------------
# 주차 자동 인식 로직
# ------------------------
def get_current_week():
    semester_start = datetime(datetime.now().year, 3, 1)  # 예: 3월 1일 개강
    today = datetime.now()
    week_number = ((today - semester_start).days // 7) + 1
    return max(1, week_number)

# ------------------------
# 드라이브 폴더 탐색 및 파일 불러오기
# ------------------------
def list_week_folders(course_folder_id):
    file_list = drive.ListFile({
        'q': f"'{course_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    }).GetList()
    week_folders = sorted(file_list, key=lambda x: x['title'])
    return [(f['title'], f['id']) for f in week_folders]

def get_txt_file_from_folder(folder_id):
    file_list = drive.ListFile({
        'q': f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false"
    }).GetList()
    for f in file_list:
        if f['title'].endswith('.txt'):
            file = drive.CreateFile({'id': f['id']})
            file.GetContentFile(f['title'])
            with open(f['title'], 'r', encoding='utf-8') as ftxt:
                content = ftxt.read()
            os.remove(f['title'])
            return content
    return ""

# ------------------------
# 학습 이력 저장 및 회고 분석 기반 스타일 튜닝
# ------------------------
def save_learning_log(name, week, briefing_type, feedback, reflection):
    log = {
        "user": name,
        "week": week,
        "type": briefing_type,
        "feedback": feedback,
        "reflection": reflection,
        "timestamp": datetime.now().isoformat()
    }
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{name}_log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

def suggest_style_update(reflection, feedback, api_key):
    openai.api_key = api_key
    prompt = f"""
    아래는 학습자의 회고와 브리핑에 대한 피드백입니다.

    회고 내용: {reflection}
    피드백: {feedback}

    학습자의 표현 방식, 내용 선호도, 어조 등을 분석해서
    다음 브리핑에 추천할 스타일을 예측해줘.
    예시 형태로 다음과 같이 답해줘:

    예습 스타일 추천: 예시 중심
    복습 스타일 추천: 질문 중심
    톤 추천: 따뜻하고 격려
    유형 분석: 설명보다 예시를 좋아하고, 생각할 질문을 주는 걸 선호함.
    """
    res = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 학습자의 회고와 피드백을 분석해 학습 스타일을 추천하는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content.strip()

# ------------------------
# 초기 세팅
# ------------------------
if "profile" not in st.session_state:
    st.session_state["profile"] = {}
if "feedback_history" not in st.session_state:
    st.session_state["feedback_history"] = []

# ------------------------
# 사이드바: 학습자 정보
# ------------------------
with st.sidebar:
    st.header("👩‍🏫 학습자 정보")
    name = st.text_input("이름", value="민경")
    level = st.selectbox("학습 수준", ["기초", "중급", "심화"])
    interest = st.text_input("관심 분야", value="과학")

# ------------------------
# 진단
# ------------------------
st.title("🎧 PrePostCast: 예습/복습 AI 브리핑")

if "initialized" not in st.session_state:
    with st.form("initial_form"):
        st.subheader("🧠 간단한 학습 스타일 진단")
        preview_style = st.selectbox("예습할 때 가장 도움이 되는 방식은?", ["핵심 요약", "질문 중심", "예시 중심"])
        review_style = st.selectbox("복습할 때 가장 편한 방식은?", ["요약 정리", "내가 말하면서 정리", "예시나 사례"])
        style_pref = st.selectbox("전체적으로 어떤 톤을 선호하나요?", ["간단 명료", "따뜻하고 격려", "재미있고 친근"])

        submitted = st.form_submit_button("저장하고 시작하기")
        if submitted:
            st.session_state["profile"] = {
                "name": name,
                "level": level,
                "interest": interest,
                "preview_style": preview_style,
                "review_style": review_style,
                "style_pref": style_pref
            }
            st.session_state["initialized"] = True
            st.success("설정이 저장되었습니다! 이제 브리핑을 시작해보세요.")

# ------------------------
# 브리핑 섹션
# ------------------------
if st.session_state.get("initialized"):
    st.subheader("📁 Google Drive에서 수업자료 자동 불러오기")
    course_folder_id = st.text_input("Google Drive 강의 폴더 ID 입력", "")

    if course_folder_id:
        week_folders = list_week_folders(course_folder_id)
        current_week = get_current_week()
        default_index = min(current_week - 1, len(week_folders) - 1)
        week_options = [f"{i+1}주차 - {title}" for i, (title, _) in enumerate(week_folders)]
        selected_index = st.selectbox("주차 선택", range(len(week_options)), format_func=lambda i: week_options[i], index=default_index)
        selected_folder_id = week_folders[selected_index][1]
        content = get_txt_file_from_folder(selected_folder_id)

        briefing_type = st.radio("브리핑 종류 선택", ["예습", "복습"])
        openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")

        if content and openai_api_key:

            def make_prompt(profile, briefing_type, content):
                return f"""
                너는 '{profile['name']}'라는 학습자를 위한 AI 학습 도우미야.
                학습자의 정보는 다음과 같아:
                - 수준: {profile['level']}
                - 관심사: {profile['interest']}
                - 예습 선호 스타일: {profile['preview_style']}
                - 복습 선호 스타일: {profile['review_style']}
                - 말투 선호: {profile['style_pref']}

                아래는 수업자료야. {briefing_type} 목적에 맞게 스크립트를 구성해줘.
                친근한 말투로 구성하고, 마지막엔 간단한 질문 하나 넣어줘.

                수업자료:
                {content}
                """

            def ask_gpt(prompt, api_key):
                openai.api_key = api_key
                res = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "너는 학습자 맞춤 브리핑을 제공하는 AI야."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return res.choices[0].message.content.strip()

            def text_to_audio(text):
                tts = gTTS(text, lang="ko")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_file.name)
                return temp_file.name

            if st.button("🎙️ 브리핑 생성"):
                with st.spinner("브리핑을 생성 중입니다..."):
                    user_profile = st.session_state["profile"]
                    prompt = make_prompt(user_profile, briefing_type, content)
                    summary = ask_gpt(prompt, openai_api_key)
                    audio_path = text_to_audio(summary)

                    st.markdown("### 🗒️ 브리핑 스크립트")
                    st.write(summary)

                    st.markdown("### 🎧 오디오 브리핑")
                    audio_file = open(audio_path, "rb")
                    st.audio(audio_file.read(), format="audio/mp3")
                    audio_file.close()
                    os.remove(audio_path)

                    st.markdown("### 🤔 어땠나요?")
                    feedback = st.radio("브리핑에 대한 느낌을 알려주세요", ["좋았어요", "조금 어려웠어요", "스타일을 바꾸고 싶어요"])
                    reflection = st.text_area("오늘 학습에서 가장 기억에 남는 내용은 무엇인가요?", "")

                    st.session_state["feedback_history"].append(feedback)
                    save_learning_log(user_profile['name'], selected_index + 1, briefing_type, feedback, reflection)

                    st.success("피드백과 회고가 저장되었습니다. 다음 브리핑에 반영할게요!")

                    if reflection and openai_api_key:
                        st.markdown("### 🧠 스타일 추천 분석")
                        suggestion = suggest_style_update(reflection, feedback, openai_api_key)
                        st.info(suggestion)
