"""Note-taking actions via Notes.app (Apple Notes), using AppleScript."""
import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def create_note(title: str, content: str = "") -> str:
    """Creates a new note in the Notes app. The title becomes the note's first line."""
    safe_title = title.replace('"', '\\"')
    safe_content = content.replace('"', '\\"')
    body = f"{safe_title}<br>{safe_content}" if safe_content else safe_title
    script = f'''
    tell application "Notes"
        tell account "iCloud"
            make new note at folder "Notes" with properties {{body:"{body}"}}
        end tell
    end tell
    '''
    output = _run_applescript(script)
    if "error" in output.lower():
        return f"Couldn't create the note: {output}"
    return f"Note created: {title}"
