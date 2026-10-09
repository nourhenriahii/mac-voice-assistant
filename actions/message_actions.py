"""
Sends iMessages, creates reminders, and manages calendar events via AppleScript.
Requires Messages.app, Reminders.app, and Calendar.app to be signed in to your
Apple ID.
"""
import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def send_imessage(contact: str, message: str) -> str:
    """Sends an iMessage to a contact (by the name saved in Contacts, or a phone number)."""
    safe_message = message.replace('"', '\\"')
    script = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{contact}" of targetService
        send "{safe_message}" to targetBuddy
    end tell
    '''
    _run_applescript(script)
    return f"Message sent to {contact}"


def create_reminder(text: str, list_name: str = "Reminders") -> str:
    """Creates a new reminder in the Reminders app (syncs to iPhone automatically)."""
    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            make new reminder with properties {{name:"{text}"}}
        end tell
    end tell
    '''
    _run_applescript(script)
    return f"Reminder added: {text}"


def create_calendar_event(title: str, date_str: str) -> str:
    """Creates a calendar event. date_str format: 'August 10, 2026 3:00 PM'"""
    script = f'''
    tell application "Calendar"
        tell calendar "Home"
            make new event with properties {{summary:"{title}", start date:date "{date_str}"}}
        end tell
    end tell
    '''
    _run_applescript(script)
    return f"Event added: {title}"


def get_today_schedule() -> str:
    """Returns a summary of today's calendar events across all calendars."""
    script = '''
    tell application "Calendar"
        set todayStart to current date
        set hours of todayStart to 0
        set minutes of todayStart to 0
        set seconds of todayStart to 0
        set todayEnd to todayStart + 1 * days
        set eventList to {}
        repeat with cal in calendars
            try
                set theEvents to (every event of cal whose start date ≥ todayStart and start date < todayEnd)
                repeat with evt in theEvents
                    set end of eventList to (summary of evt & " at " & (time string of (start date of evt)))
                end repeat
            end try
        end repeat
        set AppleScript's text item delimiters to "; "
        set outputText to eventList as text
        set AppleScript's text item delimiters to ""
        return outputText
    end tell
    '''
    output = _run_applescript(script)
    if not output:
        return "You have no events scheduled today."
    return f"Today's schedule: {output}"
