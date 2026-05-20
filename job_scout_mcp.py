import asyncio, os, json, time, hashlib, requests
from datetime import datetime, timedelta
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("job-scout")

# ── Paths ──────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent / "hermes" / "tools" / "job_scout"
PROFILE_FILE = BASE_DIR / "job_profile.json"
SEEN_FILE    = BASE_DIR / "seen_jobs.json"

DEFAULT_PROFILE = {
    "job_titles": [],
    "keywords": [],
    "locations": [],
    "remote_only": False,
    "min_salary": None,
    "max_salary": None,
    "experience_level": None,
    "exclude_companies": [],
    "preferred_industries": [],
    "country": "us",
    "results_per_search": 10,
    "max_days_old": 7,
}

# ── Profile helpers ────────────────────────────────────

def load_profile():
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE) as f:
            return {**DEFAULT_PROFILE, **json.load(f)}
    return DEFAULT_PROFILE.copy()

def save_profile(profile):
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=2)

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(job):
    key = f"{job.get('title','')}{job.get('company','')}{job.get('url','')}"
    return hashlib.md5(key.encode()).hexdigest()

# ── Adzuna ─────────────────────────────────────────────

def search_adzuna(query, profile):
    app_id  = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []
    params = {
        "app_id": app_id, "app_key": app_key,
        "what": query,
        "results_per_page": profile.get("results_per_search", 10),
        "max_days_old": profile.get("max_days_old", 7),
    }
    if profile.get("remote_only"):
        params["where"] = "remote"
    elif profile.get("locations"):
        params["where"] = profile["locations"][0]
    if profile.get("min_salary"):
        params["salary_min"] = profile["min_salary"]
    try:
        r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{profile.get('country','us')}/search/1",
            params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception:
        return []
    jobs = []
    for item in results:
        lo, hi = item.get("salary_min"), item.get("salary_max")
        salary = f"${int(lo):,}–${int(hi):,}" if lo and hi else ("$"+str(int(lo))+",000+" if lo else "Not listed")
        jobs.append({
            "source": "Adzuna",
            "title": item.get("title", ""),
            "company": item.get("company", {}).get("display_name", ""),
            "location": item.get("location", {}).get("display_name", ""),
            "salary": salary,
            "posted": item.get("created", "")[:10],
            "url": item.get("redirect_url", ""),
            "snippet": item.get("description", "")[:300],
        })
    return jobs

# ── JSearch ────────────────────────────────────────────

def search_jsearch(query, profile):
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        return []
    q = query
    if profile.get("remote_only"):
        q += " remote"
    elif profile.get("locations"):
        q += f" {profile['locations'][0]}"
    days = profile.get("max_days_old", 7)
    date_filter = "today" if days <= 1 else "3days" if days <= 3 else "week" if days <= 7 else "month"
    params = {"query": q, "num_pages": "1", "date_posted": date_filter, "employment_types": "FULLTIME"}
    if profile.get("remote_only"):
        params["remote_jobs_only"] = "true"
    try:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
            params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception:
        return []
    jobs = []
    for item in data:
        city, state = item.get("job_city",""), item.get("job_state","")
        location = "Remote" if item.get("job_is_remote") else ", ".join(p for p in [city, state] if p) or "Not listed"
        lo, hi = item.get("job_min_salary"), item.get("job_max_salary")
        salary = f"${int(lo):,}–${int(hi):,}" if lo and hi else "Not listed"
        jobs.append({
            "source": "JSearch",
            "title": item.get("job_title", ""),
            "company": item.get("employer_name", ""),
            "location": location,
            "salary": salary,
            "posted": item.get("job_posted_at_datetime_utc", "")[:10],
            "url": item.get("job_apply_link", ""),
            "snippet": item.get("job_description", "")[:300],
        })
    return jobs

# ── Filter & rank ──────────────────────────────────────

def filter_and_rank(jobs, profile):
    exclude  = [c.lower() for c in profile.get("exclude_companies", [])]
    targets  = [t.lower() for t in profile.get("job_titles", [])]
    keywords = [k.lower() for k in profile.get("keywords", [])]
    preferred = [i.lower() for i in profile.get("preferred_industries", [])]
    all_terms = targets + keywords

    filtered = []
    for job in jobs:
        if job["company"].lower() in exclude:
            continue
        if profile.get("remote_only") and "remote" not in job["location"].lower():
            continue
        if all_terms and not any(t in job["title"].lower() for t in all_terms):
            continue
        filtered.append(job)

    def score(job):
        s = sum(10 for t in targets if t in job["title"].lower())
        s += sum(3 for i in preferred if i in (job["snippet"]+job["company"]).lower())
        s += 2 if job["salary"] != "Not listed" else 0
        try:
            days_old = (datetime.utcnow().date() - datetime.strptime(job["posted"], "%Y-%m-%d").date()).days
            s += max(0, 7 - days_old)
        except Exception:
            pass
        return s

    return sorted(filtered, key=score, reverse=True)

# ── Format digest ──────────────────────────────────────

def format_digest(jobs, profile):
    lines = [f"🎯 Job Scout Digest — {datetime.now().strftime('%b %d, %Y')}\n",
             f"Found {len(jobs)} matching role(s):\n"]
    for i, job in enumerate(jobs, 1):
        lines += [
            f"{'─'*48}",
            f"{i}. {job['title']} @ {job['company']}",
            f"   📍 {job['location']}",
            f"   💰 {job['salary']}",
            f"   📅 {job['posted']}  |  🔗 {job['url']}",
            f"   📝 {job['snippet'][:200].replace(chr(10),' ')}...",
            "",
        ]
    lines.append(f"Searched: {', '.join(profile['job_titles'][:3])} | Sources: Adzuna + JSearch")
    return "\n".join(lines)

# ── Core functions ─────────────────────────────────────

def do_search_jobs(custom_query=None, show_seen=False):
    profile = load_profile()
    if not profile["job_titles"] and not profile["keywords"] and not custom_query:
        return ("No job preferences set yet!\n"
                "Tell me what roles you're looking for, e.g.:\n"
                "'Remember I want Senior TPM roles, remote, US-based, above $160k'")
    queries = [custom_query] if custom_query else (profile["job_titles"] or profile["keywords"][:2])
    seen = load_seen() if not show_seen else set()
    all_jobs = []
    for q in queries:
        all_jobs.extend(search_adzuna(q, profile))
        time.sleep(0.5)
        all_jobs.extend(search_jsearch(q, profile))
        time.sleep(0.5)
    unique = {}
    for job in all_jobs:
        jid = job_id(job)
        if jid not in seen and jid not in unique:
            unique[jid] = job
    ranked = filter_and_rank(list(unique.values()), profile)
    if not ranked:
        return "No new matching jobs found right now. Try again tomorrow or broaden your preferences."
    save_seen(seen | set(unique.keys()))
    return format_digest(ranked, profile)

def do_update_profile(**kwargs):
    profile = load_profile()
    for k, v in kwargs.items():
        if k in profile:
            profile[k] = v
    save_profile(profile)
    p = profile
    lines = ["✅ Preferences saved!\n",
             f"  Job Titles  : {', '.join(p['job_titles']) or 'Not set'}",
             f"  Keywords    : {', '.join(p['keywords']) or 'Not set'}",
             f"  Locations   : {', '.join(p['locations']) or 'Not set'}",
             f"  Remote Only : {'Yes' if p['remote_only'] else 'No'}",
             f"  Min Salary  : ${p['min_salary']:,}" if p['min_salary'] else "  Min Salary  : Not set",
             f"  Experience  : {p['experience_level'] or 'Not set'}",
             f"  Exclude Cos : {', '.join(p['exclude_companies']) or 'None'}",
             f"  Industries  : {', '.join(p['preferred_industries']) or 'Any'}",
             f"  Max Age     : {p['max_days_old']} days"]
    return "\n".join(lines)

def do_show_profile():
    p = load_profile()
    lines = ["📋 Your Job Search Profile:\n",
             f"  Job Titles  : {', '.join(p['job_titles']) or 'Not set'}",
             f"  Keywords    : {', '.join(p['keywords']) or 'Not set'}",
             f"  Locations   : {', '.join(p['locations']) or 'Not set'}",
             f"  Remote Only : {'Yes' if p['remote_only'] else 'No'}",
             f"  Min Salary  : ${p['min_salary']:,}" if p['min_salary'] else "  Min Salary  : Not set",
             f"  Experience  : {p['experience_level'] or 'Not set'}",
             f"  Exclude Cos : {', '.join(p['exclude_companies']) or 'None'}",
             f"  Industries  : {', '.join(p['preferred_industries']) or 'Any'}",
             f"  Max Age     : {p['max_days_old']} days"]
    return "\n".join(lines)

# ── MCP Tool definitions ───────────────────────────────

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="search_jobs",
            description=(
                "Search job boards for listings matching saved preferences. "
                "Returns a filtered, ranked digest of new postings. "
                "Call when the user asks to find jobs, check for new listings, or run a job search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "custom_query": {"type": "string", "description": "Optional: override the saved search query"},
                    "show_seen":    {"type": "boolean", "description": "Include previously shown jobs. Default false."},
                },
            },
        ),
        types.Tool(
            name="update_job_profile",
            description=(
                "Save or update the user's job search preferences persistently. "
                "Call when the user says things like: 'Remember I want Senior TPM roles', "
                "'Only show remote jobs', 'I want jobs above $160k', 'Exclude Amazon'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_titles":           {"type": "array", "items": {"type": "string"}},
                    "keywords":             {"type": "array", "items": {"type": "string"}},
                    "locations":            {"type": "array", "items": {"type": "string"}},
                    "remote_only":          {"type": "boolean"},
                    "min_salary":           {"type": "number"},
                    "max_salary":           {"type": "number"},
                    "experience_level":     {"type": "string", "enum": ["mid","senior","staff","principal","director"]},
                    "exclude_companies":    {"type": "array", "items": {"type": "string"}},
                    "preferred_industries": {"type": "array", "items": {"type": "string"}},
                    "max_days_old":         {"type": "integer"},
                    "country":              {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="show_job_profile",
            description="Show the user's current saved job search preferences.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_jobs":
        result = do_search_jobs(
            custom_query=arguments.get("custom_query"),
            show_seen=arguments.get("show_seen", False),
        )
    elif name == "update_job_profile":
        result = do_update_profile(**arguments)
    elif name == "show_job_profile":
        result = do_show_profile()
    else:
        result = f"Unknown tool: {name}"
    return [types.TextContent(type="text", text=result)]

# ── Entry point ────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
