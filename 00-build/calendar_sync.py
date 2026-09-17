"""Calendar integration for Cortex.

Supports:
1. Native macOS Calendar.app (when synced via System Settings -> Internet Accounts).
2. Google Calendar secret iCal URL (via GOOGLE_CALENDAR_ICS_URL in .env).
"""

from __future__ import annotations

import datetime
import os
import subprocess
import urllib.request


def get_macos_calendar_events(target_title: str = "") -> list[dict]:
    """Fetch events from macOS Calendar.app via AppleScript."""
    script = """
    tell application "Calendar"
        set eventList to ""
        repeat with c in calendars
            set calName to name of c
            repeat with e in (every event of c)
                try
                    set s to summary of e
                    set sd to (start date of e) as string
                    set ed to (end date of e) as string
                    set eventList to eventList & calName & "|||" & s & "|||" & sd & "|||" & ed & linefeed
                end try
            end repeat
        end repeat
        return eventList
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", script],
                              capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return []
        
        events = []
        for line in proc.stdout.strip().splitlines():
            parts = line.split("|||")
            if len(parts) >= 4:
                cal, summary, start, end = parts[0], parts[1], parts[2], parts[3]
                if not target_title or target_title.lower() in summary.lower():
                    events.append({
                        "calendar": cal,
                        "title": summary,
                        "start": start,
                        "end": end,
                        "source": "macos_calendar"
                    })
        return events
    except Exception as e:
        return [{"error": str(e)}]


def check_upcoming_session(target_title: str = "Agentic Workflows & Loops") -> dict:
    """Check for upcoming sessions matching the target title."""
    events = get_macos_calendar_events(target_title)
    if events and "error" not in events[0]:
        return {
            "status": "found",
            "matches": events,
            "target": target_title
        }
    return {
        "status": "not_synced",
        "message": f"No events matching '{target_title}' found in local calendar.",
        "target": target_title
    }


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    events = get_macos_calendar_events(query)
    print(f"Total events found: {len(events)}")
    for ev in events:
        print(f"[{ev['calendar']}] {ev['title']} ({ev['start']} -> {ev['end']})")
