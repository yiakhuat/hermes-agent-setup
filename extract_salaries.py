import urllib.request, urllib.error, json, re, time

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def extract_range(html, label):
    """Find the salary range that is explicitly stated for this specific role"""
    # Look for patterns like "$151,000 - $297,000" or "$151K-$297K"
    ranges = re.findall(r'\$(\d{1,3}[,\d]*)\s*[-–]+to?\s*\$?(\d{1,3}[,\d]*)', html)
    if ranges:
        for low, high in ranges:
            l = int(low.replace(',', ''))
            h = int(high.replace(',', ''))
            if h > 30000 and h < 500000:  # reasonable salary range
                return f'${l:,} - ${h:,}'
    
    k_ranges = re.findall(r'(\d{2,3})[Kk]\s*[-–]+\s*(\d{2,3})[Kk]', html)
    if k_ranges:
        for low, high in k_ranges:
            l = int(low) * 1000
            h = int(high) * 1000
            if h > 30000 and h < 500000:
                return f'${l:,} - ${h:,}'
    
    return None

def extract_location(html):
    """Extract job location from the page"""
    # Check for specific location in page text, not just generic city mentions
    loc_section = re.search(r'(?:Location|location)[^<]{0,50}(?:<[^>]*>){0,5}([^<]{0,100})', html)
    if loc_section:
        txt = loc_section.group(1).strip()
        if len(txt) < 100 and txt:
            return txt
    
    # Check specific patterns
    patterns = [
        r'"locationText"\s*:\s*"([^"]+)"',
        r'>(Remote|Hybrid|On-site|On Site|In Office)<',
        r'(?:in|at)\s+(San Francisco|Bay Area|Seattle|New York|Austin|Chicago|Denver|Los Angeles)',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1)
    
    return None

urls = [
    ('MongoDB', 'https://www.builtinsf.com/job/staff-technical-program-manager-queryable-encryption/9646133'),
    ('Affirm', 'https://www.builtinsf.com/job/staff-technical-program-manager/9330767'),
    ('Baseten', 'https://www.builtinsf.com/job/technical-program-manager-infrastructure/9678649'),
    ('Peregrine', 'https://www.builtinsf.com/job/senior-technical-program-manager/9678067'),
    ('Anthropic Inference', 'https://www.builtinsf.com/job/technical-program-manager-inference-performance/8394413'),
    ('Anthropic Safeguards', 'https://www.builtinsf.com/job/technical-program-manager-reliability-engineering/8406309'),
    ('Lyft', 'https://www.builtinsf.com/job/senior-technical-program-manager/8569355'),
    ('Blue Origin', 'https://www.builtinsf.com/job/principal-technical-program-manager-feic-asic-development-terawave/9674468'),
    ('CoreWeave Capacity', 'https://www.builtinsf.com/job/technical-program-manager-capacity-delivery/9689018'),
    ('CoreWeave Staff', 'https://www.builtinsf.com/job/staff-technical-program-manager-expansion-pmo/9596568'),
    ('Deepgram', 'https://www.builtinsf.com/job/technical-program-manager-research/8556932'),
    ('Grow Therapy', 'https://www.builtinsf.com/job/senior-technical-program-manager-internal-foundations/9562483'),
    ('Superhuman Sr', 'https://www.builtinsf.com/job/senior-technical-program-manager-growth/9383286'),
    ('Superhuman Staff', 'https://www.builtinsf.com/job/staff-technical-program-manager-coda/9383295'),
    ('Zscaler AuthOps', 'https://www.builtinsf.com/job/staff-technical-program-manager-federal-authops/9259294'),
    ('Zscaler DoW', 'https://www.builtinsf.com/job/sr-staff-technical-program-manager-dow/9478478'),
]

for name, url in urls:
    time.sleep(3)
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8', errors='replace')
    
    sal = extract_range(html, name)
    
    # Check for remote/hybrid specifically
    work_type = ''
    if re.search(r'\bRemote\b', html):
        work_type = 'Remote'
    if re.search(r'\bHybrid\b', html):
        work_type = 'Hybrid' if not work_type else f'{work_type}/Hybrid'
    if re.search(r'\bOn.site\b', html, re.IGNORECASE) or re.search(r'\bOn[- ]Site\b', html, re.IGNORECASE):
        work_type = 'On-site' if not work_type else f'{work_type}/On-site'
    
    print(f'{name}: Salary={sal} | Work={work_type}')
