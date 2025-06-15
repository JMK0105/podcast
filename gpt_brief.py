import openai
import streamlit as st

# GPT 요약 함수
def generate_brief(name, grade, major, style, last_week_text, this_week_text, subject_name):
    """
    사용자 정보와 수업 자료를 바탕으로 GPT가 예습 및 복습 브리핑을 생성
    :param name: 사용자 이름
    :param grade: 학년
    :param major: 전공
    :param style: 학습 스타일 (개념 중심, 사례 중심, 등)
    :param last_week_text: 전 주차 텍스트 (복습용)
    :param this_week_text: 이번 주차 텍스트 (예습용)
    :param subject_name: 과목 이름
    :return: (복습 브리핑, 예습 브리핑) 튜플
    """

    # 텍스트 길이 제한 (필요 시)
    this_week_text = this_week_text[:5000]
    last_week_text = last_week_text[:3000]

    # 프롬프트 생성
    prompt_template = f"""
당신은 교육 콘텐츠 전문가입니다. 
현재 사용자 이름은 {name}, 학년은 {grade}, 전공은 {major}입니다.
사용자의 선호 학습 스타일은 "{style}"입니다.

당신은 "{subject_name}" 과목의 주차별 학습자료를 기반으로 다음의 두 가지 요약을 생성해야 합니다:

1. 지난주 학습자료에 기반한 복습 브리핑 (짧고 핵심 요약 중심)
2. 이번주 학습자료에 기반한 예습 브리핑 (흥미를 유도하고 중요한 개념 중심)

복습은 간결하게 핵심만 짚어주세요.  
예습은 스토리텔링 또는 대화체로 풀어도 좋으며, 사용자 스타일에 맞게 맞춤형 요약을 제공해주세요.

--- 지난주 학습자료 ---
{last_week_text or "자료 없음"}

--- 이번주 학습자료 ---
{this_week_text}

아래와 같은 포맷으로 출력해주세요:

[복습 브리핑]
...내용...

[예습 브리핑]
...내용...
    """

    try:
        # GPT 호출
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 교육 브리핑 요약 전문가야."},
                {"role": "user", "content": prompt_template}
            ],
            temperature=0.7,
            max_tokens=1024
        )

        output = response.choices[0].message["content"]

        # 결과 분리
        if "[복습 브리핑]" in output and "[예습 브리핑]" in output:
            split = output.split("[예습 브리핑]")
            last_brief = split[0].replace("[복습 브리핑]", "").strip()
            this_brief = split[1].strip()
        else:
            # 혹시 포맷이 다르면 그냥 전체를 예습 브리핑으로 처리
            last_brief = ""
            this_brief = output.strip()

        return last_brief, this_brief

    except Exception as e:
        st.error(f"❌ GPT 브리핑 생성 실패: {e}")
        return "", "브리핑 생성 중 오류가 발생했습니다."
