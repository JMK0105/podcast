# gpt_brief.py (OpenAI v1 SDK 호환 버전)

from openai import OpenAI
import os

# ✅ OpenAI 클라이언트 초기화 (환경변수 기반)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_brief(user_name, user_grade, user_major, user_style, last_week_text, this_week_text, subject_name):
    # 지난주 요약
    last_prompt = f"""
    당신은 친절한 학습 브리핑 챗봇입니다.
    아래는 지난주 {subject_name} 수업의 강의자료입니다.
    복습을 돕기 위해 핵심 내용을 요약하고, 다음 수업과 연결될 수 있는 한 가지 질문으로 마무리해주세요.

    학습자 정보:
    - 이름: {user_name}
    - 학년: {user_grade}
    - 전공: {user_major}
    - 선호 스타일: {user_style}

    자료:
    {last_week_text[:4000]}
    """

    # 이번주 예습 요약
    this_prompt = f"""
    당신은 학생의 예습을 돕는 에듀테크 AI입니다.
    다음은 이번주 {subject_name} 수업의 강의자료입니다.
    핵심 개념을 정리하고, 이번 수업에서 주목해야 할 포인트를 친근한 말투로 500자 내외로 정리해주세요. 마지막에 질문 한 개를 던져주세요.

    학습자 정보:
    - 이름: {user_name}
    - 학년: {user_grade}
    - 전공: {user_major}
    - 선호 스타일: {user_style}

    자료:
    {this_week_text[:4000]}
    """

    def get_completion(prompt):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 교육 브리핑 챗봇이야."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()

    last_brief = get_completion(last_prompt)
    this_brief = get_completion(this_prompt)
    return last_brief, this_brief
