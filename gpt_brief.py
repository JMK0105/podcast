import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------
# 복습 브리핑 생성
# --------------------------
def generate_last_brief(name, grade, major, style, last_week_text, subject_name):
    if not last_week_text.strip():
        return ""

    prompt = f"""
당신은 교육 콘텐츠 요약 전문가입니다.
사용자 이름은 {name}, 학년은 {grade}, 전공은 {major}이며, 학습 스타일은 "{style}"입니다.
과목명은 "{subject_name}"입니다.

다음은 지난 주 수업 자료입니다. 이를 약 700자 이내로 복습 브리핑 형식으로 요약해주세요.
\n\n{last_week_text[:2000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 친절하고 전문적인 교육 브리핑 요약 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"❌ 복습 브리핑 생성 실패: {e}")
        return ""

# --------------------------
# 예습 브리핑 생성
# --------------------------
def generate_this_brief(name, grade, major, style, this_week_text, subject_name):
    if not this_week_text.strip():
        return ""

    prompt = f"""
당신은 교육 콘텐츠 요약 전문가입니다.
사용자 이름은 {name}, 학년은 {grade}, 전공은 {major}이며, 학습 스타일은 "{style}"입니다.
과목명은 "{subject_name}"입니다.

다음은 이번 주 수업 자료입니다. 학습자가 수업 전에 내용을 빠르게 이해할 수 있도록, 핵심 개념 중심으로 700자 이내로 예습 브리핑을 작성해주세요.
\n\n{this_week_text[:2500]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 친절하고 전문적인 교육 브리핑 요약 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"❌ 예습 브리핑 생성 실패: {e}")
        return ""
