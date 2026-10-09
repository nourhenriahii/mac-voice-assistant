"""
Runs Apple Shortcuts by name.
This is the easiest bridge for controlling the iPhone and smart-home devices
(lights, plugs...): any Shortcut you create syncs through iCloud and can also
run actions on the iPhone, and any HomeKit device can be controlled from a
Shortcut with no extra code.
"""
import subprocess


def run_shortcut(shortcut_name: str, input_text: str = None) -> str:
    """
    Runs an existing Shortcut from the Shortcuts app, by name.
    Create the Shortcuts first in the Shortcuts app on your Mac or iPhone
    (e.g. "Living room lights on", "Send my location", "Do Not Disturb"...)
    """
    cmd = ["shortcuts", "run", shortcut_name]
    if input_text:
        cmd += ["--input-path", "-"]
        result = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() or f"Ran the shortcut:
