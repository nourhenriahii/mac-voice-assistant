"""
Lets the assistant interact with the Mac clipboard by voice: read what's
copied, copy new text, or have the LLM explain/translate/summarize whatever
you last copied from anywhere (an error message, a foreign phrase, a link...).
"""
import subprocess

import config
from groq import Groq

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def read_clipboard() -> str:
    """Returns the current text content of the clipboard."""
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    text = result.stdout.strip()
    if not text:
        return "Your clipboard is empty."
    return text


def write_clipboard(text: str) -> str:
    """Copies the given text to the clipboard."""
    subprocess.run(["pbcopy"], input=text, text=True)
    return "Copied to clipboard."


def explain_clipboard(question: str = "Explain this clearly and concisely.") -> str:
    """Reads whatever is currently on the clipboard and asks the LLM to
    explain, translate, or summarize it, per the given question."""
    clipboard_text = read_clipboard()
    if clipboard_text == "Your clipboard is empty.":
        return clipboard_text

    client = _get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        max_tokens=400,
        messages=[
            {"role": "system", "content": "Answer briefly and clearly, suitable for being read aloud."},
            {"role": "user", "content": f"{question}\n\n---\n{clipboard_text}\n---"},
        ],
    )
    return response.choices[0].message.content.strip()
