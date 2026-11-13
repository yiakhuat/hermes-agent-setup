import json, os, subprocess, sys, time, threading, queue

env = dict(os.environ)
env['ICLOUD_EMAIL'] = 'yiakhuat@icloud.com'
env['ICLOUD_PASSWORD'] = 'zrmn-mkmu-sbty-bwle'

p = subprocess.Popen(
    ['/root/hermes-venv/bin/python3', '/root/icloud_calendar_mcp.py'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, bufsize=1, env=env,
)

q = queue.Queue()

def reader():
    for line in p.stdout:
        line = line.strip()
        if line:
            q.put(line)

threading.Thread(target=reader, daemon=True).start()

def send(msg):
    p.stdin.write(json.dumps(msg) + '\n')
    p.stdin.flush()

def wait_for(id_, timeout=45):
    end = time.time() + timeout
    while time.time() < end:
        try:
            line = q.get(timeout=max(0.1, end - time.time()))
        except queue.Empty:
            return None
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get('id') == id_:
            return obj
    return None

send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{
    'protocolVersion':'2024-11-05','capabilities':{},
    'clientInfo':{'name':'cron','version':'1'}}})
print('INIT:', json.dumps(wait_for(1))[:500])

send({'jsonrpc':'2.0','method':'notifications/initialized'})
send({'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}})
tl = wait_for(2)
print('TOOLS:')
for t in (tl or {}).get('result', {}).get('tools', []):
    print(' -', t.get('name'), '|', (t.get('description') or '')[:120])

# pick the list-events like tool
tools = [t.get('name') for t in (tl or {}).get('result', {}).get('tools', [])]
name = None
for cand in tools:
    if 'list' in cand and 'event' in cand:
        name = cand
        break
if not name:
    for cand in tools:
        if 'event' in cand:
            name = cand
            break

if name:
    send({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':name,'arguments':{'days':1}}})
    res = wait_for(3)
    print('CALL_TOOL:', name)
    print(json.dumps(res, indent=2)[:8000])
else:
    print('No event tool found')

try:
    p.stdin.close()
except Exception:
    pass
p.terminate()
