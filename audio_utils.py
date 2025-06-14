from google.cloud import texttospeech
from io import BytesIO
import streamlit as st

def play_audio(text, json_key_path="gcp_tts_key.json", voice_name="ko-KR-Wavenet-B"):
    # GCP 서비스 계정 키 파일 기반 인증
    client = texttospeech.TextToSpeechClient.from_service_account_file(json_key_path)

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=voice_name,  # 예: Wavenet-B: 중립적 남성음 / Wavenet-A: 여성음
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    mp3_fp = BytesIO(response.audio_content)
    st.audio(mp3_fp.read(), format='audio/mp3')
