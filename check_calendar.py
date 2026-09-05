import os, sys
from datetime import datetime, timedelta
import caldav

EMAIL = os.environ["ICLOUD_EMAIL"]
PASSWORD = os.environ["ICLOUD_PASSWORD"]

client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username=EMAIL,
    password=PASSWORD,
    timeout=20,
)
principal = client.principal()
calendars = principal.calendars()

now = datetime.now()
start = now.replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

rows = []
for cal in calendars:
    try:
        cal_name = cal.get_display_name()
        if cal_name == "Reminders":
            continue
        events = cal.date_search(start=start, end=end, expand=True)
        for event in events:
            try:
                v = event.vobject_instance.vevent
                summary = str(v.summary.value) if hasattr(v, 'summary') else 'No title'
                dtstart = str(v.dtstart.value) if hasattr(v, 'dtstart') else 'Unknown'
                dtend = str(v.dtend.value) if hasattr(v, 'dtend') else ''
                rows.append(f"TITLE: {summary} | START: {dtstart} | END: {dtend} | CAL: {cal_name}")
            except Exception:
                pass
    except Exception as e:
        print(f"cal error {cal}: {e}", file=sys.stderr)

if not rows:
    print("NO_EVENTS")
else:
    for r in sorted(rows):
        print(r)
