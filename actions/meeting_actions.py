"""
Records a short meeting/discussion, transcribes it locally with Whisper, and
produces a text summary using the same Groq model as the rest of the
assistant. Note: this uses extra Groq tokens for the summarization call.
"""
import audio_io
import stt
import config
from groq import Groq

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def record_and_summarize_meeting(duration_seconds: int = 60) -> str:
    """Records audio for the given duration, transcribes it, and returns a
    short summary with key points and any action items."""
    duration_seconds = max(10, min(duration_seconds, 600))
    wav_path = audio_io.record_fixed(duration_seconds)
    transcript = stt.transcribe(wav_path)
    audio_io.cleanup(wav_path)

    if not transcript.strip():
        return "I didn't catch any speech during the recording."

    client = _get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        max_tokens=400,
        messages=[
            {
                "role": "system",
                "content": "Summarize this meeting/discussion transcript in a few short bullet points, "
                            "highlighting key decisions and any action items. Be concise.",
            },
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content.strip()
