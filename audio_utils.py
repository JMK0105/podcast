from gtts import gTTS
from io import BytesIO
import streamlit as st


def play_audio(text, lang='ko'):
    tts = gTTS(text, lang=lang)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    st.audio(mp3_fp.read(), format='audio/mp3')
