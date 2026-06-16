import re, json, sys

files = [
    ("1. Superhuman Sr TPM Growth", "/root/job1.html"),
    ("2. Superhuman Staff TPM Coda", "/root/job2.html"),
    ("3. Anthropic TPM Infrastructure", "/root/job3.html"),
    ("4. Databricks Sr Staff TPM Reliability", "/root/job4.html"),
    ("5. Zoox Sr/Staff TPM Autonomy Ops", "/root/job5.html"),
    ("6. Bright Machines Sr TPM Autonomous Platform", "/root/job6.html"),
    ("7. Luma AI TPM Research", "/root/job7.html"),
    ("8. EchoTwin AI Sr TPM", "/root/job8.html"),
    ("9. Eliyan Corp Principal/Sr Principal TPM", "/root/job9.html"),
    ("10. Affirm Staff TPM", "/root/job10.html"),
]

for name, path in files:
    with open(path) as f:
        html = f.read()
    
    # Title from <title>
    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.DOTALL)
    title = title_m.group(1).strip() if title_m else "NOT FOUND"
    
    # Salary from JSON-LD or page text
    salary = "Not listed"
    ld_m = re.search(r'"@type"\s*:\s*"JobPosting".*?"baseSalary".*?"minValue":(\d+).*?"maxValue":(\d+)', html, re.DOTALL)
    if ld_m:
        minv = int(ld_m.group(1))
        maxv = int(ld_m.group(2))
        salary = f"${minv:,} - ${maxv:,}"
    else:
        sal_m = re.findall(r'\$(\d{1,3}),?(\d{3})\s*[–\-—]\s*\$(\d{1,3}),?(\d{3})', html)
        if sal_m:
            salary = f"${sal_m[0][0]},{sal_m[0][1]} - ${sal_m[0][2]},{sal_m[0][3]}"
    
    # howToApply from Builtin.jobPostInit
    hta = "None found"
    hta_m = re.search(r'"howToApply"\s*:\s*"([^"]+)"', html)
    if hta_m:
        hta = hta_m.group(1).replace('\\u0026', '&')
    
    # ATS URLs in the full page
    ats_urls = re.findall(r'(https?://(?:boards\.greenhouse\.io|jobs\.ashbyhq\.com|jobs\.lever\.co|workday\.com)[^"\'<\s]+)', html)
    # Deduplicate
    ats_urls = list(set(ats_urls))
    
    # directApply
    direct_apply = re.search(r'"directApply"\s*:\s*(true|false)', html)
    direct = direct_apply.group(1) if direct_apply else "unknown"
    
    # Location
    loc_m = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', html)
    loc = loc_m.group(1) if loc_m else "Not found"
    
    # Work mode
    work_mode = "Not specified"
    for mode in ["Remote", "Hybrid", "On-site", "In-Office"]:
        if re.search(mode.replace("-", "[- ]?"), html, re.I):
            work_mode = mode
            break
    
    # Stale check
    stale_indicators = ["this position has been filled", "no longer accepting", "expired", "job has been removed", "position is no longer available"]
    is_stale = any(ind in html.lower() for ind in stale_indicators)
    
    print(f"\n=== {name} ===")
    print(f"Job Title: {title[:150]}")
    print(f"Salary: {salary}")
    print(f"Location: {loc} | Work mode: {work_mode}")
    print(f"Direct Apply: {direct}")
    print(f"HowToApply: {hta[:200]}")
    if ats_urls:
        for u in ats_urls:
            print(f"ATS URL: {u}")
    else:
        print("ATS URL: None found")
    print(f"Stale signals: {'STALE' if is_stale else 'Active'}")
    print(f"HTTP Status: 200")
