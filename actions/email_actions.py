"""
Email actions via Apple Mail (Mail.app), using AppleScript.
Requires Mail.app to be set up with at least one account, and Automation
permission granted to Terminal/the app when first prompted.
"""
import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def get_unread_emails(count: int = 5) -> str:
    """Returns a short summary of the most recent unread emails in the inbox."""
    count = max(1, min(count, 15))
    script = f'''
    tell application "Mail"
        set theMessages to messages of inbox whose read status is false
        set outputList to {{}}
        set n to count of theMessages
        if n > {count} then set n to {count}
        repeat with i from 1 to n
            set theMessage to item i of theMessages
            set theSender to sender of theMessage
            set theSubject to subject of theMessage
            set end of outputList to (theSender & " - " & theSubject)
        end repeat
        set AppleScript's text item delimiters to "; "
        set outputText to outputList as text
        set AppleScript's text item delimiters to ""
        return outputText
    end tell
    '''
    output = _run_applescript(script)
    if not output:
        return "You have no unread emails."
    return f"Unread emails: {output}"


def get_unread_count() -> str:
    """Returns just the number of unread emails in the inbox."""
    script = 'tell application "Mail" to return count of (messages of inbox whose read status is false)'
    output = _run_applescript(script)
    return f"You have {output} unread email(s)."


def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email via Mail.app. 'to' should be an email address (or a name
    that exactly matches a contact in the Contacts app)."""
    safe_subject = subject.replace('"', '\\"')
    safe_body = body.replace('"', '\\"')
    safe_to = to.replace('"', '\\"')
    script = f'''
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}", visible:false}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:"{safe_to}"}}
        end tell
        send newMessage
    end tell
    '''
    output = _run_applescript(script)
    print(f"   (debug: send_email AppleScript output = {output!r})")
    if "error" in output.lower():
        return f"Couldn't send the email: {output}"
    return f"Email sent to {to} with subject '{subject}'."
