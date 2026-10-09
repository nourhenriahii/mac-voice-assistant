# 🎙️ Personal Voice Assistant for macOS

A voice assistant that runs on your Mac, in the spirit of Alexa or Siri — but yours to
customize. It listens for a wake word, understands what you ask (in English, Arabic, or
dialect), and **actually does it**: opens apps, sets the volume, sends messages and emails,
adds reminders and calendar events, reads your screen, summarizes documents, controls your
iPhone and smart-home devices through Shortcuts, and more.

- **Speech-to-text:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper), running locally on your Mac
- **Wake word:** [openWakeWord](https://github.com/dscripka/openWakeWord) ("Hey Jarvis"), running locally
- **Brain:** [Groq](https://console.groq.com) LLM with tool-calling (fast, with a free tier)
- **Actions:** AppleScript, shell commands and Apple Shortcuts
- **Voice:** the built-in macOS `say` command (free, offline)
- **Interface:** a menu bar app, a terminal mode, and a small web page for your phone

## How it works

```
🎙️ Microphone ──► Wake word ──► Record command ──► Whisper (speech → text)
                                                         │
                                                         ▼
                                       Groq LLM decides which tool(s) to call
                                                         │
                                                         ▼
                              Real action on your Mac (AppleScript / shell / Shortcuts)
                                                         │
                                                         ▼
                                              Spoken reply (macOS `say`)
```

## Features

| Category | What you can say | Tools |
|---|---|---|
| **Apps & system** | "Open Safari", "Close Music", "Set volume to 30", "Mute", "Lock the screen", "Put the Mac to sleep", "How's the battery?" | `open_app`, `close_app`, `set_volume`, `mute`, `lock_screen`, `sleep_computer`, `get_battery_status` |
| **Files & documents** | "Find my tax PDF", "Open ~/Downloads", "Summarize /path/to/report.pdf" | `search_files`, `open_file_or_folder`, `read_document` (PDF, DOCX, RTF, TXT…) |
| **Web** | "Open github.com", "Search for pasta recipes" | `open_url`, `web_search` |
| **Messages & email** | "Text Sarah I'm running late", "Any unread emails?", "Email John about the meeting" | `send_imessage`, `get_unread_emails`, `get_unread_count`, `send_email` |
| **Planning** | "Remind me to call the bank", "Add dinner on August 10 at 8 PM", "What's on my schedule today?", "Give me my morning briefing" | `create_reminder`, `create_calendar_event`, `get_today_schedule`, `get_morning_briefing` |
| **Notes & journal** | "Take a note: …", "Add a journal entry: …", "Summarize my journal this week" | `create_note`, `add_journal_entry`, `get_journal_entries` |
| **Screen & clipboard** | "What does this error say?", "Explain what I copied", "Translate my clipboard" | `see_screen`, `read_clipboard`, `write_clipboard`, `explain_clipboard` |
| **Meetings** | "Record and summarize this meeting for 5 minutes" | `record_and_summarize_meeting` |
| **Phone & smart home** | "Run my Good Night shortcut", "Send a notification to my phone" | `run_shortcut`, `notify_phone` |

For sensitive actions (sending an email or message), the assistant is instructed to read the details back and ask you to confirm before it runs.

## Requirements

- A Mac (Apple Silicon or Intel) with macOS
- Python 3.10 or newer
- [PortAudio](http://www.portaudio.com/) for microphone access (`brew install portaudio`)
- A free [Groq API key](https://console.groq.com/keys)

## Installation

### Option A — Double-click (easiest)

1. Download or clone this repository.
2. Double-click **`Launch Assistant.command`**. The first run creates a virtual environment and installs everything.
   (If macOS blocks it: right-click → **Open**. If it says it isn't executable, run `chmod +x "Launch Assistant.command"` once.)
3. A 🎙️ icon appears in the menu bar. On first launch you'll be asked for your Groq API key.
4. Click the icon → **Start Listening**, then say **"Hey Jarvis"**.

### Option B — Terminal

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

brew install portaudio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then open .env and add your GROQ_API_KEY
```

Run it:

```bash
python main.py --text       # type commands instead of speaking (great for testing)
python main.py              # full voice mode (wake word + microphone)
python menubar_app.py       # menu bar app
```

## Configuration

Settings live in a `.env` file (copy `.env.example`). Only `GROQ_API_KEY` is required.

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Your Groq API key (**required**) |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model that understands commands and calls tools (must support tool-calling) |
| `GROQ_VISION_MODEL` | `qwen/qwen3.8-27b` | Model used by "what's on my screen?" (must accept images) |
| `ASSISTANT_NAME` | `Jarvis` | Name shown and spoken |
| `TTS_VOICE` | `Samantha` | macOS voice (list them with `say -v '?'`) |
| `WHISPER_MODEL_SIZE` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3` — bigger is more accurate but slower |
| `WHISPER_LANGUAGE` | `en` | Speech language (`en`, `ar`, …). Leave empty to auto-detect |
| `TEXT_ONLY_MODE` | `false` | `true` = type instead of speak |
| `CALENDAR_NAME` | `Home` | Calendar new events are added to (must exist in Calendar.app) |
| `NTFY_TOPIC` | — | Topic for phone notifications via [ntfy.sh](https://ntfy.sh) |
| `CUSTOM_WAKE_WORD_MODEL_PATH` | — | Path to your own `.onnx` wake word model (default: bundled "Hey Jarvis") |
| `SERVER_AUTH_TOKEN` | — | Secret for phone control; generated automatically by the menu bar app |

> The assistant always **replies in English**, whatever language you speak. To change that, edit `SYSTEM_PROMPT` in `brain.py` (and pick a matching `TTS_VOICE`).

## macOS permissions

The first time you use a feature, macOS asks for permission. Grant these to **Terminal** (or the app you launch it from) in
**System Settings → Privacy & Security**:

| Permission | Needed for |
|---|---|
| **Microphone** | Listening to you |
| **Automation** | Controlling Mail, Messages, Calendar, Reminders, Notes and System Events |
| **Screen Recording** | "What's on my screen?" |
| **Contacts** | Looking up people by name when messaging |

## Phone control

Control the assistant from your iPhone over your home Wi-Fi:

1. Menu bar icon → **Enable Phone Control**.
2. Open the link it shows in your phone's browser (it contains your secret token), or build an iPhone Shortcut that calls the API:

```bash
# Check the server is reachable
curl http://<mac-ip>:5005/ping

# Send a command (set "speak": false to stop the Mac from also saying the answer out loud)
curl -X POST http://<mac-ip>:5005/ask \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <your-token>" \
  -d '{"text": "open Safari", "speak": false}'
```

The server listens on your local network only. Anyone on that network who has the token can control your Mac, so keep the link private.

## Notification to your phone

Install the **ntfy** app on your phone, subscribe to a hard-to-guess topic name, and put the same name in `NTFY_TOPIC`.
Then say *"Send a notification to my phone saying …"*.

## Project structure

```
.
├── main.py                 # Terminal entry point (voice or --text mode)
├── menubar_app.py          # Menu bar app (double-click launcher uses this)
├── brain.py                # LLM + tool definitions (TOOLS) + dispatch table (DISPATCH)
├── config.py               # Settings, read from .env
├── stt.py                  # Local speech-to-text (faster-whisper)
├── tts.py                  # Text-to-speech (macOS `say`)
├── audio_io.py             # Microphone recording, silence detection
├── wake_word.py            # Local wake-word detection (openWakeWord)
├── server.py               # Phone-control web server (Flask)
├── actions/                # Things the assistant can do
│   ├── app_actions.py        # open / close apps
│   ├── system_actions.py     # volume, battery, sleep, file search
│   ├── web_actions.py        # open URL, web search
│   ├── message_actions.py    # iMessage, reminders, calendar
│   ├── email_actions.py      # Mail.app
│   ├── notes_actions.py      # Apple Notes
│   ├── document_actions.py   # read PDF / Word / text files
│   ├── meeting_actions.py    # record + summarize a meeting
│   ├── shortcuts_actions.py  # run Apple Shortcuts
│   └── _applescript.py       # safe AppleScript runner + escaping
├── briefing_actions.py     # Morning briefing
├── clipboard_actions.py    # Clipboard read / write / explain
├── journal_actions.py      # Voice journal (stored locally in journal.jsonl)
├── notify_actions.py       # Phone notifications via ntfy.sh
├── vision_actions.py       # "Look" at the screen
└── Launch Assistant.command
```

## Adding your own action

1. Write a function that returns a short string describing the result, e.g. in `actions/`:

   ```python
   def tell_joke() -> str:
       return "Why do programmers prefer dark mode? Because light attracts bugs."
   ```

2. Describe it to the model by adding an entry to `TOOLS` in `brain.py`:

   ```python
   {
       "type": "function",
       "function": {
           "name": "tell_joke",
           "description": "Tells the user a joke",
           "parameters": {"type": "object", "properties": {}},
       },
   },
   ```

3. Map its name to the function in `DISPATCH` in `brain.py`:

   ```python
   "tell_joke": lambda **kw: my_module.tell_joke(),
   ```

Say "tell me a joke" and the model will call it.

## Privacy and security

- **Audio stays on your Mac.** Speech recognition and wake-word detection run locally.
- **Text goes to Groq.** Your transcribed commands and the results of tools (calendar entries, email subjects, document text, clipboard text, journal entries you ask about) are sent to Groq to produce the reply. When you use "what's on my screen?", a screenshot is sent too. Don't use those features with content you wouldn't want to share with that provider.
- **The assistant runs real commands on your computer.** Review what each action can do before extending it, and add confirmations for anything destructive.
- **Never commit `.env`** — it holds your API key and phone-control token. The included `.gitignore` already excludes it, along with `journal.jsonl` (your personal journal).

## Troubleshooting

| Problem | Try |
|---|---|
| *"Sorry, something went wrong on my end"* | Look at the terminal output for the real error (bad API key, no internet, model name changed). |
| *"I've hit my usage limit"* | You reached Groq's rate limit; wait a bit, or use a smaller model. Screen reading uses the most tokens. |
| Nothing happens when I speak | Check the Microphone permission, and that `brew install portaudio` succeeded. |
| Wake word never triggers | Watch the live score in the terminal; lower `threshold` in `wake_word.py`, or speak closer to the mic. |
| Transcription is poor | Use a bigger `WHISPER_MODEL_SIZE`, and set `WHISPER_LANGUAGE` to the language you speak. |
| "What's on my screen?" fails | Grant **Screen Recording** permission, and make sure `GROQ_VISION_MODEL` accepts images. |
| Calendar event isn't created | Make sure a calendar named like `CALENDAR_NAME` exists in Calendar.app. |

## License

No license has been chosen yet. Add a `LICENSE` file (for example MIT) if you want others to be able to reuse the code.
