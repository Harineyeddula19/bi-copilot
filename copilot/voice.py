"""Speech to text using the same provider as the chat model (OpenAI-compatible)."""
import os

from . import llm   # importing llm also loads the .env file

STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")
STT_LANGUAGE = os.getenv("STT_LANGUAGE")      # optional, e.g. "en"


def transcribe(audio_file) -> str:
    data = audio_file.getvalue()
    if len(data) < 2000:
        return ""                              # recording too short to contain speech
    kwargs = {"model": STT_MODEL, "file": ("voice.wav", data)}
    if STT_LANGUAGE:
        kwargs["language"] = STT_LANGUAGE
    result = llm.client.audio.transcriptions.create(**kwargs)
    return (result.text or "").strip()