from google.cloud import texttospeech
from io import BytesIO
import streamlit as st
import json

def text_to_audio(text, json_key=None, voice_name="ko-KR-Wavenet-B"):
    # ✅ secrets.toml에 저장된 키를 불러옴
    if json_key is None:
        json_key = json.loads(st.secrets["gcp_tts_key"])  # 문자열 → dict 변환

    # ✅ from_service_account_info 사용 (파일이 아니라 dict)
    client = texttospeech.TextToSpeechClient.from_service_account_info(json_key)

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    mp3_fp = BytesIO(response.audio_content)
    return mp3_fp
