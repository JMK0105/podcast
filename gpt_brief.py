import openai
import os

# ✅ OpenAI API 키 설정 (환경변수 또는 직접 입력)
openai.api_key = os.getenv("OPENAI_API_KEY")  # 또는 직접 문자열로 입력


def generate_briefing(text, subject_name):
    prompt = f"""
    당신은 학생의 예습을 돕는 에듀테크 AI입니다.
    다음은 "{subject_name}" 수업의 강의자료입니다.
    이 내용을 바탕으로 핵심 개념을 정리하고, 
    오늘 수업에서 주목해야 할 포인트를 설명하는 예습용 브리핑을 500자 내외로 작성해주세요.
    반드시 학생 친화적인 말투로 구성하고, 결론에 질문 하나를 던져주세요.

    자료:
    {text[:4000]}  # GPT 입력 토큰 제한 대비 슬라이싱
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 교육 브리핑 챗봇이야."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()
