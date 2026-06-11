#!/usr/bin/env python3
import urllib.request, urllib.error, json, re, time, sys

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

all_jobs = []

def fetch_bi(url, label):
    job = {
        'id': label.split('.')[0],
        'name': label.split('. ')[1] if '. ' in label else label,
        'url': url,
        'title': '',
        'company': '',
        'salary': '',
        'location': '',
        'active': True,
        'ats_links': [],
        'apply_url': '',
        'work_type': '',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode('utf-8', errors='replace')
        
        # Extract jobPostInit config
        ji = re.search(r'jobPostInit\((.*?)\);', html, re.DOTALL)
        if ji:
            try:
                config = json.loads(ji.group(1))
                j = config.get('job', {})
                job['title'] = j.get('title', '')
                job['company'] = j.get('companyName', '')
                hta = j.get('howToApply', '')
                if hta:
                    job['apply_url'] = hta
                    job['ats_links'].append(('howToApply', hta))
            except:
                pass
        
        # Also check for additional data in the page
        # salary
        sal_match = re.search(r'"salaryRange"\s*:\s*"([^"]+)"', html)
        if sal_match:
            job['salary'] = sal_match.group(1)
        
        # location
        loc_match = re.search(r'"locationText"\s*:\s*"([^"]+)"', html)
        if loc_match:
            job['location'] = loc_match.group(1)
        
        # company name from other sources
        comp_match = re.search(r'"companyName"\s*:\s*"([^"]+)"', html)
        if comp_match:
            job['company'] = comp_match.group(1)
        
        # title from other sources
        title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        if title_match:
            if not job['title']:
                t = title_match.group(1).strip()
                # Remove "| Built In San Francisco"
                t = re.sub(r'\s*\|.*$', '', t)
                job['title'] = t
        
        # ATS links from all over HTML
        ats_pats = [
            (r'https://[^"\'\\s]*greenhouse\.io[^"\'\\s]*', 'greenhouse'),
            (r'https://[^"\'\\s]*ashbyhq\.com[^"\'\\s]*', 'ashby'),
            (r'https://[^"\'\\s]*jobs\.ashbyhq\.com[^"\'\\s]*', 'ashby'),
            (r'https://[^"\'\\s]*lever\.co[^"\'\\s]*', 'lever'),
            (r'https://[^"\'\\s]*(myworkdayjobs|wd5|jobs\.workday)\.com[^"\'\\s]*', 'workday'),
            (r'(gh_jid/[^"\'\\s]+)', 'gh_jid'),
        ]
        for pat, at in ats_pats:
            matches = re.findall(pat, html)
            for m in set(matches):
                if at == 'gh_jid':
                    full_url = f'https://www.mongodb.com/careers/job/?{m.split("?")[-1]}' if '?' not in m else f'https://www.mongodb.com/careers/job/?{m}'
                    job['ats_links'].append(('greenhouse', full_url))
                else:
                    job['ats_links'].append((at, m))
        
        # Work type
        for wt in ['Remote', 'Hybrid', 'On-site', 'On Site', 'In Office']:
            if wt.lower() in html.lower():
                job['work_type'] = wt
                break
        
        # Active check
        expired = re.search(r'(no longer accepting|position filled|this job has been filled|expired|this posting is no longer)', html, re.IGNORECASE)
        if expired:
            job['active'] = False
        
        # Check for ATS from howToApply if we didn't get apply_url from config
        hta2 = re.search(r'"howToApply"\s*:\s*"([^"]+)"', html)
        if hta2 and not job['apply_url']:
            job['apply_url'] = hta2.group(1)
        
    except urllib.error.HTTPError as e:
        job['active'] = False
        job['error'] = f'HTTP {e.code}'
    except Exception as e:
        job['active'] = False
        job['error'] = str(e)
    
    return job

def verify_ats(job):
    """Verify the ATS page is still accepting applications"""
    if not job['apply_url']:
        job['ats_verified'] = False
        job['ats_status'] = 'No ATS URL found'
        return
    
    url = job['apply_url']
    # Fix backslash escaping
    url = url.replace('\\u0026', '&')
    
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        ats_html = resp.read().decode('utf-8', errors='replace')
        job['ats_http'] = resp.status
        
        # Check title
        title_m = re.search(r'<title>(.*?)</title>', ats_html, re.DOTALL)
        job['ats_title'] = title_m.group(1).strip() if title_m else '(no title)'
        
        # Check for "no longer accepting" signals
        closed = re.search(r'(no longer accepting|position has been filled|this job is no longer|this position has been filled|job has been closed)', ats_html, re.IGNORECASE)
        if closed:
            job['ats_verified'] = False
            job['ats_status'] = f'CLOSED: {closed.group(1)}'
        else:
            job['ats_verified'] = True
            job['ats_status'] = 'Active - accepting applications'
            
            # Check for apply button
            apply_btn = re.search(r'(apply|Apply|APPLY).{0,30}(button|Button|btn)', ats_html)
            if apply_btn:
                job['ats_status'] += ' (apply button found)'
            else:
                # Greenhouse has specific patterns
                if 'greenhouse' in url:
                    if 'bdi' in ats_html or re.search(r'\$\d{2,3}[,\dk]', ats_html):
                        job['ats_status'] += ' (has salary info)'
                
    except urllib.error.HTTPError as e:
        job['ats_verified'] = False
        job['ats_status'] = f'HTTP {e.code}'
    except Exception as e:
        job['ats_verified'] = False
        job['ats_status'] = f'Error: {str(e)[:50]}'

def print_results(jobs):
    print(f'\n{"="*80}')
    print(f'VERIFICATION RESULTS - {len(jobs)} TPM Postings')
    print(f'{"="*80}')
    for j in jobs:
        print(f'\n--- #{j["id"]}: {j["name"]} ---')
        print(f'Title: {j["title"]}')
        print(f'Company: {j["company"]}')
        print(f'Salary: {j["salary"] or "Not listed"}')
        print(f'Location: {j["location"] or "Not listed"}')
        print(f'Work type: {j.get("work_type", "Not specified")}')
        print(f'Active on BuiltIn: {"YES" if j["active"] else "NO"}')
        if j.get('error'):
            print(f'Error: {j["error"]}')
        if j['apply_url']:
            print(f'Apply URL: {j["apply_url"]}')
        else:
            print(f'Apply URL: Not found on BuiltIn page')
        if j.get('ats_links'):
            seen = set()
            for t, u in j['ats_links']:
                if u not in seen:
                    seen.add(u)
                    print(f'  ATS ({t}): {u}')
        if j.get('ats_status'):
            print(f'ATS Status: {j["ats_status"]}')
        if j.get('ats_title'):
            print(f'ATS Page Title: {j["ats_title"][:80]}')

# All 16 URLs
all_urls = [
    ('1', 'MongoDB Staff TPM Queryable Encryption', 'https://www.builtinsf.com/job/staff-technical-program-manager-queryable-encryption/9646133'),
    ('2', 'Affirm Staff TPM', 'https://www.builtinsf.com/job/staff-technical-program-manager/9330767'),
    ('3', 'Baseten TPM Infrastructure', 'https://www.builtinsf.com/job/technical-program-manager-infrastructure/9678649'),
    ('4', 'Peregrine Technologies Sr TPM', 'https://www.builtinsf.com/job/senior-technical-program-manager/9678067'),
    ('5', 'Anthropic TPM Inference Performance', 'https://www.builtinsf.com/job/technical-program-manager-inference-performance/8394413'),
    ('6', 'Anthropic TPM Safeguards', 'https://www.builtinsf.com/job/technical-program-manager-reliability-engineering/8406309'),
    ('7', 'Lyft Sr TPM Product & Rider Loyalty', 'https://www.builtinsf.com/job/senior-technical-program-manager/8569355'),
    ('8', 'Blue Origin Principal TPM ASIC', 'https://www.builtinsf.com/job/principal-technical-program-manager-feic-asic-development-terawave/9674468'),
    ('9', 'CoreWeave TPM Capacity Delivery', 'https://www.builtinsf.com/job/technical-program-manager-capacity-delivery/9689018'),
    ('10', 'CoreWeave Staff TPM Expansion PMO', 'https://www.builtinsf.com/job/staff-technical-program-manager-expansion-pmo/9596568'),
    ('11', 'Deepgram TPM Research', 'https://www.builtinsf.com/job/technical-program-manager-research/8556932'),
    ('12', 'Grow Therapy Sr TPM Internal Foundations', 'https://www.builtinsf.com/job/senior-technical-program-manager-internal-foundations/9562483'),
    ('13', 'Superhuman Sr TPM Growth', 'https://www.builtinsf.com/job/senior-technical-program-manager-growth/9383286'),
    ('14', 'Superhuman Staff TPM Coda', 'https://www.builtinsf.com/job/staff-technical-program-manager-coda/9383295'),
    ('15', 'Zscaler Staff TPM Federal AuthOps', 'https://www.builtinsf.com/job/staff-technical-program-manager-federal-authops/9259294'),
    ('16', 'Zscaler Sr Staff TPM DoW', 'https://www.builtinsf.com/job/sr-staff-technical-program-manager-dow/9478478'),
]

# Fetch all BuiltIn pages in batches of 5 with delays
jobs = []
for i in range(0, len(all_urls), 5):
    batch = all_urls[i:i+5]
    print(f'\n--- Fetching batch {i//5 + 1} ({len(batch)} URLs) ---')
    for idx, name, url in batch:
        j = fetch_bi(url, f'{idx}. {name}')
        jobs.append(j)
        print(f'  {idx}. {name}: active={j["active"]}, apply_url={"found" if j["apply_url"] else "none"}')
        sys.stdout.flush()
        time.sleep(5)
    if i + 5 < len(all_urls):
        print('  Waiting 10 seconds before next batch...')
        time.sleep(10)

print(f'\n{"="*80}')
print(f'ALL 16 BuiltIn pages fetched. Now verifying ATS pages...')
print(f'{"="*80}')

# Now verify ATS pages for active jobs
for j in jobs:
    if j['active'] and j['apply_url']:
        print(f'\nVerifying ATS for #{j["id"]}: {j["name"]}')
        verify_ats(j)
        print(f'  ATS Status: {j["ats_status"]}')
        sys.stdout.flush()
        time.sleep(3)

print_results(jobs)

# Save to JSON
with open('/root/results_all.json', 'w') as f:
    # Convert to serializable dicts
    serializable = []
    for j in jobs:
        s = {k: v for k, v in j.items() if k != 'ats_links' or v}
        f.write(json.dumps(s, indent=2) + '\n')

print(f'\nResults saved to /root/results_all.json')
