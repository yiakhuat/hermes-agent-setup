import os, sys
from datetime import datetime, timedelta, timezone
import caldav

EMAIL = os.environ["ICLOUD_EMAIL"]
PASSWORD = os.environ["ICLOUD_PASSWORD"]

# Determine "today" boundaries. Search range is broad; we'll filter events by
# comparing against the local calendar date the event belongs to.
client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username=EMAIL,
    password=PASSWORD,
    timeout=20,
)
principal = client.principal()
calendars = principal.calendars()

print(f"Server now (UTC): {datetime.now(timezone.utc).isoformat()}", file=sys.stderr)

now_utc = datetime.now(timezone.utc)
# search broad window around now
start = now_utc - timedelta(hours=48)
end = now_utc + timedelta(hours=48)

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
                ds = getattr(v.dtstart.value, 'isoformat', lambda: str(v.dtstart.value))()
                de = getattr(v.dtend.value, 'isoformat', lambda: '' )() if hasattr(v, 'dtend') else ''
                rows.append(f"TITLE: {summary} | START: {ds} | END: {de} | CAL: {cal_name}")
            except Exception:
                pass
    except Exception as e:
        print(f"cal error: {e}", file=sys.stderr)

for r in sorted(rows):
    print(r)
print(f"TOTAL: {len(rows)}", file=sys.stderr)
