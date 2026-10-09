"""
The "brain" responsible for understanding the user's speech and deciding what to do.
Uses the Groq API (OpenAI-compatible) with tool use: we give it a list of all
available actions, and it automatically decides which action(s) to run.
"""
import json
from groq import Groq, APIError

import config
from actions import (
    app_actions, system_actions, web_actions, message_actions, shortcuts_actions,
    email_actions, notes_actions, document_actions, meeting_actions,
)
import briefing_actions
import notify_actions
import journal_actions
import vision_actions
import clipboard_actions

client = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = f"""You are {config.ASSISTANT_NAME}, a smart personal voice assistant running on a Mac.
Your job is to understand the user's requests (they may speak in English, Arabic, or Tunisian dialect)
and carry them out using the tools available to you. If a request requires taking an action, use the
appropriate tool directly without asking for extra confirmation, unless the action is sensitive
(such as sending an email/message or deleting something) — for sensitive actions, first read back
the exact details (recipient, subject/content) and ask the user to confirm before calling the tool.
Always reply in a short, natural sentence suitable for being spoken out loud.
IMPORTANT: Always reply in English, no matter what language the user spoke in."""

# Tool (action) definitions in OpenAI/Groq function-calling format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Opens an application on the computer by name, e.g. Safari, Notes, or Music",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string", "description": "The application's name in English"}},
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Closes an open application",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string"}},
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Sets the computer's system volume from 0 to 100",
            "parameters": {
                "type": "object",
                "properties": {"level": {"type": "integer", "description": "0-100"}},
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mute",
            "description": "Mutes or unmutes the system volume",
            "parameters": {
                "type": "object",
                "properties": {"state": {"type": "boolean", "description": "true to mute"}},
                "required": ["state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Locks/turns off the computer screen",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sleep_computer",
            "description": "Puts the computer to sleep",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Returns the current battery charge status",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Takes a screenshot",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_or_folder",
            "description": "Opens a file or folder given its full path",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Opens a website in the browser",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches for a topic on Google and opens the results",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_imessage",
            "description": "Sends an iMessage to a contact",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact": {"type": "string", "description": "Contact name or phone number"},
                    "message": {"type": "string"},
                },
                "required": ["contact", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Creates a new reminder that syncs automatically to iPhone",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Adds an event to the calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date_str": {"type": "string", "description": "e.g.: 'August 10, 2026 3:00 PM'"},
                },
                "required": ["title", "date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shortcut",
            "description": "Runs an existing Shortcut (for controlling the iPhone or smart devices like lights)",
            "parameters": {
                "type": "object",
                "properties": {"shortcut_name": {"type": "string"}},
                "required": ["shortcut_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_emails",
            "description": "Reads and summarizes the most recent unread emails in the inbox (sender and subject)",
            "parameters": {
                "type": "object",
                "properties": {"count": {"type": "integer", "description": "How many unread emails to summarize, default 5"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_count",
            "description": "Returns just the number of unread emails, without details",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Reads today's calendar and summarizes all scheduled events/meetings",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Sends an email via Mail.app. This is a sensitive action — always confirm the recipient, subject, and body with the user before calling this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient's email address"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "Creates a quick note in the Notes app",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string", "description": "The note's body text, optional"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Reads and extracts the text of a document (PDF, Word, RTF, or plain text file) given its full file path, so it can be summarized or searched",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Full path to the file"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Searches for files on the computer by name or content using Spotlight",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "location": {"type": "string", "description": "Folder to search in, defaults to the home folder"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_and_summarize_meeting",
            "description": "Records the room's audio for a set duration and returns a bullet-point summary with key decisions and action items. Use when the user asks to record/summarize a meeting or discussion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_seconds": {"type": "integer", "description": "How long to record, in seconds (default 60)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_morning_briefing",
            "description": "Gives a combined summary: today's schedule, unread email count, and battery status",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_phone",
            "description": "Sends a push notification to the user's phone",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "title": {"type": "string", "description": "Optional notification title"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_journal_entry",
            "description": "Saves a dictated journal/diary entry with a timestamp",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_journal_entries",
            "description": "Retrieves journal entries from the last N days, so they can be summarized or recalled",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "How many days back to look, default 7"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "see_screen",
            "description": "Takes a screenshot and visually analyzes it to answer a question about what's on screen — use for things like reading an error message, describing an image, or summarizing visible content that the user is looking at",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "What to look for or ask about the screen"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_clipboard",
            "description": "Reads and returns whatever text is currently copied to the clipboard",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_clipboard",
            "description": "Copies the given text to the clipboard",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_clipboard",
            "description": "Reads whatever is on the clipboard and explains, translates, or summarizes it depending on the question — use when the user says things like 'explain what I copied' or 'translate my clipboard'",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string", "description": "What to do with the clipboard content"}},
            },
        },
    },
]

# Maps a tool name to the actual function that carries it out
DISPATCH = {
    "open_app": lambda **kw: app_actions.open_app(kw["app_name"]),
    "close_app": lambda **kw: app_actions.close_app(kw["app_name"]),
    "set_volume": lambda **kw: system_actions.set_volume(kw["level"]),
    "mute": lambda **kw: system_actions.mute(kw["state"]),
    "lock_screen": lambda **kw: system_actions.lock_screen(),
    "sleep_computer": lambda **kw: system_actions.sleep_computer(),
    "get_battery_status": lambda **kw: system_actions.get_battery_status(),
    "take_screenshot": lambda **kw: system_actions.take_screenshot(),
    "open_file_or_folder": lambda **kw: system_actions.open_file_or_folder(kw["path"]),
    "open_url": lambda **kw: web_actions.open_url(kw["url"]),
    "web_search": lambda **kw: web_actions.web_search(kw["query"]),
    "send_imessage": lambda **kw: message_actions.send_imessage(kw["contact"], kw["message"]),
    "create_reminder": lambda **kw: message_actions.create_reminder(kw["text"]),
    "create_calendar_event": lambda **kw: message_actions.create_calendar_event(kw["title"], kw["date_str"]),
    "run_shortcut": lambda **kw: shortcuts_actions.run_shortcut(kw["shortcut_name"]),
    "get_unread_emails": lambda **kw: email_actions.get_unread_emails(kw.get("count", 5)),
    "get_unread_count": lambda **kw: email_actions.get_unread_count(),
    "get_today_schedule": lambda **kw: message_actions.get_today_schedule(),
    "send_email": lambda **kw: email_actions.send_email(kw["to"], kw["subject"], kw["body"]),
    "create_note": lambda **kw: notes_actions.create_note(kw["title"], kw.get("content", "")),
    "read_document": lambda **kw: document_actions.read_document(kw["path"]),
    "search_files": lambda **kw: system_actions.search_files(kw["query"], kw.get("location", "~")),
    "record_and_summarize_meeting": lambda **kw: meeting_actions.record_and_summarize_meeting(kw.get("duration_seconds", 60)),
    "get_morning_briefing": lambda **kw: briefing_actions.get_morning_briefing(),
    "notify_phone": lambda **kw: notify_actions.notify_phone(kw["message"], kw.get("title")),
    "add_journal_entry": lambda **kw: journal_actions.add_journal_entry(kw["text"]),
    "get_journal_entries": lambda **kw: journal_actions.get_journal_entries(kw.get("days", 7)),
    "see_screen": lambda **kw: vision_actions.see_screen(kw.get("question", "Describe what's currently on the screen.")),
    "read_clipboard": lambda **kw: clipboard_actions.read_clipboard(),
    "write_clipboard": lambda **kw: clipboard_actions.write_clipboard(kw["text"]),
    "explain_clipboard": lambda **kw: clipboard_actions.explain_clipboard(kw.get("question", "Explain this clearly and concisely.")),
}


def execute_tool(name: str, tool_input: dict) -> str:
    """Actually performs an action on the system and returns a text result."""
    print(f"⚙️  Executing: {name}({tool_input})")
    try:
        fn = DISPATCH.get(name)
        if not fn:
            return f"Unknown tool: {name}"
        return fn(**tool_input)
    except Exception as e:
        return f"An error occurred while executing {name}: {e}"


def process_command(user_text: str, history: list = None) -> tuple[str, list]:
    """
    Sends the user's command to Groq, sequentially executes any tools it
    requests (loop), and returns the final reply along with the updated
    history (to preserve conversation context).
    """
    messages = (history or [])
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    messages = messages + [{"role": "user", "content": user_text}]

    while True:
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                max_tokens=1024,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except APIError as e:
            print(f"⚠️  Groq API error: {e}")
            # Return a friendly message instead of letting the app crash
            return "Sorry, something went wrong on my end and I couldn't process that. Please try again.", (history or [])

        choice = response.choices[0]
        msg = choice.message

        # Add the assistant's reply to the history (in a re-sendable format)
        assistant_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        messages.append(assistant_msg)

        if not msg.tool_calls:
            return (msg.content or "").strip(), messages

        # Execute every requested tool_call, then feed the results back to the model
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = execute_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })
