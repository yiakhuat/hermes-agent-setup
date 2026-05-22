"""
hermes_dashboard_api.py  v2
Real-time data API for Hermes Agent Office Dashboard
Dynamically reads all personalities + MCP servers from config.yaml
Run: /root/hermes-venv/bin/python3 hermes_dashboard_api.py
"""

import os
import json
import time
import psutil
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HERMES_DIR  = Path("/root/.hermes")
CONFIG_YAML = HERMES_DIR / "config.yaml"
JOB_PROFILE = Path("/root/hermes/tools/job_scout/job_profile.json")
SEEN_JOBS   = Path("/root/hermes/tools/job_scout/seen_jobs.json")
AGENT_LOG   = HERMES_DIR / "logs" / "agent.log"
DASHBOARD   = Path("/root/hermes-agent-office-live.html")

@app.route("/")
def dashboard():
    return send_file(str(DASHBOARD))


# ── Helpers ────────────────────────────────────────────────

def read_tail(path, lines=50):
    try:
        with open(path, "r", errors="ignore") as f:
            return [l.rstrip() for l in f.readlines()[-lines:]]
    except Exception:
        return []


def load_config():
    try:
        with open(CONFIG_YAML) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ── System stats ───────────────────────────────────────────

def get_system_stats():
    net1 = psutil.net_io_counters()
    time.sleep(0.1)
    net2 = psutil.net_io_counters()
    net_mbps = ((net2.bytes_sent - net1.bytes_sent) +
                (net2.bytes_recv - net1.bytes_recv)) / 0.1 / 1024 / 1024
    uptime_s = int(time.time() - psutil.boot_time())
    return {
        "cpu":      round(psutil.cpu_percent(interval=0.5), 1),
        "memory":   round(psutil.virtual_memory().percent, 1),
        "disk":     round(psutil.disk_usage("/").percent, 1),
        "network":  round(min(net_mbps * 10, 100), 1),
        "uptime":   f"{uptime_s//3600}h {(uptime_s%3600)//60}m",
        "hostname": "ubuntu-8gb-nbg1-1",
        "ip":       "188.34.202.40",
    }


# ── Hermes gateway ─────────────────────────────────────────

def get_gateway_status():
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "hermes-gateway"],
            capture_output=True, text=True, timeout=3)
        return r.stdout.strip() == "active"
    except Exception:
        return False


def get_hermes_sessions():
    try:
        d = HERMES_DIR / "sessions"
        return len(list(d.glob("session_*.json"))) if d.exists() else 0
    except Exception:
        return 0


# ── MCP server status ──────────────────────────────────────
def get_mcp_statuses(mcp_server_names):
    statuses = {name: "unknown" for name in mcp_server_names}
    try:
        with open(AGENT_LOG, "r", errors="ignore") as f:
            log_content = f.read()
        import re
        for name in mcp_server_names:
            pattern = "'" + name + "'.*registered"
            if re.search(pattern, log_content):
                statuses[name] = "ok"
            elif "'" + name + "'" in log_content and "failed" in log_content:
                statuses[name] = "failed"
    except Exception as e:
        print(f"MCP status error: {e}")
    return statuses
def get_all_agents():
    import re
    agents = []
    try:
        with open(CONFIG_YAML, 'r') as f:
            raw = f.read()
        mcp_section = re.search(r'mcp_servers:\s*\n((?:[ \t]+\S.*\n?)*)', raw)
        mcp_names = []
        if mcp_section:
            mcp_names = re.findall(r'^\s{2}([\w-]+):', mcp_section.group(1), re.MULTILINE)
        mcp_statuses = get_mcp_statuses(mcp_names)
        for name in mcp_names:
            agents.append({"name": name, "type": "mcp", "status": mcp_statuses.get(name, "unknown"), "prompt": ""})
        pers_section = re.search(r'personalities:\s*\n((?:[ \t]+\S.*\n?)*)', raw)
        if pers_section:
            pers_names = re.findall(r'^\s+([\w-]+):', pers_section.group(1), re.MULTILINE)
            skip = {"null", "system_prompt", "remember"}
            for name in pers_names:
                if name not in skip:
                    agents.append({"name": name, "type": "personality", "status": "ready", "prompt": ""})
    except Exception as e:
        print(f"Error: {e}")
    return agents

def get_job_profile():
    try:
        if JOB_PROFILE.exists():
            with open(JOB_PROFILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def get_seen_jobs_count():
    try:
        if SEEN_JOBS.exists():
            with open(SEEN_JOBS) as f:
                return len(json.load(f))
    except Exception:
        pass
    return 0


# ── Activity log ───────────────────────────────────────────

def get_recent_logs():
    entries = []
    try:
        for line in read_tail(AGENT_LOG, 80)[-15:]:
            if not line.strip():
                continue
            level = "info"
            if "ERROR" in line or "failed" in line.lower():
                level = "warn"
            elif "registered" in line or "started" in line or "OK" in line:
                level = "ok"
            ts  = line[:19] if len(line) > 19 else ""
            msg = line[20:].strip()[:65] if len(line) > 20 else line.strip()
            entries.append({"time": ts, "level": level, "msg": msg})
    except Exception:
        pass
    return entries[-10:]


# ── Cron jobs ──────────────────────────────────────────────

def get_cron_jobs():
    try:
        result = subprocess.run(
            ["/usr/local/bin/hermes", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return [{"name": j.get("name","?")[:20],
                     "schedule": j.get("schedule","?"),
                     "status": j.get("status","?"),
                     "next_run": j.get("next_run","?")} for j in data[:5]]
    except Exception:
        pass
    return [
        {"name":"job-search-daily", "schedule":"0 8 * * *",  "status":"active","next_run":"next: 8h"},
        {"name":"github-push",      "schedule":"0 0 * * *",  "status":"active","next_run":"next: 18h"},
        {"name":"cal-check",        "schedule":"on-demand",  "status":"ready", "next_run":"ready"},
    ]


# ── API endpoints ──────────────────────────────────────────

@app.route("/api/status")
def status():
    sys_stats  = get_system_stats()
    gateway_up = get_gateway_status()
    all_agents = get_all_agents()
    job_profile = get_job_profile()

    mcp_agents  = [a for a in all_agents if a["type"] == "mcp"]
    mcp_ok      = sum(1 for a in mcp_agents if a["status"] == "ok")

    js_agent = next((a for a in all_agents if "job" in a["name"].lower() and a["type"]=="mcp"), None)
    cal_agent = next((a for a in all_agents if "cal" in a["name"].lower() and a["type"]=="mcp"), None)

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu":      sys_stats["cpu"],
            "memory":   sys_stats["memory"],
            "disk":     sys_stats["disk"],
            "network":  sys_stats["network"],
            "uptime":   sys_stats["uptime"],
            "hostname": sys_stats["hostname"],
            "ip":       sys_stats["ip"],
        },
        "hermes": {
            "version":   "0.12.0",
            "gateway":   "online" if gateway_up else "offline",
            "sessions":  get_hermes_sessions(),
            "mcp_ok":    mcp_ok,
            "mcp_total": len(mcp_agents),
        },
        "agents": all_agents,
        "job_scout": {
            "status":     js_agent["status"] if js_agent else "unknown",
            "titles":     job_profile.get("job_titles", []),
            "remote":     job_profile.get("remote_only", False),
            "min_salary": job_profile.get("min_salary"),
            "seen_jobs":  get_seen_jobs_count(),
            "industries": job_profile.get("preferred_industries", []),
        },
        "icloud_calendar": {
            "status": cal_agent["status"] if cal_agent else "unknown",
        },
        "cron_jobs": get_cron_jobs(),
        "logs":      get_recent_logs(),
    })


@app.route("/api/agents")
def agents_endpoint():
    """Dedicated endpoint — returns just the agent list."""
    return jsonify(get_all_agents())


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    print("Starting Hermes Dashboard API v2 on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
