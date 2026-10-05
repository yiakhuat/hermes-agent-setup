import os
from datetime import datetime, timedelta
import caldav

os.environ.setdefault("ICLOUD_EMAIL", "yiakhuat@icloud.com")
os.environ.setdefault("ICLOUD_PASSWORD", "zrmn-mkmu-sbty-bwle")

client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username=os.environ["ICLOUD_EMAIL"],
    password=os.environ["ICLOUD_PASSWORD"],
    timeout=30,
)
principal = client.principal()
calendars = principal.calendars()

now = datetime.now()
day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
day_end = day_start + timedelta(days=1)

print("TODAY:", day_start.date().isoformat())
print("WINDOW:", day_start.isoformat(), "->", day_end.isoformat())
print("=" * 50)

found = 0
for cal in calendars:
    try:
        cal_name = cal.get_display_name()
        if "Reminders" in cal_name:
            continue
        events = cal.search(start=day_start, end=day_end, event=True, expand=True)
        for event in events:
            try:
                v = event.vobject_instance.vevent
                summary = str(v.summary.value) if hasattr(v, 'summary') else 'No title'
                dtstart = v.dtstart.value if hasattr(v, 'dtstart') else 'Unknown'
                dtend = v.dtend.value if hasattr(v, 'dtend') else ''
                all_day = not isinstance(dtstart, datetime)
                found += 1
                print(f"{summary} | start={dtstart} | end={dtend} | cal={cal_name} | allday={all_day}")
            except Exception as e:
                print("  parse err:", e)
    except Exception as e:
        print("cal err:", cal_name if 'cal_name' in dir() else '?', e)

print("=" * 50)
print("TOTAL EVENTS TODAY:", found)
