import os
from datetime import datetime, timedelta
import caldav

os.environ.setdefault("ICLOUD_EMAIL", "yiakhuat@icloud.com")
os.environ.setdefault("ICLOUD_PASSWORD", "zrmn-mkmu-sbty-bwle")

def get_client():
    return caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=os.environ["ICLOUD_EMAIL"],
        password=os.environ["ICLOUD_PASSWORD"],
        timeout=30,
    )

def main():
    now = datetime.now()
    # Cover the whole of today
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    client = get_client()
    principal = client.principal()
    calendars = principal.calendars()
    print(f"NOW={now.isoformat()}")
    print(f"WINDOW={start.isoformat()} -> {end.isoformat()}")
    print(f"CALENDARS={[c.get_display_name() for c in calendars]}")
    print("-" * 50)
    found = []
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
                    found.append((cal_name, summary, dtstart, dtend))
                    print(f"EVENT | {cal_name} | {summary} | {dtstart} -> {dtend}")
                except Exception as e:
                    print(f"  parse error: {e}")
        except Exception as e:
            print(f"  cal error ({cal_name}): {e}")
    if not found:
        print("NO_EVENTS_TODAY")

if __name__ == "__main__":
    main()
