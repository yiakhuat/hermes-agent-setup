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
start = now
end = now + timedelta(days=1)

print("NOW:", now.isoformat())
print("CALENDARS:", [c.get_display_name() for c in calendars])
print("=" * 50)

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
                dtstart = v.dtstart.value if hasattr(v, 'dtstart') else 'Unknown'
                dtend = v.dtend.value if hasattr(v, 'dtend') else ''
                all_day = not isinstance(dtstart, datetime)
                print(f"{summary} | {dtstart} -> {dtend} | {cal_name} | allday={all_day}")
            except Exception as e:
                print("  parse err:", e)
    except Exception as e:
        print("cal err:", cal.get_display_name() if hasattr(cal,'get_display_name') else '?', e)
