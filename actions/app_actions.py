"""macOS application control actions, via AppleScript and the `open` command."""
import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def open_app(app_name: str) -> str:
    """Opens an application by name, e.g.: Safari, Notes, Music, Terminal, Mail."""
    result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Couldn't find an app named {app_name}. Is it installed?"
    return f"Opened {app_name}"


def close_app(app_name: str) -> str:
    """Closes an open application."""
    output = _run_applescript(f'tell application "{app_name}" to quit')
    if "error" in output.lower() or "can't" in output.lower() or "doesn't" in output.lower():
        return f"Couldn't close {app_name}: {output}"
    return f"Closed {app_name}"


def list_open_apps() -> str:
    """Returns a list of currently open applications."""
    script = 'tell application "System Events" to get name of every process whose background only is false'
    return _run_applescript(script)
