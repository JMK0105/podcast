# audio_utils.py

from google.cloud import texttospeech
from io import BytesIO
import streamlit as st

# 텍스트를 TTS로 변환하고 오디오 스트림 반환
def text_to_audio(text, json_key_path="gcp_tts_key", voice_name="ko-KR-Wavenet-B"):
    # 인증 및 클라이언트 생성
    client = texttospeech.TextToSpeechClient.from_service_account_file(json_key_path)

    # 텍스트 입력
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # 음성 설정
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # 오디오 설정
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # 음성 합성 요청
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # BytesIO 객체로 반환 (메모리 기반 오디오)
    mp3_fp = BytesIO(response.audio_content)
    return mp3_fp

# Streamlit에서 오디오를 재생하는 함수
def play_audio_from_text(text, **kwargs):
    audio_stream = text_to_audio(text, **kwargs)
    st.audio(audio_stream.read(), format='audio/mp3')
