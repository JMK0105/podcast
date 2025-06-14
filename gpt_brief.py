import openai
import os

# ✅ OpenAI API 키 설정 (환경변수 또는 직접 입력)
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_brief(user_name, user_grade, user_major, user_style, last_week_text, this_week_text, subject_name="수업"):
    # 🔁 복습용 프롬프트
    last_prompt = f"""
    당신은 대학생 '{user_grade}'학년 '{user_major}' 전공 학습자에게 친절하게 설명하는 에듀테크 AI입니다.
    이 학습자는 '{user_style}' 스타일을 선호합니다.

    다음은 지난주 "{subject_name}" 수업의 강의자료입니다.
    복습을 위해 지난 내용을 요약 정리하고, 핵심 개념을 간결하게 정리해주세요.
    결론에 이번 내용을 간단히 되새기는 질문을 추가해주세요.

    자료:
    {last_week_text[:3500]}
    """

    # 🔮 예습용 프롬프트
    this_prompt = f"""
    당신은 대학생 '{user_grade}'학년 '{user_major}' 전공 학습자에게 설명하는 에듀테크 AI입니다.
    이 학습자는 '{user_style}' 스타일을 선호합니다.

    다음은 오늘 들을 "{subject_name}" 수업의 강의자료입니다.
    예습을 위해 핵심 개념을 정리하고, 어떤 주제에 주목하면 좋을지 알려주세요.
    결론에는 흥미를 유도하는 질문을 추가해주세요.

    자료:
    {this_week_text[:3500]}
    """

    # GPT 요청
    def get_completion(prompt):
        response = openai.ChatCompletion.create(
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
