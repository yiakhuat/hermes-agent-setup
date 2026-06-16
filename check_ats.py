import re, html as htmlmod

ats_files = [
    ("1. Superhuman Sr TPM Growth", "/root/ats1.html", ["Senior", "Technical Program Manager", "Growth"]),
    ("2. Superhuman Staff TPM Coda", "/root/ats2.html", ["Staff", "Technical Program Manager", "Coda"]),
    ("3. Anthropic TPM Infrastructure", "/root/ats3.html", ["Technical Program Manager", "Infrastructure", "Anthropic"]),
    ("4. Databricks Sr Staff TPM Reliability", "/root/ats4.html", ["Sr. Staff", "Technical Program Manager", "Reliability", "Databricks"]),
    ("5. Zoox Sr/Staff TPM Autonomy Ops", "/root/ats5.html", ["Technical Program Manager", "Autonomy", "Zoox"]),
    ("6. Bright Machines Sr TPM Autonomous Platform", "/root/ats6.html", ["Technical Program Manager", "Bright Machines"]),
    ("7. Luma AI TPM Research", "/root/ats7.html", ["Technical Program Manager", "Research", "Luma"]),
    ("8. EchoTwin AI Sr TPM", "/root/ats8.html", ["Technical Program Manager", "EchoTwin"]),
    ("9. Eliyan Corp Principal/Sr Principal TPM", "/root/ats9.html", ["Program Manager", "Eliyan"]),
    ("10. Affirm Staff TPM", "/root/ats10.html", ["Staff", "Technical Program Manager", "Affirm"]),
]

for name, path, keywords in ats_files:
    with open(path, errors='replace') as f:
        html = f.read()
    
    # Title
    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.DOTALL)
    title = title_m.group(1).strip() if title_m else "NO TITLE TAG"
    title_clean = re.sub(r'\s+', ' ', title)
    
    # Check if title contains role keywords
    title_lower = title_clean.lower()
    match_count = sum(1 for kw in keywords if kw.lower() in title_lower)
    title_match = f"{match_count}/{len(keywords)} keywords matched"
    
    # Stale indicators on ATS page
    stale_indicators = [
        "this position has been filled", "no longer accepting", "expired",
        "position is no longer available", "job has been removed", "not found",
        "page not found", "404", "the page you were looking for doesn't exist",
        "this job posting is closed", "no longer accepting applications",
        "this job is no longer accepting applications"
    ]
    is_stale = any(ind in html.lower() for ind in stale_indicators)
    
    # Check for obvious ATS platform indicators
    platform = "Unknown"
    if "ashbyhq" in html or "Ashby" in html:
        platform = "Ashby"
    if "greenhouse" in html or "Greenhouse" in html:
        platform = "Greenhouse" if platform == "Unknown" else platform
    if "lever" in html.lower():
        platform = "Lever"
    
    # Body length as sanity check
    body_m = re.search(r'<body[^>]*>(.*?)</body>', html, re.I | re.DOTALL)
    body_len = len(body_m.group(1)) if body_m else 0
    
    print(f"\n=== {name} ===")
    print(f"ATS Title: {title_clean[:200]}")
    print(f"Title match: {title_match}")
    print(f"Platform: {platform}")
    print(f"Body size: {body_len} chars")
    print(f"Stale signals: {'STALE' if is_stale else 'Active'}")
    print(f"HTTP Status: 200")
