import urllib.request, urllib.error, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

urls_to_check = [
    ('MongoDB', 'https://www.builtinsf.com/job/staff-technical-program-manager-queryable-encryption/9646133'),
    ('Affirm', 'https://www.builtinsf.com/job/staff-technical-program-manager/9330767'),
    ('Anthropic Inference', 'https://www.builtinsf.com/job/technical-program-manager-inference-performance/8394413'),
    ('Lyft', 'https://www.builtinsf.com/job/senior-technical-program-manager/8569355'),
    ('Blue Origin', 'https://www.builtinsf.com/job/principal-technical-program-manager-feic-asic-development-terawave/9674468'),
    ('CoreWeave Capacity', 'https://www.builtinsf.com/job/technical-program-manager-capacity-delivery/9689018'),
    ('Deepgram', 'https://www.builtinsf.com/job/technical-program-manager-research/8556932'),
    ('Zscaler AuthOps', 'https://www.builtinsf.com/job/staff-technical-program-manager-federal-authops/9259294'),
]

for name, url in urls_to_check:
    print(f'\n=== {name} ===')
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8', errors='replace')
    
    # Look for salary-related text
    for pat in [
        r'\$\d{1,3}[,\d]*\s*[-–to]+\s*\$?\d{1,3}[,\d]*(?:\s*[Kk])?',
        r'\$\d{1,3}[,\d]*(?:\s*[-–]\s*\$?\d{1,3}[,\d]*)?(?:\s*[Kk])?(?:\s*(?:a|per)\s*(?:year|yr|annum))?',
        r'salary.*?\$\d',
        r'\d{2,3}[Kk]\s*[-–]\s*\d{2,3}[Kk]',
    ]:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            if len(m) > 5:
                print(f'  Salary match: {m.strip()}')
    
    # Look for location info
    for pat in [
        r'"locationText"\s*:\s*"([^"]+)"',
        r'"location"\s*:\s*"([^"]+)"',
        r'(San Francisco|CA|California|Bay Area|Remote|Hybrid|On.site|New York|Seattle|Austin|Denver|Chicago)',
    ]:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in set(matches):
            if isinstance(m, str) and len(m) < 100:
                print(f'  Location/city: {m}')
    
    # Check for salary in jobPostInit - look at full config
    ji = re.search(r'jobPostInit\((.*?)\);', html, re.DOTALL)
    if ji:
        try:
            config = json.loads(ji.group(1))
            for k in config:
                if isinstance(config[k], dict):
                    for k2 in config[k]:
                        if 'salar' in k2.lower() or 'pay' in k2.lower() or 'range' in k2.lower() or 'comp' in k2.lower() or 'locat' in k2.lower():
                            print(f'  Config.{k}.{k2}: {config[k][k2]}')
                if 'salar' in k.lower() or 'pay' in k.lower() or 'range' in k.lower() or 'comp' in k.lower() or 'locat' in k.lower():
                    print(f'  Config.{k}: {config[k]}')
            if 'job' in config:
                jj = config['job']
                for k in jj:
                    if k not in ['id', 'drupalId', 'isSaved', 'howToApply', 'companyName', 'title', 'isEasyApply', 'resolvedBidId']:
                        print(f'  Job extra field: {k} = {jj[k]}')
        except:
            pass

    # Also check for salary in HTML body text
    body = re.search(r'<div[^>]*class=["\']content[^>]*>(.*?)</div>', html, re.DOTALL)
    if body:
        text = body.group(1)
        sal = re.search(r'\$\d{1,3}[,\d]*(?:\s*[-–]\s*\$?\d{1,3}[,\d]*)?(?:\s*k|\s*K)?(?:\s*(?:a|per)\s*(?:year|yr))?', text)
        if sal:
            print(f'  Body salary: {sal.group()}')
