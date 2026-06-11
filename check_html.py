import urllib.request, urllib.error, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

url = 'https://www.builtinsf.com/job/staff-technical-program-manager-queryable-encryption/9646133'
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='replace')

# Save full HTML for inspection
with open('/root/mongodb_debug.html', 'w') as f:
    f.write(html)

print(f"HTML length: {len(html)}")

# Look for __NEXT_DATA__
nd = re.search(r'__NEXT_DATA__\s*=\s*({.*?});', html, re.DOTALL)
if nd:
    print("Found __NEXT_DATA__")
    data = json.loads(nd.group(1))
    print(f'Keys: {list(data.keys())}')
else:
    print("No __NEXT_DATA__")

# Look for jobPostInit
ji = re.search(r'jobPostInit', html)
if ji:
    print("Found jobPostInit")
    # try to extract
    jis = re.search(r'window\.jobPostInit\s*=\s*({.*?});', html, re.DOTALL)
    if jis:
        print(f"jobPostInit excerpt: {jis.group(1)[:500]}")
else:
    print("No jobPostInit")

# Look for JSON-LD
ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld)}")
for i, l in enumerate(ld):
    print(f"  Block {i}: {l[:200]}")

# Check for apply links
for pat, name in [
    (r'https://[^"\'\\s]*greenhouse\.io[^"\'\\s]*', 'greenhouse'),
    (r'https://[^"\'\\s]*ashbyhq\.com[^"\'\\s]*', 'ashby'),
    (r'https://[^"\'\\s]*lever\.co[^"\'\\s]*', 'lever'),
    (r'https://[^"\'\\s]*myworkdayjobs[^"\'\\s]*', 'workday'),
]:
    matches = re.findall(pat, html)
    for m in set(matches):
        print(f'ATS {name}: {m}')
