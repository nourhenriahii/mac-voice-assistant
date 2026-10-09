"""Combines calendar and email info into a short morning briefing."""
from actions import message_actions, email_actions, system_actions


def get_morning_briefing() -> str:
    """Returns a short combined summary: today's schedule, unread email count,
    and battery status — meant to be read aloud as a morning briefing."""
    schedule = message_actions.get_today_schedule()
    unread = email_actions.get_unread_count()
    battery = system_actions.get_battery_status()

    return f"{schedule} {unread} Battery: {battery}"
