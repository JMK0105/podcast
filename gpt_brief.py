import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_brief(name, grade, major, style, last_week_text, this_week_text, subject_name):
    this_week_text = this_week_text[:5000]
    last_week_text = last_week_text[:3000]

    prompt = f"""
당신은 교육 콘텐츠 전문가입니다.  
현재 사용자 이름은 {name}, 학년은 {grade}, 전공은 {major}입니다.  
선호 학습 스타일은 "{style}"입니다.  

과목명은 "{subject_name}"이며, 아래와 같은 요약을 만들어주세요:

[복습 브리핑]
지난주 자료 요약:

{last_week_text or '자료 없음'}

[예습 브리핑]
이번주 자료 요약:

{this_week_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 교육 브리핑 요약 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )

        output = response.choices[0].message.content

        if "[복습 브리핑]" in output and "[예습 브리핑]" in output:
            parts = output.split("[예습 브리핑]")
            last_brief = parts[0].replace("[복습 브리핑]", "").strip()
            this_brief = parts[1].strip()
        else:
            last_brief = ""
            this_brief = output.strip()

        return last_brief, this_brief

    except Exception as e:
        st.error(f"❌ GPT 브리핑 생성 실패: {e}")
        return "", "GPT 브리핑 생성 중 오류가 발생했습니다."
