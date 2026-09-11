import os, sys
sys.path.insert(0, "/root")
os.environ.setdefault("ICLOUD_EMAIL", "yiakhuat@icloud.com")
os.environ.setdefault("ICLOUD_PASSWORD", "zrmn-mkmu-sbty-bwle")

import icloud_calendar_mcp as m

print("TODAY:", __import__("datetime").datetime.now().isoformat())
print(m.fetch_events(None, 1))
