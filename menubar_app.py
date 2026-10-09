"""
Menu bar app for the voice assistant.

Runs entirely from a small icon in the macOS menu bar — no Terminal needed
day-to-day. First launch walks you through entering your Groq API key.

Requires: pip install rumps
"""
import os
import threading
import time
from pathlib import Path

import rumps

PROJECT_DIR = Path(__file__).resolve().parent
ENV_PATH = PROJECT_DIR / ".env"


def _read_env() -> dict:
    """Reads the .env file into a dict (simple parser, no external dependency needed here)."""
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _write_env(values: dict):
    """Writes a dict back out to the .env file, preserving simple KEY=VALUE format."""
    lines = [f"{k}={v}" for k, v in values.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n")


class AssistantMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("🎙️", quit_button=None)
        self.menu = ["Start Listening", "Stop Listening", None, "Enable Phone Control", "Settings...", None, "Quit"]
        self.menu["Stop Listening"].set_callback(None)  # disabled until running
        self._running = False
        self._server_running = False
        self._stop_event = threading.Event()
        self._worker_thread = None

        # First-run: if there's no API key yet, prompt for it immediately.
        if not _read_env().get("GROQ_API_KEY"):
            rumps.Timer(self._prompt_for_setup, 0.5).start()

    def _prompt_for_setup(self, _timer):
        _timer.stop()
        self.open_settings(None)

    @rumps.clicked("Enable Phone Control")
    def enable_phone_control(self, sender):
        if self._server_running:
            rumps.alert("Phone control is already running.")
            return
        import socket
        import secrets
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "<your-mac's-local-ip>"

        current = _read_env()
        token = current.get("SERVER_AUTH_TOKEN", "")
        if not token:
            token = secrets.token_urlsafe(8)
            current["SERVER_AUTH_TOKEN"] = token
            _write_env(current)

        import config
        config.SERVER_AUTH_TOKEN = token

        from server import run_server
        threading.Thread(target=run_server, daemon=True).start()
        self._server_running = True
        sender.state = 1
        rumps.alert(
            f"Phone control is on.\n\nOpen this exact link in your phone's "
            f"browser (same Wi-Fi network):\n\nhttp://{local_ip}:5005/?token={token}\n\n"
            f"Anyone without this exact link can't use it."
        )

    @rumps.clicked("Settings...")
    def open_settings(self, _sender):
        current = _read_env()
        response = rumps.Window(
            title="Assistant Settings",
            message="Paste your Groq API key (get one free at console.groq.com/keys):",
            default_text=current.get("GROQ_API_KEY", ""),
            ok="Save",
            cancel="Cancel",
            dimensions=(320, 24),
        ).run()
        if response.clicked and response.text.strip():
            current["GROQ_API_KEY"] = response.text.strip()
            current.setdefault("GROQ_MODEL", "qwen/qwen3.6-27b")
            current.setdefault("ASSISTANT_NAME", "Assistant")
            current.setdefault("TTS_VOICE", "Samantha")
            current.setdefault("WHISPER_MODEL_SIZE", "base")
            current.setdefault("TEXT_ONLY_MODE", "false")
            _write_env(current)
            rumps.alert("Saved! Click 'Start Listening' to begin.")

    @rumps.clicked("Start Listening")
    def start_listening(self, _sender):
        if self._running:
            return
        if not _read_env().get("GROQ_API_KEY"):
            rumps.alert("Please set your Groq API key first (Settings...).")
            return

        self._running = True
        self._stop_event.clear()
        self.title = "🟢"
        self.menu["Start Listening"].set_callback(None)
        self.menu["Stop Listening"].set_callback(self.stop_listening)

        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    @rumps.clicked("Stop Listening")
    def stop_listening(self, _sender):
        self._running = False
        self._stop_event.set()
        self.title = "🎙️"
        self.menu["Start Listening"].set_callback(self.start_listening)
        self.menu["Stop Listening"].set_callback(None)

    @rumps.clicked("Quit")
    def quit_app(self, _sender):
        self._stop_event.set()
        rumps.quit_application()

    def _run_loop(self):
        """Runs the wake-word + command loop in a background thread, updating
        the menu bar icon to reflect what's currently happening."""
        # Imported here (not at module level) so the app can start up and show
        # the settings prompt even before dependencies/config are fully ready.
        import config
        import audio_io
        import stt
        import tts
        from brain import process_command

        history = []

        try:
            from wake_word import listen_for_wake_word
            has_wake_word = True
        except ImportError:
            has_wake_word = False

        while not self._stop_event.is_set():
            try:
                if has_wake_word:
                    self.title = "🎙️"
                    listen_for_wake_word()
                else:
                    time.sleep(0.5)  # no-wake-word fallback isn't practical for a menu bar app

                if self._stop_event.is_set():
                    break

                # Inner loop: after the wake word triggers once, keep listening
                # for follow-up commands without needing to say the wake word
                # again, until the user goes quiet for a bit.
                while not self._stop_event.is_set():
                    self.title = "🔴"  # recording
                    t0 = time.time()
                    wav_path = audio_io.record_until_silence(
                        max_seconds=config.COMMAND_RECORD_SECONDS,
                        silence_duration=2.0,
                    )
                    print(f"   ⏱️  (recording: {time.time() - t0:.1f}s)")

                    self.title = "💭"  # thinking
                    t1 = time.time()
                    user_text = stt.transcribe(wav_path)
                    audio_io.cleanup(wav_path)
                    print(f"   ⏱️  (STT: {time.time() - t1:.1f}s) transcribed = {user_text!r}")

                    if not user_text.strip():
                        # Nothing was said — go back to waiting for the wake word.
                        break

                    print(f"🗣️  You: {user_text}")
                    t2 = time.time()
                    reply, history = process_command(user_text, history)
                    print(f"   ⏱️  (brain/Groq: {time.time() - t2:.1f}s)")
                    history = history[-8:]

                    self.title = "🔊"  # speaking
                    t3 = time.time()
                    tts.speak(reply)
                    print(f"   ⏱️  (TTS: {time.time() - t3:.1f}s)")

            except Exception as e:
                print(f"⚠️  Error in assistant loop: {e}")
                time.sleep(1)

        self.title = "🎙️"


if __name__ == "__main__":
    AssistantMenuBarApp().run()
