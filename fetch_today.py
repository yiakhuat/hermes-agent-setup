import os
from datetime import datetime, timedelta
import caldav

EMAIL = "yiakhuat@icloud.com"
PASSWORD = "zrmn-mkmu-sbty-bwle"

client = caldav.DAVClient(
    url="https://caldav.icloud.com",
    username=EMAIL,
    password=PASSWORD,
    timeout=20
)
principal = client.principal()
calendars = principal.calendars()

now = datetime.now()
start = now.replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

print(f"Today: {now.strftime('%Y-%m-%d %A')}")
print("=" * 60)

found = False
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
                print(f"CAL: {cal_name}")
                print(f"  TITLE: {summary}")
                print(f"  START: {dtstart}")
                print(f"  END:   {dtend}")
                print("-" * 40)
                found = True
            except Exception:
                pass
    except Exception as e:
        print(f"Error on calendar: {e}")

if not found:
    print("No events found for today.")
