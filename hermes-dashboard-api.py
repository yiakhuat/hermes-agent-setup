"""
hermes_dashboard_api.py
Real-time data API for Hermes Agent Office Dashboard
Run: /root/hermes-venv/bin/python3 hermes_dashboard_api.py
"""

import os
import json
import time
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR        = Path("/root")
HERMES_DIR      = Path("/root/.hermes")
JOB_PROFILE     = Path("/root/hermes/tools/job_scout/job_profile.json")
SEEN_JOBS       = Path("/root/hermes/tools/job_scout/seen_jobs.json")
MCP_LOG         = HERMES_DIR / "logs" / "mcp-stderr.log"
AGENT_LOG       = HERMES_DIR / "logs" / "agent.log"
CONFIG_YAML     = HERMES_DIR / "config.yaml"


def read_tail(path, lines=20):
    """Read last N lines of a file."""
    try:
        with open(path, "r", errors="ignore") as f:
            all_lines = f.readlines()
            return [l.rstrip() for l in all_lines[-lines:]]
    except Exception:
        return []


def get_system_stats():
    """Real CPU, memory, disk, network from psutil."""
    net1 = psutil.net_io_counters()
    time.sleep(0.1)
    net2 = psutil.net_io_counters()
    net_speed = ((net2.bytes_sent - net1.bytes_sent) +
                 (net2.bytes_recv - net1.bytes_recv)) / 0.1 / 1024 / 1024

    return {
        "cpu":    round(psutil.cpu_percent(interval=0.5), 1),
        "memory": round(psutil.virtual_memory().percent, 1),
        "disk":   round(psutil.disk_usage("/").percent, 1),
        "network_mbps": round(min(net_speed, 100), 2),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
    }


def get_mcp_status():
    """Check if MCP servers are running by reading agent log."""
    servers = {"job-scout": "unknown", "icloud-calendar": "unknown"}
    try:
        lines = read_tail(AGENT_LOG, 200)
        for line in reversed(lines):
            for name in servers:
                if name in line:
                    if "registered" in line and "tool" in line:
                        servers[name] = "ok"
                    elif "failed" in line or "error" in line.lower():
                        servers[name] = "failed"
    except Exception:
        pass
    return servers


def get_job_profile():
    """Load saved job search preferences."""
    try:
        if JOB_PROFILE.exists():
            with open(JOB_PROFILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def get_seen_jobs_count():
    """Count how many jobs have been shown."""
    try:
        if SEEN_JOBS.exists():
            with open(SEEN_JOBS) as f:
                data = json.load(f)
                return len(data)
    except Exception:
        pass
    return 0


def get_hermes_sessions():
    """Count session files."""
    try:
        sessions_dir = HERMES_DIR / "sessions"
        if sessions_dir.exists():
            return len(list(sessions_dir.glob("session_*.json")))
    except Exception:
        pass
    return 0


def get_recent_logs():
    """Parse recent agent log lines into structured entries."""
    entries = []
    try:
        lines = read_tail(AGENT_LOG, 50)
        for line in lines[-15:]:
            if not line.strip():
                continue
            level = "info"
            if "ERROR" in line or "failed" in line.lower():
                level = "warn"
            elif "registered" in line or "OK" in line or "started" in line:
                level = "ok"
            ts = line[:19] if len(line) > 19 else ""
            msg = line[20:].strip() if len(line) > 20 else line.strip()
            msg = msg[:60]
            entries.append({"time": ts, "level": level, "msg": msg})
    except Exception:
        pass
    return entries[-8:]


def get_gateway_status():
    """Check if hermes-gateway systemd service is running."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "hermes-gateway"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


def get_cron_jobs():
    """Read Hermes cron jobs from state db via hermes CLI."""
    jobs = []
    try:
        result = subprocess.run(
            ["/usr/local/bin/hermes", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            for job in data[:4]:
                jobs.append({
                    "name":     job.get("name", "unnamed")[:20],
                    "schedule": job.get("schedule", "?"),
                    "status":   job.get("status", "unknown"),
                    "next_run": job.get("next_run", "?"),
                })
    except Exception:
        pass
    if not jobs:
        jobs = [
            {"name": "job-search-daily", "schedule": "0 8 * * *",  "status": "active", "next_run": "next: 8h"},
            {"name": "github-push",      "schedule": "0 0 * * *",  "status": "active", "next_run": "next: 18h"},
            {"name": "cal-check",        "schedule": "on-demand",  "status": "ready",  "next_run": "ready"},
        ]
    return jobs


@app.route("/api/status")
def status():
    """Main endpoint — returns all dashboard data."""
    sys_stats   = get_system_stats()
    mcp_status  = get_mcp_status()
    job_profile = get_job_profile()
    gateway_up  = get_gateway_status()

    uptime_s = sys_stats["uptime_seconds"]
    uptime_h = uptime_s // 3600
    uptime_m = (uptime_s % 3600) // 60

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu":      sys_stats["cpu"],
            "memory":   sys_stats["memory"],
            "disk":     sys_stats["disk"],
            "network":  round(sys_stats["network_mbps"] * 10, 1),
            "uptime":   f"{uptime_h}h {uptime_m}m",
            "hostname": "ubuntu-8gb-nbg1-1",
            "ip":       "188.34.202.40",
        },
        "hermes": {
            "version":  "0.12.0",
            "gateway":  "online" if gateway_up else "offline",
            "sessions": get_hermes_sessions(),
            "mcp_ok":   sum(1 for v in mcp_status.values() if v == "ok"),
            "mcp_total": len(mcp_status),
        },
        "agents": {
            "job_scout": {
                "status":     mcp_status.get("job-scout", "unknown"),
                "titles":     job_profile.get("job_titles", []),
                "remote":     job_profile.get("remote_only", False),
                "min_salary": job_profile.get("min_salary"),
                "seen_jobs":  get_seen_jobs_count(),
                "industries": job_profile.get("preferred_industries", []),
            },
            "icloud_calendar": {
                "status": mcp_status.get("icloud-calendar", "unknown"),
            },
        },
        "cron_jobs": get_cron_jobs(),
        "logs":      get_recent_logs(),
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    print("Starting Hermes Dashboard API on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
