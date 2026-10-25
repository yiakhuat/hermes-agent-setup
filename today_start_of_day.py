import os
from datetime import datetime, timedelta, time
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
start = datetime.combine(now.date(), time.min)
end = start + timedelta(days=1)

print("NOW:", now.isoformat())
print("WINDOW:", start.isoformat(), "->", end.isoformat())
print("CALENDARS:", [c.get_display_name() for c in calendars])
print("=" * 60)

rows = []
for cal in calendars:
    try:
        cal_name = cal.get_display_name()
        if cal_name and cal_name.startswith("Reminders"):
            continue
        events = cal.date_search(start=start, end=end, expand=True)
        print(f"[{cal_name}] raw events: {len(events)}")
        for event in events:
            try:
                v = event.vobject_instance.vevent
                summary = str(v.summary.value) if hasattr(v, "summary") else "No title"
                dtstart = v.dtstart.value if hasattr(v, "dtstart") else None
                dtend = v.dtend.value if hasattr(v, "dtend") else None
                all_day = not isinstance(dtstart, datetime)
                loc = str(v.location.value) if hasattr(v, "location") else ""
                rows.append((start if not all_day else dtstart, summary, dtstart, dtend, all_day, cal_name, loc))
            except Exception as e:
                print("  parse err:", e)
    except Exception as e:
        print("cal err:", cal.get_display_name() if hasattr(cal, "get_display_name") else "?", e)

rows.sort(key=lambda r: (r[2] if isinstance(r[2], datetime) else datetime.combine(r[2], time.min)))
print("=" * 60)
print("TOTAL TODAY:", len(rows))
for _, summary, dtstart, dtend, all_day, cal_name, loc in rows:
    print(f"{dtstart} -> {dtend} | {summary} | {cal_name} | allday={all_day} | {loc}")
