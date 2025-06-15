from google.cloud import texttospeech
from google.oauth2.service_account import Credentials
import io
import json
import streamlit as st

# ✅ Google TTS 클라이언트 생성 (서비스 계정 명시적으로 전달)
def get_tts_client():
    key_dict = json.loads(st.secrets["gcp_tts_key"])
    creds = Credentials.from_service_account_info(key_dict)
    return texttospeech.TextToSpeechClient(credentials=creds)

# ✅ 텍스트를 MP3 오디오로 변환

def text_to_audio(text):
    try:
        client = get_tts_client()

        input_text = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )

        return io.BytesIO(response.audio_content)

    except Exception as e:
        st.error(f"❌ 오디오 생성 실패: {e}")
        return None
