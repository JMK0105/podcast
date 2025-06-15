from google.cloud import texttospeech
from io import BytesIO
import streamlit as st

def text_to_audio(text: str):
    """
    주어진 텍스트를 Google TTS를 사용해 오디오로 변환
    :param text: 브리핑 텍스트
    :return: MP3 BytesIO 객체 or None
    """

    try:
        if not text.strip():
            return None

        # 1. TTS 클라이언트 생성
        client = texttospeech.TextToSpeechClient()

        # 2. 입력 텍스트 (최대 길이 제한 적용)
        synthesis_input = texttospeech.SynthesisInput(text=text[:4999])

        # 3. 음성 설정 (한국어, 중성 음색)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # 4. 출력 오디오 형식
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # 5. TTS 요청 실행
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # 6. Streamlit에 맞게 BytesIO 변환
        audio_stream = BytesIO(response.audio_content)
        return audio_stream

    except Exception as e:
        st.error(f"❌ 오디오 생성 실패: {e}")
        return None
