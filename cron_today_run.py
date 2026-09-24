import json, subprocess, sys, os

env = dict(os.environ)
env["ICLOUD_EMAIL"] = "yiakhuat@icloud.com"
env["ICLOUD_PASSWORD"] = "zrmn-mkmu-sbty-bwle"

msgs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "cron", "version": "1.0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
     "params": {"name": "list_events", "arguments": {"days": 1}}},
]

inp = "".join(json.dumps(m) + "\n" for m in msgs)

p = subprocess.run(
    ["/usr/local/lib/hermes-agent/venv/bin/python", "/root/icloud_calendar_mcp.py"],
    input=inp, capture_output=True, text=True, env=env, timeout=120)

for line in p.stdout.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    if obj.get("id") == 2:
        for c in obj.get("result", {}).get("content", []):
            print(c.get("text", ""))

if p.returncode != 0:
    sys.stderr.write(p.stderr[-2000:])
