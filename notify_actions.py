"""
Sends push notifications to your phone via ntfy.sh — a free, no-signup
notification relay. Install the "ntfy" app on your phone and subscribe to
your chosen topic name to receive these.
"""
import ssl
import urllib.request
import config

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = None


def notify_phone(message: str, title: str = None) -> str:
    """Sends a push notification to the phone via the configured ntfy.sh topic."""
    topic = config.NTFY_TOPIC
    if not topic:
        return ("Phone notifications aren't set up yet. Set NTFY_TOPIC in your .env "
                "to a unique topic name, and subscribe to it in the ntfy app on your phone.")

    url = f"https://ntfy.sh/{topic}"
    headers = {}
    if title:
        headers["Title"] = title.encode("utf-8")

    try:
        req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
        urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT)
    except Exception as e:
        print(f"⚠️  notify_phone error: {e!r}")
        return f"Couldn't send the notification: {e}"

    return "Notification sent to your phone."
