import os
from datetime import datetime, timedelta
import caldav
import yaml
from pathlib import Path

config = yaml.safe_load(Path('/root/.hermes/config.yaml').read_text())
env = config['mcp_servers']['icloud-calendar']['env']

client = caldav.DAVClient(
    url='https://caldav.icloud.com',
    username=env['ICLOUD_EMAIL'],
    password=env['ICLOUD_PASSWORD'],
    timeout=20,
)
principal = client.principal()

# Today's boundaries (local time)
now = datetime.now()
start = datetime(now.year, now.month, now.day, 0, 0, 0)
end = start + timedelta(days=1)

results = []
for cal in principal.calendars():
    try:
        cal_name = cal.get_display_name()
        if cal_name == "Reminders":
            continue
        events = cal.date_search(start=start, end=end, expand=True)
        for event in events:
            try:
                v = event.vobject_instance.vevent
                summary = str(v.summary.value) if hasattr(v, 'summary') else 'No title'
                dtstart = v.dtstart.value
                dtend = v.dtend.value if hasattr(v, 'dtend') else None
                all_day = not hasattr(dtstart, 'hour') or (hasattr(dtstart, 'hour') and not hasattr(v, 'dtstart').__class__ and False)
                # detect all-day (date without time)
                is_date = not hasattr(dtstart, 'hour')
                uid = str(v.uid.value) if hasattr(v, 'uid') else ''
                results.append({
                    'summary': summary,
                    'dtstart': str(dtstart),
                    'dtend': str(dtend) if dtend else '',
                    'calendar': cal_name,
                    'uid': uid,
                    'all_day': is_date,
                })
            except Exception:
                pass
    except Exception:
        pass

# Sort by start time
results.sort(key=lambda r: r['dtstart'])

print(f"TODAY={now.strftime('%Y-%m-%d %A')}")
print(f"COUNT={len(results)}")
for r in results:
    print(f"EVENT|{r['summary']}|{r['dtstart']}|{r['dtend']}|{r['calendar']}|allday={r['all_day']}|UID={r['uid']}")
