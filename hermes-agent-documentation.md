# Hermes Agent — MCP Tools Setup Documentation

> **Author:** Victor  
> **Platform:** Hermes Agent v0.12.0 on Hetzner VPS (Ubuntu 24.04)  
> **Last Updated:** May 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Infrastructure](#2-infrastructure)
3. [Prerequisites](#3-prerequisites)
4. [iCloud Calendar MCP Tool](#4-icloud-calendar-mcp-tool)
5. [Job Scout MCP Tool](#5-job-scout-mcp-tool)
6. [Registering MCP Tools with Hermes](#6-registering-mcp-tools-with-hermes)
7. [Hermes Personalities](#7-hermes-personalities)
8. [Job Search Profile — Persistent Preferences](#8-job-search-profile--persistent-preferences)
9. [Usage Guide](#9-usage-guide)
10. [Troubleshooting](#10-troubleshooting)
11. [File Structure Reference](#11-file-structure-reference)
12. [API Keys Reference](#12-api-keys-reference)

---

## 1. Project Overview

This project extends a self-hosted **Hermes Agent** instance with two custom MCP (Model Context Protocol) tools:

| Tool | Purpose |
|---|---|
| `icloud-calendar` | Read, create, and update iCloud calendar events |
| `job-scout` | Search job boards, filter by preferences, and return a clean digest |

Both tools run as **stdio MCP servers** on the Hetzner VPS and are registered permanently in Hermes' `config.yaml`. They persist across restarts and sessions — no repeated setup needed.

The job scout tool additionally stores the user's job search preferences in a local JSON file on disk, so the user only needs to state their preferences once and Hermes remembers them forever.

---

## 2. Infrastructure

| Component | Details |
|---|---|
| **Server** | Hetzner VPS — Ubuntu 24.04 (8GB RAM) |
| **Hostname** | `ubuntu-8gb-nbg1-1` |
| **Hermes Version** | v0.12.0 (2026.4.30) |
| **Python (Hermes venv)** | `/root/hermes-venv/bin/python3` |
| **Hermes Config** | `~/.hermes/config.yaml` |
| **Hermes Logs** | `~/.hermes/logs/` |
| **MCP Scripts Location** | `/root/` |

---

## 3. Prerequisites

### System Packages

```bash
apt install python3-full python3-venv -y
```

### Python Dependencies (Hermes venv)

The MCP tools run inside the Hermes virtual environment at `/root/hermes-venv`. Install required packages there:

```bash
/root/hermes-venv/bin/python3 -m pip install requests
```

> **Note:** The `mcp` package is already bundled with Hermes agent and does not need to be installed separately.

### Verify Installation

```bash
/root/hermes-venv/bin/python3 -c "import mcp; print('mcp OK')"
/root/hermes-venv/bin/python3 -c "import requests; print('requests OK')"
```

---

## 4. iCloud Calendar MCP Tool

### Overview

The iCloud Calendar tool connects to Apple's CalDAV API and exposes three capabilities to Hermes:

- **List events** — fetch upcoming calendar events by date range and calendar name
- **Create events** — add new events to any iCloud calendar
- **Update events** — modify existing events by UID

### File Location

```
/root/icloud_calendar_mcp.py
```

### How It Works

The tool uses the `caldav` Python library to communicate with `https://caldav.icloud.com`. It reads credentials from environment variables injected by Hermes at startup.

### Key Functions

| Function | Description |
|---|---|
| `fetch_events(cal_filter, days)` | Returns events within N days, optionally filtered by calendar name |
| `create_event(cal_name, summary, start, end, description)` | Creates a new iCalendar event |
| `update_event(uid, ...)` | Updates an existing event by its UID |

### Configuration in `config.yaml`

```yaml
mcp_servers:
  icloud-calendar:
    command: /root/hermes-venv/bin/python3
    args:
    - /root/icloud_calendar_mcp.py
    timeout: 60
    connect_timeout: 60
    env:
      ICLOUD_EMAIL: your@icloud.com
      ICLOUD_PASSWORD: your-app-specific-password
```

> **Important:** Use an **App-Specific Password** from [appleid.apple.com](https://appleid.apple.com), not your regular iCloud password.

### MCP Tools Exposed

| Tool Name | Description |
|---|---|
| `mcp_icloud_calendar_list_events` | List upcoming events |
| `mcp_icloud_calendar_create_event` | Create a new event |
| `mcp_icloud_calendar_update_event` | Update an existing event by UID |

### Example Usage in Hermes

```
What's on my Family calendar this week?
Create a meeting called "Team Sync" on May 10 from 9am to 10am in my Work calendar
```

---

## 5. Job Scout MCP Tool

### Overview

The Job Scout tool searches multiple job boards, filters results against the user's saved preferences, deduplicates listings across sources, and returns a clean ranked digest. Preferences are saved permanently to disk so the user never has to repeat them.

### File Location

```
/root/job_scout_mcp.py
```

### Architecture

```
User asks Hermes → Hermes calls MCP tool → job_scout_mcp.py
                                                    ↓
                                         Load job_profile.json
                                                    ↓
                              ┌─────────────────────┴──────────────────────┐
                              ↓                                             ↓
                        Adzuna API                                   JSearch API
                        (250 req/mo free)                         (200 req/mo free)
                              ↓                                             ↓
                              └─────────────────────┬──────────────────────┘
                                                    ↓
                                         Filter → Rank → Deduplicate
                                                    ↓
                                         Save to seen_jobs.json
                                                    ↓
                                         Return clean digest to Hermes
```

### Persistent Storage Files

| File | Purpose |
|---|---|
| `~/hermes/tools/job_scout/job_profile.json` | Saved user preferences — loaded on every search |
| `~/hermes/tools/job_scout/seen_jobs.json` | Deduplication cache — prevents showing same job twice |

### Job Profile Schema

```json
{
  "job_titles": ["Senior Technical Program Manager", "Staff TPM"],
  "keywords": ["TPM", "technical program manager"],
  "locations": ["Remote", "San Francisco"],
  "remote_only": true,
  "min_salary": 160000,
  "max_salary": null,
  "experience_level": "senior",
  "exclude_companies": [],
  "preferred_industries": ["fintech", "infrastructure"],
  "country": "us",
  "results_per_search": 10,
  "max_days_old": 7
}
```

### Data Sources

| Source | API | Free Tier | Sign Up |
|---|---|---|---|
| Adzuna | REST API | 250 req/month | [developer.adzuna.com](https://developer.adzuna.com) |
| JSearch | RapidAPI | 200 req/month | [rapidapi.com](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) |

### MCP Tools Exposed

| Tool Name | Description |
|---|---|
| `mcp_job_scout_search_jobs` | Search jobs using saved profile |
| `mcp_job_scout_update_job_profile` | Save/update preferences permanently |
| `mcp_job_scout_show_job_profile` | Display current saved preferences |

### Configuration in `config.yaml`

```yaml
mcp_servers:
  job-scout:
    command: /root/hermes-venv/bin/python3
    args:
    - /root/job_scout_mcp.py
    timeout: 60
    connect_timeout: 60
    env:
      ADZUNA_APP_ID: your_adzuna_app_id
      ADZUNA_APP_KEY: your_adzuna_app_key
      RAPIDAPI_KEY: your_rapidapi_key
```

### Sample Output

```
🎯 Job Scout Digest — May 05, 2026

Found 5 matching role(s):

────────────────────────────────────────────────
1. Senior Technical Program Manager @ Stripe
   📍 Remote
   💰 $180,000 – $220,000
   📅 2026-05-03  |  🔗 https://stripe.com/jobs/...
   📝 We are looking for a Senior TPM to lead cross-functional...

────────────────────────────────────────────────
2. Staff TPM, Infrastructure @ Figma
   📍 Remote / San Francisco
   💰 $200,000+
   📅 2026-05-04  |  🔗 https://figma.com/careers/...
```

---

## 6. Registering MCP Tools with Hermes

### Edit `config.yaml`

```bash
nano ~/.hermes/config.yaml
```

Append the MCP server entries at the bottom of the file under the `mcp_servers:` key. Both tools follow the same pattern:

```yaml
mcp_servers:
  icloud-calendar:
    command: /root/hermes-venv/bin/python3
    args:
    - /root/icloud_calendar_mcp.py
    timeout: 60
    connect_timeout: 60
    env:
      ICLOUD_EMAIL: your@icloud.com
      ICLOUD_PASSWORD: your-app-specific-password
  job-scout:
    command: /root/hermes-venv/bin/python3
    args:
    - /root/job_scout_mcp.py
    timeout: 60
    connect_timeout: 60
    env:
      ADZUNA_APP_ID: your_adzuna_app_id
      ADZUNA_APP_KEY: your_adzuna_app_key
      RAPIDAPI_KEY: your_rapidapi_key
```

### Restart Hermes Gateway

After every `config.yaml` change:

```bash
systemctl --user restart hermes-gateway
```

### Verify Registration

```bash
hermes tools list
```

Expected output under **MCP servers**:

```
MCP servers:
  icloud-calendar  all tools enabled
  job-scout        all tools enabled
```

---

## 7. Hermes Personalities

Personalities allow Hermes to switch roles and behave differently depending on the task. They are defined in `config.yaml` and activated with `/personality <name>` inside the chat.

### Configuration

```yaml
personalities:
  job-scout:
    prompt: "You are a job search specialist. Always use the job-scout MCP tool when the user asks about jobs."
  calendar-assistant:
    prompt: "You are a calendar assistant. Always use icloud-calendar tools to manage schedules."
  tech-writer:
    prompt: "You are a professional technical writer. Write clear, structured documentation in Markdown."
  doc-reviewer:
    prompt: "You are a strict technical documentation reviewer. Check for clarity, accuracy, completeness, and consistency."
```

### Switching Personalities

Inside Hermes chat:

```
/personality job-scout
/personality calendar-assistant
/personality tech-writer
```

---

## 8. Job Search Profile — Persistent Preferences

The most important feature of the Job Scout tool is that preferences are saved **once** and remembered forever.

### Setting Preferences (One Time Only)

Start Hermes and say:

```
Remember that I'm looking for Senior Technical Program Manager or 
Staff TPM roles. Remote only, US-based. Minimum $160k salary. 
Prefer fintech or infrastructure companies.
```

Hermes calls `update_job_profile` and writes to `job_profile.json`. This survives restarts, new sessions, and server reboots.

### Verifying Saved Preferences

```
Show my job search profile
```

### Running a Search

```
Find me TPM jobs
Find me Localization Manager jobs
Any new program manager listings?
```

### Resetting Seen Jobs

To see previously shown listings again:

```
Show me all TPM jobs including ones you've shown before
```

Or delete the cache manually:

```bash
rm ~/hermes/tools/job_scout/seen_jobs.json
```

---

## 9. Usage Guide

### Calendar Commands

| What to say | What happens |
|---|---|
| `What's on my Family calendar this week?` | Lists events for the next 7 days |
| `What's on my calendar for June 2?` | Lists events for a specific date |
| `Create a meeting called Team Sync on May 10 from 9am to 10am in Work calendar` | Creates a new event |
| `Update the Coffee with Karin event to May 13` | Updates an existing event |

### Job Search Commands

| What to say | What happens |
|---|---|
| `Find me TPM jobs` | Searches using saved profile |
| `Find me Localization Manager jobs` | Searches for a specific role |
| `Remember I only want remote jobs above $140k` | Updates saved preferences |
| `Show my job search profile` | Displays current preferences |
| `Find jobs and include ones I've seen before` | Ignores dedup cache |

---

## 10. Troubleshooting

### MCP Tool Shows as "Failed"

Check the MCP error log:

```bash
tail -30 ~/.hermes/logs/mcp-stderr.log
```

**Common errors and fixes:**

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'requests'` | `/root/hermes-venv/bin/python3 -m pip install requests` |
| `ModuleNotFoundError: No module named 'mcp'` | `/root/hermes-venv/bin/python3 -m pip install mcp` |
| `AuthorizationError` (iCloud) | Regenerate App-Specific Password at appleid.apple.com |
| No jobs returned | Check API keys are correctly set in `config.yaml` |

### After Any Fix

Always restart the gateway:

```bash
systemctl --user restart hermes-gateway
```

### Verify Gateway Status

```bash
systemctl --user status hermes-gateway
```

### Check Agent Logs

```bash
tail -50 ~/.hermes/logs/agent.log
```

---

## 11. File Structure Reference

```
/root/
├── icloud_calendar_mcp.py        # iCloud Calendar MCP server
├── job_scout_mcp.py              # Job Scout MCP server
├── hermes-venv/                  # Python venv used by MCP tools
│   └── bin/python3               # Python interpreter
└── hermes/
    └── tools/
        └── job_scout/
            ├── job_profile.json  # Persistent job preferences
            └── seen_jobs.json    # Deduplication cache

~/.hermes/
├── config.yaml                   # Main Hermes configuration
├── logs/
│   ├── agent.log                 # Agent activity log
│   ├── mcp-stderr.log            # MCP server error log
│   └── errors.log                # General error log
└── skills/                       # Hermes skills library
```

---

## 12. API Keys Reference

| Key | Where to Get | Environment Variable |
|---|---|---|
| Adzuna App ID | [developer.adzuna.com](https://developer.adzuna.com) | `ADZUNA_APP_ID` |
| Adzuna App Key | [developer.adzuna.com](https://developer.adzuna.com) | `ADZUNA_APP_KEY` |
| RapidAPI Key (JSearch) | [rapidapi.com](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | `RAPIDAPI_KEY` |
| iCloud App Password | [appleid.apple.com](https://appleid.apple.com) → Security → App-Specific Passwords | `ICLOUD_PASSWORD` |

All keys are stored securely in `~/.hermes/config.yaml` under each MCP server's `env:` block and are never exposed to the user or logged.

---

*Documentation generated with Hermes Agent — tech-writer + doc-reviewer personalities.*
