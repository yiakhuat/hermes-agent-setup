# Hermes Agent — Complete Setup Documentation

> **Author:** Victor  
> **Platform:** Hermes Agent v0.14.0 on Hetzner VPS (Ubuntu 24.04)  
> **Last Updated:** May 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Infrastructure](#2-infrastructure)
3. [Prerequisites](#3-prerequisites)
4. [iCloud Calendar MCP Tool](#4-icloud-calendar-mcp-tool)
5. [Job Scout MCP Tool](#5-job-scout-mcp-tool)
6. [Registering MCP Tools with Hermes](#6-registering-mcp-tools-with-hermes)
7. [Personalities & Agent Manager](#7-personalities--agent-manager)
8. [Communication Channels](#8-communication-channels)
9. [Live Dashboard](#9-live-dashboard)
10. [Telephony Agent](#10-telephony-agent)
11. [Scheduled Cron Jobs](#11-scheduled-cron-jobs)
12. [Usage Guide](#12-usage-guide)
13. [Troubleshooting](#13-troubleshooting)
14. [File Structure Reference](#14-file-structure-reference)
15. [API Keys Reference](#15-api-keys-reference)

---

## 1. Project Overview

This project deploys a fully automated, self-hosted **Hermes Agent** on a Hetzner VPS with the following capabilities:

| Capability | Description |
|---|---|
| **Job Scout** | Searches job boards daily, filters by preferences, delivers results |
| **iCloud Calendar** | Read, create, and update Apple Calendar events |
| **Telegram** | Chat and voice messaging with Hermes |
| **WhatsApp** | Chat with Hermes via self-chat bridge |
| **Phone Calls** | Call a Twilio number and speak to Hermes |
| **Live Dashboard** | Real-time Pac-Man ghost agent office |
| **Daily Reports** | Automated tech news and financial market summaries |

All components run 24/7 as systemd services, survive reboots, and are monitored via the live dashboard.

---

## 2. Infrastructure

| Component | Details |
|---|---|
| **Server** | Hetzner VPS — Ubuntu 24.04 (8GB RAM) |
| **Hostname** | `ubuntu-8gb-nbg1-1` |
| **IP Address** | `188.34.202.40` |
| **Hermes Version** | v0.14.0 |
| **Python venv** | `/root/hermes-venv/bin/python3` |
| **Hermes Config** | `~/.hermes/config.yaml` |
| **Environment Variables** | `~/.hermes/.env` |
| **Logs** | `~/.hermes/logs/` |

---

## 3. Prerequisites

### System Packages

```bash
apt install python3-full python3-venv ffmpeg -y
```

### Python Dependencies

```bash
/root/hermes-venv/bin/python3 -m pip install requests caldav flask flask-cors psutil pyyaml twilio edge-tts
```

### Verify Installation

```bash
/root/hermes-venv/bin/python3 -c "import mcp; print('mcp OK')"
/root/hermes-venv/bin/python3 -c "import requests; print('requests OK')"
/root/hermes-venv/bin/python3 -c "import edge_tts; print('edge_tts OK')"
/root/hermes-venv/bin/python3 -c "import twilio; print('twilio OK')"
```

---

## 4. iCloud Calendar MCP Tool

### Overview

Connects to Apple's CalDAV API to manage iCloud calendar events directly from Hermes.

### File Location

```
/root/icloud_calendar_mcp.py
```

### Capabilities

- **List events** — fetch upcoming events by date range and calendar name
- **Create events** — add new events to any iCloud calendar
- **Update events** — modify existing events by UID

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

> **Important:** Use an **App-Specific Password** from [appleid.apple.com](https://appleid.apple.com) → Security → App-Specific Passwords. Do not use your regular Apple ID password.

### MCP Tools Exposed

| Tool Name | Description |
|---|---|
| `mcp_icloud_calendar_list_events` | List upcoming calendar events |
| `mcp_icloud_calendar_create_event` | Create a new calendar event |
| `mcp_icloud_calendar_update_event` | Update an existing event by UID |

### Example Usage

```
What's on my Family calendar this week?
What's on my calendar for June 2?
Create a meeting called "Team Sync" on May 10 from 9am to 10am in my Work calendar
Update the Coffee with Karin event to May 13
```

---

## 5. Job Scout MCP Tool

### Overview

Searches multiple job boards, filters results against saved preferences, deduplicates listings, and delivers a clean ranked digest. Preferences are saved permanently — set once, remembered forever.

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
                    Adzuna API                                  JSearch API
                    (250 req/mo free)                        (200 req/mo free)
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

### Current Job Profile

```json
{
  "job_titles": ["Technical Project Manager", "Localization Manager"],
  "locations": ["remote", "hybrid"],
  "remote_only": false,
  "min_salary": 140000,
  "experience": "senior",
  "industries": ["software", "consulting"],
  "max_days_old": 7
}
```

### Data Sources

| Source | API | Free Tier | Sign Up |
|---|---|---|---|
| Adzuna | REST API | 250 req/month | [developer.adzuna.com](https://developer.adzuna.com) |
| JSearch | RapidAPI | 200 req/month | [rapidapi.com](https://rapidapi.com) |

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

---

## 6. Registering MCP Tools with Hermes

### Edit `config.yaml`

```bash
nano ~/.hermes/config.yaml
```

Add both MCP servers under the `mcp_servers:` key. Restart after every change:

```bash
systemctl --user restart hermes-gateway
```

### Verify Registration

```bash
grep -i "registered" ~/.hermes/logs/agent.log | tail -5
```

Expected output:
```
MCP server 'job-scout' (stdio): registered 3 tool(s)
MCP server 'icloud-calendar' (stdio): registered 3 tool(s)
```

---

## 7. Personalities & Agent Manager

Personalities allow Hermes to switch roles and specializations. They are defined in `config.yaml` under the `personalities:` key.

### Active Personalities

| Name | Role |
|---|---|
| `job-scout` | Job search specialist — uses Job Scout MCP tool |
| `calendar-assistant` | Calendar manager — uses iCloud Calendar MCP tool |
| `researcher` | Web research and information gathering |
| `Coder` | Software development and coding tasks |
| `tech-writer` | Professional technical documentation |
| `Doc-reviewer` | Documentation review and quality check |
| `technical` | Detailed technical expert |
| `creative` | Creative and innovative thinking |
| `teacher` | Patient teaching with clear examples |
| `manager` | Agent orchestrator — delegates tasks to specialists |

### Manager Agent

The manager personality coordinates all other agents for complex multi-step tasks:

```
As manager, plan my week — find new TPM jobs, check my calendar, and research AI news
```

Hermes will automatically delegate to the right specialist and combine results.

### Switching Personalities

From terminal:
```bash
hermes chat -q "/personality job-scout"
```

From Telegram or WhatsApp (natural language):
```
Switch to researcher mode
Find me jobs (automatically uses job-scout)
```

---

## 8. Communication Channels

### Telegram

Hermes is connected to a Telegram bot and listens for messages 24/7.

**Configuration in `.env`:**
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USERS=your_telegram_user_id
TELEGRAM_HOME_CHANNEL=your_telegram_user_id
```

**Features:**
- Text messaging
- Voice message input (transcribed via local Whisper)
- Voice output (Edge TTS / OpenAI TTS)
- Home channel for cron job delivery

**Voice mode:**
```
/voice on      — always reply with voice
/voice off     — text only
```

### WhatsApp

Connected via Baileys bridge in self-chat mode (message yourself).

**Setup:**
```bash
hermes whatsapp   # Choose option 2 (personal number)
                  # Scan QR code with your phone
```

**Configuration in `.env`:**
```
WHATSAPP_ENABLED=true
WHATSAPP_ALLOWED_USERS=1XXXXXXXXXX
```

**Features:**
- Text messaging
- Voice message input (transcribed via local Whisper)
- Text responses

**Note:** Both Telegram and WhatsApp run simultaneously on the same Hermes gateway.

---

## 9. Live Dashboard

### Overview

A real-time Pac-Man ghost style dashboard showing the status of all Hermes agents, system resources, and activity logs.

### Access

- **URL:** `http://188.34.202.40:5000/`
- **API:** `http://188.34.202.40:5000/api/status`

### Features

- MCP Tool Agents with live ACTIVE/FAILED status
- All personality agents as colored ghost cards
- Real CPU, memory, disk, and network usage
- Live activity log from Hermes
- Scheduled cron jobs
- VPS uptime and session count
- Auto-refreshes every 30 seconds

### Files

| File | Purpose |
|---|---|
| `hermes_dashboard_api.py` | Flask backend API (port 5000) |
| `hermes-agent-office-live.html` | Frontend dashboard |
| `hermes-dashboard.service` | Systemd service |

### Service Management

```bash
systemctl --user status hermes-dashboard
systemctl --user restart hermes-dashboard
```

---

## 10. Telephony Agent

### Overview

The telephony agent enables callers to speak directly to Hermes AI over a regular phone call. Built with Twilio and Flask.

### Architecture

```
Incoming Call
      ↓
Twilio (toll-free number)
      ↓
Hetzner VPS (port 5001)
      ↓
hermes_telephony.py (Flask webhook)
      ↓
Hermes CLI (hermes chat -q)
      ↓
DeepSeek AI model
      ↓
Twilio TTS (Polly.Joanna / Polly.Zhiyu)
      ↓
Caller hears response
```

### File Location

```
/root/hermes_telephony.py
```

### Features

- English and Chinese (Mandarin) language support
- Automatic language detection from speech
- Multi-turn conversation within a single call
- Powered by Hermes with all MCP tools available
- Runs 24/7 as a systemd service
- No ngrok needed — uses direct VPS IP

### Installation

```bash
# Install dependencies
/root/hermes-venv/bin/python3 -m pip install twilio flask

# Copy service file
cp hermes-telephony.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable hermes-telephony
systemctl --user start hermes-telephony
```

### Twilio Configuration

1. Create a Twilio account at [twilio.com](https://twilio.com)
2. Get a toll-free US phone number
3. In the Twilio Console → Phone Numbers → Configure:
   - **Webhook URL:** `http://188.34.202.40:5001/voice/incoming`
   - **HTTP Method:** `POST`
4. Add credentials to `~/.hermes/.env`:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
```

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/voice/incoming` | POST | Handles incoming calls, greets caller |
| `/voice/process` | POST | Processes speech, queries Hermes, responds |
| `/voice/status` | POST | Call status callbacks from Twilio |
| `/health` | GET | Service health check |

### Service Management

```bash
systemctl --user status hermes-telephony
systemctl --user restart hermes-telephony
```

### Testing

```bash
# Check health endpoint
curl http://188.34.202.40:5001/health

# Check service logs
journalctl --user -u hermes-telephony -n 20
```

Then call your Twilio toll-free number from any phone. Speak your question in English or Chinese.

---

## 11. Scheduled Cron Jobs

| ID | Name | Schedule (UTC) | Status |
|---|---|---|---|
| `0d35772459f4` | Daily Tech News Report | 3:00 PM daily | ✅ Active |
| `05e4f24d5ded` | Daily Financial Market News | 4:00 PM daily | ✅ Active |
| `5a56bc82a038` | GitHub Auto-Push | Midnight daily | ✅ Active |
| `2c321efa08b2` | Daily Localization Job Openings | 5:00 PM daily | ✅ Active |
| `6e9aa7ae6532` | Daily TPM Job Openings | 5:30 PM daily | ✅ Active |

All cron results are delivered to the Telegram home channel.

### Managing Cron Jobs

```bash
hermes cron list              # List all jobs with status
hermes cron run <job_id>      # Trigger a job immediately
hermes cron pause <job_id>    # Pause a job
hermes cron resume <job_id>   # Resume a paused job
```

---

## 12. Usage Guide

### Terminal (Recommended for Quick Tasks)

```bash
# One-time alias setup
echo 'alias h="hermes chat -q"' >> ~/.bashrc
source ~/.bashrc

# Examples
h "find me TPM jobs"
h "what's on my calendar this week?"
h "research latest AI agent frameworks in 2026"
h "switch to manager and plan my week"
h "show my job search profile"
```

### Calendar Commands

| What to say | What happens |
|---|---|
| `What's on my calendar this week?` | Lists events for the next 7 days |
| `What's on my calendar for June 2?` | Lists events for a specific date |
| `Create a meeting called Team Sync on May 10 from 9am to 10am` | Creates a new event |
| `Update the Coffee with Karin event to May 13` | Updates an existing event |

### Job Search Commands

| What to say | What happens |
|---|---|
| `Find me TPM jobs` | Searches using saved profile |
| `Find me Localization Manager jobs` | Searches for a specific role |
| `Remember I only want remote jobs above $150k` | Updates saved preferences |
| `Show my job search profile` | Displays current preferences |
| `Find jobs including ones I've seen before` | Bypasses dedup cache |

### Telephony Commands

Call your Twilio number and speak naturally in English or Chinese:
- *"What jobs are available for me?"*
- *"What's on my calendar today?"*
- *"Tell me the latest tech news"*
- *"你好，帮我查一下我的日历"*

---

## 13. Troubleshooting

### Hermes Gateway Not Responding

```bash
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway
tail -20 ~/.hermes/logs/agent.log
```

### MCP Tool Shows Unknown/Failed Status

```bash
grep -i "job-scout\|icloud-calendar" ~/.hermes/logs/agent.log | tail -5
```

### Dashboard Not Loading

```bash
systemctl --user restart hermes-dashboard
curl http://localhost:5000/api/health
```

### Telephony Agent Not Responding to Calls

```bash
systemctl --user restart hermes-telephony
curl http://localhost:5001/health
```

### YAML Config Errors

```bash
/root/hermes-venv/bin/python3 -c "
import yaml
try:
    yaml.safe_load(open('/root/.hermes/config.yaml'))
    print('OK - no errors')
except yaml.YAMLError as e:
    print('ERROR:', e)
"
```

### Common Errors and Fixes

| Error | Fix |
|---|---|
| `NoneType object is not iterable` | Run `hermes model` and switch to DeepSeek provider |
| `Failed to parse config.yaml` | Check for tab characters or duplicate keys in YAML |
| `MCP server registered 0 tools` | Verify API keys in `config.yaml` env section |
| `File not found: tts_*.mp3` | Clear audio cache: `rm -f ~/.hermes/audio_cache/tts_*` |
| `Session DB: file is not a database` | Remove state files: `rm -f ~/.hermes/state.db*` |
| WhatsApp not responding | Clear sessions and restart: `rm -rf ~/.hermes/sessions/* && systemctl --user restart hermes-gateway` |

---

## 14. File Structure Reference

```
/root/
├── icloud_calendar_mcp.py         # iCloud Calendar MCP server
├── job_scout_mcp.py               # Job Scout MCP server
├── hermes_dashboard_api.py        # Dashboard Flask API (port 5000)
├── hermes_telephony.py            # Telephony agent Flask server (port 5001)
├── hermes-agent-office-live.html  # Live dashboard frontend
├── hermes-venv/                   # Python virtual environment
│   └── bin/python3
└── hermes/
    └── tools/
        └── job_scout/
            ├── job_profile.json   # Persistent job preferences
            └── seen_jobs.json     # Deduplication cache

~/.hermes/
├── config.yaml                    # Main Hermes configuration
├── .env                           # API keys and environment variables
├── logs/
│   ├── agent.log                  # Agent activity log
│   └── mcp-stderr.log             # MCP server error log
├── audio_cache/                   # TTS audio files (auto-cleaned)
├── sessions/                      # Conversation history
└── whatsapp/
    └── session/                   # WhatsApp Baileys bridge session

~/.config/systemd/user/
├── hermes-gateway.service         # Main Hermes agent
├── hermes-dashboard.service       # Dashboard API
└── hermes-telephony.service       # Telephony agent
```

---

## 15. API Keys Reference

| Service | Key(s) | Where to Get | Config Location |
|---|---|---|---|
| Adzuna | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | [developer.adzuna.com](https://developer.adzuna.com) | `config.yaml` → `mcp_servers.job-scout.env` |
| JSearch | `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) | `config.yaml` → `mcp_servers.job-scout.env` |
| iCloud | `ICLOUD_EMAIL` + `ICLOUD_PASSWORD` | [appleid.apple.com](https://appleid.apple.com) → App-Specific Passwords | `config.yaml` → `mcp_servers.icloud-calendar.env` |
| DeepSeek | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) | `~/.hermes/.env` |
| Telegram | `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram | `~/.hermes/.env` |
| OpenAI TTS | `VOICE_TOOLS_OPENAI_KEY` | [platform.openai.com](https://platform.openai.com) | `~/.hermes/.env` |
| Twilio | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | [console.twilio.com](https://console.twilio.com) | `~/.hermes/.env` |
| Finnhub | `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) | `~/.hermes/.env` |
| NewsData | `NEWSDATA_API_KEY` | [newsdata.io](https://newsdata.io) | `~/.hermes/.env` |
| Twelve Data | `TWELVE_DATA_API_KEY` | [twelvedata.com](https://twelvedata.com) | `~/.hermes/.env` |

---

*Documentation maintained by Victor · Hermes Agent v0.14.0 · May 2026*
