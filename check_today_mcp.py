import os, sys
os.environ.setdefault("ICLOUD_EMAIL", "yiakhuat@icloud.com")
os.environ.setdefault("ICLOUD_PASSWORD", "zrmn-mkmu-sbty-bwle")
sys.path.insert(0, "/root")
import icloud_calendar_mcp as m

print("NOW:", __import__("datetime").datetime.now().isoformat())
print("--- list_events(days=1) ---")
print(m.fetch_events("", 1))
