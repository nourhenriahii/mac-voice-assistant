"""
Small local HTTP server that lets you control the assistant remotely — e.g.
from an iPhone Shortcut over your home Wi-Fi. This is NOT exposed to the
internet; it only works on your local network.

Requires: pip install flask
"""
from flask import Flask, request, jsonify, Response

import config
from brain import process_command
import tts

app = Flask(__name__)
_history = []


def _check_auth() -> bool:
    token = request.args.get("token") or request.headers.get("X-Auth-Token")
    return bool(token) and bool(config.SERVER_AUTH_TOKEN) and token == config.SERVER_AUTH_TOKEN


_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ask Jarvis</title>
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 480px; margin: 40px auto; padding: 0 16px; }
        input[type=text] { width: 100%; font-size: 18px; padding: 12px; box-sizing: border-box; }
        button { width: 100%; font-size: 18px; padding: 14px; margin-top: 10px; }
        #reply { margin-top: 20px; padding: 14px; background: #f0f0f0; border-radius: 8px; min-height: 20px; }
        #log { margin-top: 20px; }
        .entry { padding: 10px; border-bottom: 1px solid #ddd; }
        .entry .q { color: #666; font-size: 14px; }
        .entry .a { margin-top: 4px; }
    </style>
</head>
<body>
    <h2>🎙️ Ask Jarvis</h2>
    <p>Type or use your keyboard's mic button to dictate a command.</p>
    <form id="askForm">
        <input type="text" id="textInput" placeholder="e.g. open Safari" autofocus>
        <button type="submit">Send</button>
    </form>
    <div id="reply"></div>
    <div id="log"></div>
    <script>
        const AUTH_TOKEN = "__TOKEN__";
        document.getElementById('askForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('textInput').value.trim();
            if (!text) return;
            const replyBox = document.getElementById('reply');
            replyBox.textContent = 'Thinking...';
            try {
                const res = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-Auth-Token': AUTH_TOKEN},
                    body: JSON.stringify({text: text})
                });
                const rawText = await res.text();
                let data;
                try {
                    data = JSON.parse(rawText);
                } catch (parseErr) {
                    replyBox.textContent = 'Unexpected response: ' + rawText;
                    return;
                }
                replyBox.textContent = data.reply || data.error || 'No response';
                const entry = document.createElement('div');
                entry.className = 'entry';
                entry.innerHTML = '<div class="q">You: ' + text + '</div><div class="a">' + (data.reply || data.error || 'No response') + '</div>';
                document.getElementById('log').prepend(entry);
            } catch (networkErr) {
                replyBox.textContent = 'Network error: ' + networkErr.message;
            }
            document.getElementById('textInput').value = '';
        });
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    if not _check_auth():
        return Response("<h3>Unauthorized — open this page using the exact link shown in "
                         "'Enable Phone Control' on the Mac.</h3>", mimetype="text/html"), 401
    token = request.args.get("token", "")
    return Response(_PAGE_HTML.replace("__TOKEN__", token), mimetype="text/html")


@app.route("/ask", methods=["POST"])
def ask():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    global _history
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No 'text' provided"}), 400

    reply, _history = process_command(text, _history)
    _history = _history[-8:]

    if data.get("speak", True):
        tts.speak(reply)

    return jsonify({"reply": reply})


@app.route("/ping", methods=["GET"])
def ping():
    """Lets a Shortcut check the server is reachable before asking anything."""
    return jsonify({"status": "ok"})


def run_server(host: str = "0.0.0.0", port: int = 5005):
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_server()
