#!/usr/bin/env python3
"""Check today's events on iCloud Calendar."""
import os, sys
from datetime import datetime, timedelta
import caldav

# Set credentials from config
os.environ["ICLOUD_EMAIL"] = "yiakhuat@icloud.com"
os.environ["ICLOUD_PASSWORD"] = "zrmn-mkmu-sbty-bwle"

client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username=os.environ["ICLOUD_EMAIL"],
    password=os.environ["ICLOUD_PASSWORD"],
    timeout=20
)

principal = client.principal()
calendars = principal.calendars()

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today + timedelta(days=1)

print(f"Today: {today.date()}")
print(f"Checking period: {today} to {tomorrow}")
print("-" * 70)

found = False
for cal in calendars:
    try:
        cal_name = cal.get_display_name()
        if cal_name == "Reminders":
            continue
        events = cal.date_search(start=today, end=tomorrow, expand=True)
        for event in events:
            try:
                v = event.vobject_instance.vevent
                summary = str(v.summary.value) if hasattr(v, 'summary') else 'No title'
                dtstart = str(v.dtstart.value) if hasattr(v, 'dtstart') else 'Unknown'
                dtend = str(v.dtend.value) if hasattr(v, 'dtend') else ''
                uid = str(v.uid.value) if hasattr(v, 'uid') else ''
                print(f"EVENT: {summary}")
                print(f"  Start: {dtstart}")
                print(f"  End:   {dtend}")
                print(f"  Cal:   {cal_name}")
                print(f"  UID:   {uid}")
                print("-" * 70)
                found = True
            except Exception as e:
                pass
    except Exception as e:
        print(f"Error with calendar: {e}")

if not found:
    print("NO_EVENTS_FOUND")

print("=" * 70)
print(f"Calendar check complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
