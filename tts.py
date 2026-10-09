import subprocess
import config


def speak(text: str):
    if not text:
        return
    print(f"🔊 {config.ASSISTANT_NAME}: {text}")
    try:
        subprocess.run(["say", "-v", config.TTS_VOICE, text], check=False)
    except FileNotFoundError:

          print("[TTS unavailable on this system - text shown only]")
