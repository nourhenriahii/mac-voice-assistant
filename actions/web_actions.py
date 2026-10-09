"""Web-related actions: open a website, search."""
import webbrowser
import urllib.parse


def open_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def web_search(query: str) -> str:
    q = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={q}")
    return f"Searched for: {query}"
