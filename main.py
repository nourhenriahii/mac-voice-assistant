"""
Personal voice assistant - entry point.

Usage:
    python main.py              # full voice mode (wake word + microphone)
    python main.py --text       # text mode (type commands instead of speaking - useful for testing)
"""
import sys
import time
import config
import audio_io
import stt
import tts
from brain import process_command

conversation_history = []


def handle_command(user_text: str):
    """Processes a single command (text) and replies with speech."""
    global conversation_history
    if not user_text.strip():
        return
    print(f"🗣️  You: {user_text}")
    t0 = time.time()
    reply, conversation_history = process_command(user_text, conversation_history)
    print(f"   ⏱️  (brain/Groq took {time.time() - t0:.1f}s)")
    # Keep only the last 10 exchanges to avoid unbounded context growth
    conversation_history = conversation_history[-8:]
    t1 = time.time()
    tts.speak(reply)
    print(f"   ⏱️  (TTS took {time.time() - t1:.1f}s)")


def run_text_mode():
    tts.speak(f"Hi, I'm {config.ASSISTANT_NAME}. Type your command (or 'exit' to quit).")
    while True:
        try:
            user_text = input("👤 > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_text.lower() in ("exit", "quit"):
            break
        handle_command(user_text)


def run_voice_mode():
    """
    Full voice mode: uses openwakeword to detect the wake word, then records
    the command, transcribes it, and executes it.
    Note: openwakeword is optional - if it's not installed, we fall back to
    a simple "press Enter then speak" flow to keep initial setup simple.
    """
    try:
        from wake_word import listen_for_wake_word
        has_wake_word = True
    except ImportError:
        has_wake_word = False

    tts.speak(f"Hi, I'm {config.ASSISTANT_NAME}. Ready to listen.")

    while True:
        try:
            if has_wake_word:
                print("👂 Waiting for the wake word...")
                listen_for_wake_word()
            else:
                input("⏎ Press Enter, then speak your command...")

            # Inner loop: keep listening for follow-up commands without
            # repeating the wake word, until the user goes quiet for a bit.
            while True:
                t_record = time.time()
                wav_path = audio_io.record_until_silence(
                    max_seconds=config.COMMAND_RECORD_SECONDS,
                    silence_duration=1.5,
                )
                print(f"   ⏱️  (recording took {time.time() - t_record:.1f}s)")

                t_stt = time.time()
                user_text = stt.transcribe(wav_path)
                print(f"   ⏱️  (STT/Whisper took {time.time() - t_stt:.1f}s)")
                audio_io.cleanup(wav_path)

                if not user_text.strip():
                    print("(Didn't hear anything clear — back to waiting for the wake word)")
                    break

                handle_command(user_text)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    if not config.GROQ_API_KEY:
        print("⚠️  You need to set GROQ_API_KEY in your .env file first (copy .env.example)")
        sys.exit(1)

    if "--text" in sys.argv or config.TEXT_ONLY_MODE:
        run_text_mode()
    else:
        run_voice_mode()
