#!/usr/bin/env python3
import urllib.request, urllib.error, json, re, time, sys

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def fetch_bi(url, label):
    out = []
    out.append(f'\n{"="*60}')
    out.append(f'=== {label} ===')
    out.append(f'URL: {url}')
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode('utf-8', errors='replace')
        
        # JSON-LD
        ld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        for ld_str in ld_matches:
            try:
                ld = json.loads(ld_str)
                if isinstance(ld, dict) and ld.get('@type') == 'JobPosting':
                    out.append(f'Title: {ld.get("title","N/A")}')
                    out.append(f'DatePosted: {ld.get("datePosted","N/A")}')
                    out.append(f'ValidThrough: {ld.get("validThrough","N/A")}')
                    sal = ld.get('baseSalary', {})
                    if isinstance(sal, dict):
                        out.append(f'Salary: {json.dumps(sal)}')
                    org = ld.get('hiringOrganization', {})
                    out.append(f'Company: {org.get("name","N/A")}')
                    loc = ld.get('jobLocation', {})
                    if isinstance(loc, dict):
                        out.append(f'Location: {loc.get("address",{}).get("addressLocality","N/A")}')
            except:
                pass
        
        # BuiltIn jobPostInit config
        config_match = re.search(r'window\.jobPostInit\s*=\s*({.*?});', html, re.DOTALL)
        if config_match:
            try:
                config_str = config_match.group(1)
                config = json.loads(config_str)
                for key in ['jobTitle', 'companyName', 'salaryRange', 'location', 'applyUrl', 'howToApply']:
                    if key in config:
                        val = config[key]
                        if isinstance(val, str) and len(val) > 300:
                            val = val[:300] + '...'
                        out.append(f'{key}: {val}')
            except Exception as e:
                out.append(f'Config parse error: {e}')
        
        # ATS links
        ats_pats = [
            (r'https://[^"\'\\s]*greenhouse\.io[^"\'\\s]*', 'greenhouse'),
            (r'https://[^"\'\\s]*ashbyhq\.com[^"\'\\s]*', 'ashby'),
            (r'https://[^"\'\\s]*lever\.co[^"\'\\s]*', 'lever'),
            (r'https://[^"\'\\s]*(myworkdayjobs|wd5|jobs\.workday)\.com[^"\'\\s]*', 'workday'),
            (r'gh_jid/[^"\'\\s]+', 'gh_jid'),
            (r'https://[^"\'\\s]*jobs\.ashbyhq[^"\'\\s]*', 'ashby'),
        ]
        for pat, at in ats_pats:
            matches = re.findall(pat, html)
            for m in set(matches):
                out.append(f'ATS ({at}): {m}')
        
        # Location text
        loc_t = re.search(r'"locationText"\s*:\s*"([^"]+)"', html)
        if loc_t:
            out.append(f'Location: {loc_t.group(1)}')
        
        # Salary text
        sal_t = re.search(r'"salaryRange"\s*:\s*"([^"]+)"', html)
        if sal_t:
            out.append(f'Salary: {sal_t.group(1)}')
        
        # Check active
        expired = re.search(r'(no longer accepting|position filled|this job has been filled|expired|unfilled|closed|job has been filled)', html, re.IGNORECASE)
        out.append(f'Active: {"YES" if not expired else "NO (expired signal)"}')
        
        # Check page title
        title_m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        if title_m:
            out.append(f'Page title: {title_m.group(1).strip()}')
        
    except urllib.error.HTTPError as e:
        out.append(f'ERROR: HTTP {e.code} {e.reason}')
    except Exception as e:
        out.append(f'ERROR: {e}')
    
    return '\n'.join(out)

labels = [
    ('1. MongoDB Staff TPM Queryable Encryption', 'https://www.builtinsf.com/job/staff-technical-program-manager-queryable-encryption/9646133'),
    ('2. Affirm Staff TPM', 'https://www.builtinsf.com/job/staff-technical-program-manager/9330767'),
    ('3. Baseten TPM Infrastructure', 'https://www.builtinsf.com/job/technical-program-manager-infrastructure/9678649'),
    ('4. Peregrine Technologies Sr TPM', 'https://www.builtinsf.com/job/senior-technical-program-manager/9678067'),
    ('5. Anthropic TPM Inference Performance', 'https://www.builtinsf.com/job/technical-program-manager-inference-performance/8394413'),
]
all_out = []
for label, url in labels:
    result = fetch_bi(url, label)
    all_out.append(result)
    print(result)
    sys.stdout.flush()
    time.sleep(4)

with open('/root/results_batch1.txt', 'w') as f:
    f.write('\n'.join(all_out))
print('\nBatch 1 complete. Results saved to /root/results_batch1.txt')
