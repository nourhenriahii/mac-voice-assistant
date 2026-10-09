"""macOS system control actions."""
import os
import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def set_volume(level: int) -> str:
    """Sets the system volume from 0 to 100."""
    level = max(0, min(100, level))
    _run_applescript(f"set volume output volume {level}")
    return f"Volume set to {level}%"


def mute(state: bool = True) -> str:
    _run_applescript(f"set volume output muted {'true' if state else 'false'}")
    return "Muted" if state else "Unmuted"


def lock_screen() -> str:
    subprocess.run(["pmset", "displaysleepnow"])
    return "Screen locked/turned off"


def sleep_computer() -> str:
    subprocess.run(["osascript", "-e", 'tell application "System Events" to sleep'])
    return "The computer is going to sleep"


def get_battery_status() -> str:
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    return result.stdout.strip()


def take_screenshot(save_path: str = "/tmp/screenshot.png") -> str:
    subprocess.run(["screencapture", save_path])
    return f"Screenshot saved to {save_path}"


def open_file_or_folder(path: str) -> str:
    subprocess.run(["open", path])
    return f"Opened {path}"


def search_files(query: str, location: str = "~") -> str:
    """Searches for files by name or content using Spotlight (mdfind).
    Returns up to 10 matching file paths."""
    location = os.path.expanduser(location)
    result = subprocess.run(["mdfind", "-onlyin", location, query], capture_output=True, text=True)
    paths = [p for p in result.stdout.strip().split("\n") if p][:10]
    if not paths:
        return f"No files found matching '{query}'."
    return "Found files: " + "; ".join(paths)
