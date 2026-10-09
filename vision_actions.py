"""
Lets the assistant literally "look" at your screen using Groq's multimodal
vision model (the same model used everywhere else in this project, since it
natively accepts image + text input) — so you can ask things like "what does
this error say?" or "summarize what's on my screen" by voice, with no manual
screenshot-and-upload step.

Note: sending an image uses noticeably more tokens than a normal text
request, so this eats into the daily Groq quota faster than other commands.
"""
import base64
import os
import subprocess
import tempfile

import config
from groq import Groq

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def see_screen(question: str = "Describe what's currently on the screen.") -> str:
    """Takes a screenshot and asks the vision model a question about it."""
    tmp_path = tempfile.mktemp(suffix=".png")
    subprocess.run(["screencapture", "-x", tmp_path])  # -x = no camera shutter sound

    try:
        with open(tmp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    client = _get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                ],
            }
        ],
    )
    return response.choices[0].message.content.strip()
