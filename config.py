"""
Voice assistant settings.
All values are read from a .env file (copy .env.example to .env and fill it in).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API key - get one at https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Groq model used as the assistant's "brain" (must support tool-calling).
# Note: llama-3.3-70b-versatile is deprecated on Groq as of mid-2026.
# openai/gpt-oss-120b is the current recommended tool-calling model.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Assistant name and wake word
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
WAKE_WORDS = ["hey jarvis", "hey computer", "hey assistant"]  # depends on the openWakeWord model used

# Path to a custom-trained wake word .onnx model (e.g. trained via a Colab
# notebook). Leave empty/unset to use the bundled "hey_jarvis" model instead.
CUSTOM_WAKE_WORD_MODEL_PATH = os.getenv("CUSTOM_WAKE_WORD_MODEL_PATH", "")

# macOS voice used for replies (see available voices with: say -v '?')
TTS_VOICE = os.getenv("TTS_VOICE", "Samantha")  # English voice built into macOS

# Local Whisper model for speech-to-text (tiny/base/small/medium/large-v3)
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

# How long to record a command after the wake word (in seconds)
COMMAND_RECORD_SECONDS = 6

# Text-only mode (no microphone needed: type instead of speaking)
TEXT_ONLY_MODE = os.getenv("TEXT_ONLY_MODE", "false").lower() == "true"

# Topic name for phone push notifications via ntfy.sh (free, no signup).
# Pick any unique-ish name, e.g. "jarvis-alerts-yourname", and subscribe to
# it in the ntfy app on your phone. Leave empty to disable.
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")

# Secret token required to use the phone-control web server. Auto-generated
# and saved to .env the first time you enable phone control from the menu
# bar app, so you don't need to set this yourself.
SERVER_AUTH_TOKEN = os.getenv("SERVER_AUTH_TOKEN", "")
