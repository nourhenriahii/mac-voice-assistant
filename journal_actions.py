"""
A simple voice journal: entries are dictated by the user and stored locally
(no cloud sync) as timestamped lines in journal.jsonl, in the project folder.
"""
import json
import os
from datetime import datetime, timedelta

JOURNAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "journal.jsonl")


def add_journal_entry(text: str) -> str:
    """Appends a new timestamped journal entry."""
    entry = {"timestamp": datetime.now().isoformat(), "text": text}
    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return "Journal entry saved."


def get_journal_entries(days: int = 7) -> str:
    """Returns journal entries from the last N days as text, for the LLM to
    summarize or answer questions about."""
    if not os.path.isfile(JOURNAL_PATH):
        return "You haven't written any journal entries yet."

    cutoff = datetime.now() - timedelta(days=days)
    lines = []
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    lines.append(f"[{ts.strftime('%Y-%m-%d %H:%M')}] {entry['text']}")
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    if not lines:
        return f"No journal entries found in the last {days} day(s)."
    return "\n".join(lines)
